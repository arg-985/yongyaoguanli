"""家庭药箱、症状咨询与用药安全的核心规则实现。"""
import json
import urllib.request
from itertools import combinations

from django.conf import settings

from apps.medications.models import Medication
from apps.plans.models import MedicationPlan

from .catalog import SYMPTOM_CATALOG
from .models import HomeCabinetItem

FREQUENCY_PER_DAY = {
    'DAILY': 1,
    'ONCE_DAILY': 1,
    'BID': 2,
    'TID': 3,
    'QID': 4,
    'ONCE_WEEKLY': 0,
}

MAX_DAILY_TIMES = 4

_EXPIRY_RANK = {'normal': 0, 'soon': 1, 'unknown': 2, 'expired': 3}


def _symptom_name(code):
    item = SYMPTOM_CATALOG.get(code)
    return item['name'] if item else code


def _symptom_names(codes):
    return [_symptom_name(code) for code in (codes or [])]


def _ingredient_list(raw):
    if not raw:
        return []
    return [part.strip() for part in str(raw).split(',') if part.strip()]


def _cabinet_index(patient):
    """药箱中每个药品取「有效期状态最好」的一条，便于判断库存。"""
    index = {}
    items = HomeCabinetItem.objects.filter(owner=patient).select_related('medication')
    for item in items:
        if item.medication_id is None:
            continue
        current = index.get(item.medication_id)
        if current is None or _EXPIRY_RANK.get(item.expiry_status, 2) < _EXPIRY_RANK.get(
            current.expiry_status, 2
        ):
            index[item.medication_id] = item
    return index


def recommend(patient, symptoms, severity=2, duration_days=1):
    """按症状命中数、是否非处方药、药箱库存排序推荐非处方药。"""
    symptom_codes = [code for code in (symptoms or []) if code]
    if not patient or not symptom_codes:
        return []

    cabinet = _cabinet_index(patient)
    scored = []
    for med in Medication.objects.all():
        tags = med.symptom_tags
        if not isinstance(tags, list):
            continue
        hits = [tag for tag in tags if tag in symptom_codes]
        if not hits:
            continue

        cabinet_item = cabinet.get(med.id)
        stock_available = bool(
            cabinet_item
            and cabinet_item.quantity
            and cabinet_item.quantity > 0
            and cabinet_item.expiry_status != 'expired'
        )
        expiry_status = cabinet_item.expiry_status if cabinet_item else 'unknown'

        reason_bits = ['适用症状：' + '、'.join(_symptom_names(hits))]
        if med.is_otc:
            reason_bits.append('非处方药')
        else:
            reason_bits.append('处方药，需医生开具')
        if cabinet_item:
            reason_bits.append(
                '家庭药箱有库存' if stock_available else '家庭药箱中的同款药品已过期或无库存'
            )
        if severity >= 4:
            reason_bits.append('症状偏重，建议尽快就医')
        if duration_days and duration_days >= 7:
            reason_bits.append('症状已持续一周以上')

        scored.append((
            (-len(hits), 0 if med.is_otc else 1, 0 if stock_available else 1, med.id),
            {
                'medication_id': med.id,
                'name': med.name,
                'specification': med.specification or '',
                'dosage': med.max_daily_dose or '',
                'reason': '；'.join(reason_bits),
                'stock_available': stock_available,
                'expiry_status': expiry_status,
            },
        ))

    scored.sort(key=lambda pair: pair[0])
    return [data for _, data in scored[:10]]


def collect_warnings(symptoms):
    """汇总所选症状的危险信号。"""
    warnings = []
    for code in symptoms or []:
        item = SYMPTOM_CATALOG.get(code)
        if not item:
            continue
        for flag in item['red_flags']:
            text = f'{item["name"]}：{flag}'
            if text not in warnings:
                warnings.append(text)
    return warnings


def build_advice(symptoms, severity, duration_days, recommendations, warnings=None):
    """拼装规则版中文建议文本。"""
    names = _symptom_names(symptoms)
    overview = (
        f'本次咨询的主要症状为{("、".join(names) if names else "未填写")}，'
        f'严重程度 {severity}/5，已持续 {duration_days} 天。'
    )

    if recommendations:
        lines = []
        for idx, rec in enumerate(recommendations, start=1):
            spec = f'（规格 {rec["specification"]}）' if rec.get('specification') else ''
            dose = rec.get('dosage') or '按说明书推荐剂量'
            lines.append(f'{idx}. {rec["name"]}{spec}：{dose}。{rec["reason"]}。')
        med_text = '可参考以下非处方药，用药前请核对过敏史并阅读说明书：\n' + '\n'.join(lines)
    else:
        med_text = '暂未匹配到合适的非处方药，建议先咨询药师或医生后再用药。'

    caveats = (
        '严格按说明书剂量服用，不要同时服用含相同成分的复方感冒药，以免重复用药；'
        '服药期间避免饮酒；症状缓解后即可停药，无需长期服用；'
        '孕妇、哺乳期妇女、儿童、老年人及肝肾功能异常者用药前请咨询医生。'
    )

    warning_list = warnings if warnings else [
        '症状持续加重或超过一周无缓解',
        '出现高热不退、呼吸困难、意识改变',
    ]
    doctor_text = '出现以下情况请立即就医：' + '；'.join(warning_list) + '。'

    return '\n\n'.join([
        '【症状概述】' + overview,
        '【用药建议】' + med_text,
        '【注意事项】' + caveats,
        '【何时就医】' + doctor_text,
    ])


def _plan_times_per_day(plan):
    if plan.custom_times and isinstance(plan.custom_times, list):
        return len(plan.custom_times)
    return FREQUENCY_PER_DAY.get(plan.frequency, 1)


def check_interactions(patient_id):
    """检测同一患者有效用药计划中的用药风险。"""
    if not patient_id:
        return []

    plans = MedicationPlan.objects.filter(
        patient_id=patient_id, is_active=True
    ).select_related('medication')
    if not plans:
        return []

    meds = {}
    times_by_med = {}
    for plan in plans:
        med = plan.medication
        meds[med.id] = med
        times_by_med[med.id] = times_by_med.get(med.id, 0) + _plan_times_per_day(plan)

    findings = []

    # ① 同成分重复
    for id_a, id_b in combinations(sorted(meds), 2):
        med_a, med_b = meds[id_a], meds[id_b]
        common = set(_ingredient_list(med_a.ingredients)) & set(
            _ingredient_list(med_b.ingredients)
        )
        if not common:
            continue
        findings.append({
            'level': 'high',
            'title': '重复用药风险',
            'detail': (
                f'「{med_a.name}」与「{med_b.name}」含有相同成分：'
                f'{"、".join(sorted(common))}，同时服用可能造成该成分过量，'
                '请及时与医生或药师确认后再服用。'
            ),
            'medications': [
                {'id': med_a.id, 'name': med_a.name},
                {'id': med_b.id, 'name': med_b.name},
            ],
        })

    # ② 每日服用次数过多
    for med_id, times in times_by_med.items():
        if times <= MAX_DAILY_TIMES:
            continue
        med = meds[med_id]
        detail = (
            f'「{med.name}」当前有效计划合计每日 {times} 次，'
            f'超过建议的每日 {MAX_DAILY_TIMES} 次，请核对用药计划。'
        )
        if med.min_interval_hours:
            detail += f'该药最小用药间隔为 {med.min_interval_hours} 小时。'
        findings.append({
            'level': 'medium',
            'title': '每日服用次数过多',
            'detail': detail,
            'medications': [{'id': med.id, 'name': med.name}],
        })

    # ③ 特殊人群警示
    cautions = [
        (med, med.population_caution.strip())
        for med in meds.values()
        if (med.population_caution or '').strip()
    ]
    if cautions:
        findings.append({
            'level': 'info',
            'title': '特殊人群用药警示',
            'detail': '；'.join(f'「{med.name}」：{text}' for med, text in cautions),
            'medications': [
                {'id': med.id, 'name': med.name} for med, _ in cautions
            ],
        })

    return findings


def llm_enabled():
    return bool((getattr(settings, 'LLM_API_KEY', '') or '').strip())


def llm_model_name():
    return getattr(settings, 'LLM_MODEL', '') or 'gpt-4o-mini'


def ask_llm(messages):
    """调用 OpenAI 兼容的 chat/completions 接口，未配置或异常时返回 None。"""
    if not llm_enabled():
        return None

    url = getattr(settings, 'LLM_BASE_URL', '') or 'https://api.openai.com/v1/chat/completions'
    payload = json.dumps({
        'model': llm_model_name(),
        'messages': messages,
        'temperature': 0.3,
    }).encode('utf-8')
    request = urllib.request.Request(
        url,
        data=payload,
        method='POST',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.LLM_API_KEY}',
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
        content = (data['choices'][0]['message']['content'] or '').strip()
        return content or None
    except Exception:
        return None
