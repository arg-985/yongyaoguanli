"""家庭药箱 / 症状咨询模块的种子数据（幂等）。"""
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.clinic.models import HomeCabinetItem
from apps.medications.models import Medication

User = get_user_model()

MEDICATIONS = [
    {
        'name': '对乙酰氨基酚片',
        'specification': '0.5g*20片',
        'unit': '盒',
        'category': '解热镇痛药',
        'ingredients': '对乙酰氨基酚',
        'is_otc': True,
        'symptom_tags': ['fever', 'headache', 'pain'],
        'max_daily_dose': '每日不超过 4 片（2g）',
        'min_interval_hours': 6,
        'population_caution': '严重肝肾功能不全者禁用；服药期间禁止饮酒；孕妇及哺乳期慎用。',
        'description': '用于普通感冒或流行性感冒引起的发热，也用于缓解轻至中度疼痛。',
    },
    {
        'name': '布洛芬缓释胶囊',
        'specification': '0.3g*20粒',
        'unit': '盒',
        'category': '解热镇痛药',
        'ingredients': '布洛芬',
        'is_otc': True,
        'symptom_tags': ['fever', 'headache', 'pain', 'stomach'],
        'max_daily_dose': '每日不超过 2 粒',
        'min_interval_hours': 12,
        'population_caution': '活动性消化道溃疡、严重心衰患者禁用；餐后服用以减少胃部刺激。',
        'description': '用于缓解轻至中度疼痛及发热。',
    },
    {
        'name': '复方氨酚烷胺片',
        'specification': '12片',
        'unit': '盒',
        'category': '复方感冒药',
        'ingredients': '对乙酰氨基酚,盐酸金刚烷胺,马来酸氯苯那敏,人工牛黄,咖啡因',
        'is_otc': True,
        'symptom_tags': ['cold', 'fever', 'nasal', 'headache'],
        'max_daily_dose': '每日不超过 2 片',
        'min_interval_hours': 12,
        'population_caution': '含对乙酰氨基酚，勿与其他感冒药同服；服药后易嗜睡，避免驾驶；孕妇及 1 岁以下儿童禁用。',
        'description': '用于缓解普通感冒及流行性感冒引起的发热、头痛、鼻塞、流涕等症状。',
    },
    {
        'name': '感冒灵颗粒',
        'specification': '10g*9袋',
        'unit': '盒',
        'category': '复方感冒药',
        'ingredients': '对乙酰氨基酚,马来酸氯苯那敏,咖啡因,三叉苦,金盏银盘',
        'is_otc': True,
        'symptom_tags': ['cold', 'fever', 'headache', 'nasal'],
        'max_daily_dose': '每日不超过 3 袋',
        'min_interval_hours': 6,
        'population_caution': '含对乙酰氨基酚与马来酸氯苯那敏，服药后可能嗜睡；肝肾功能不全者慎用。',
        'description': '用于感冒引起的头痛、发热、鼻塞、流涕、咽痛。',
    },
    {
        'name': '氨溴索口服液',
        'specification': '100ml',
        'unit': '瓶',
        'category': '祛痰药',
        'ingredients': '盐酸氨溴索',
        'is_otc': True,
        'symptom_tags': ['cough'],
        'max_daily_dose': '每日不超过 3 次，每次 10ml',
        'min_interval_hours': 6,
        'population_caution': '妊娠早期慎用；胃溃疡患者慎用。',
        'description': '用于痰液黏稠、咳痰困难的急慢性呼吸道疾病。',
    },
    {
        'name': '右美沙芬糖浆',
        'specification': '120ml',
        'unit': '瓶',
        'category': '镇咳药',
        'ingredients': '氢溴酸右美沙芬',
        'is_otc': True,
        'symptom_tags': ['cough'],
        'max_daily_dose': '每日不超过 3 次，每次 10ml',
        'min_interval_hours': 6,
        'population_caution': '痰多者不宜使用；妊娠 3 个月内及哺乳期妇女禁用；勿与单胺氧化酶抑制剂合用。',
        'description': '用于干咳，包括上呼吸道感染引起的咳嗽。',
    },
    {
        'name': '阿莫西林胶囊',
        'specification': '0.25g*24粒',
        'unit': '盒',
        'category': '抗生素',
        'ingredients': '阿莫西林',
        'is_otc': False,
        'symptom_tags': [],
        'max_daily_dose': '每日不超过 4 次，需遵医嘱',
        'min_interval_hours': 6,
        'population_caution': '青霉素过敏者禁用；必须足疗程使用，不可自行停药；需医生处方。',
        'description': '处方抗生素，用于敏感菌引起的感染，禁止自行购买使用。',
    },
    {
        'name': '蒙脱石散',
        'specification': '3g*10袋',
        'unit': '盒',
        'category': '止泻药',
        'ingredients': '蒙脱石',
        'is_otc': True,
        'symptom_tags': ['diarrhea'],
        'max_daily_dose': '每日不超过 3 袋',
        'min_interval_hours': 6,
        'population_caution': '与其他药物需间隔 1-2 小时服用；便秘患者慎用。',
        'description': '用于成人及儿童急、慢性腹泻。',
    },
    {
        'name': '口服补液盐',
        'specification': '5.125g*6袋',
        'unit': '盒',
        'category': '补液制剂',
        'ingredients': '氯化钠,氯化钾,枸橼酸钠,无水葡萄糖',
        'is_otc': True,
        'symptom_tags': ['diarrhea'],
        'max_daily_dose': '按口渴程度随时补充，每日不超过 6 袋',
        'min_interval_hours': 2,
        'population_caution': '少尿或无尿、严重腹泻脱水者应及时就医；心肾功能不全者慎用。',
        'description': '用于腹泻、呕吐等原因引起的轻中度脱水。',
    },
    {
        'name': '氯雷他定片',
        'specification': '10mg*6片',
        'unit': '盒',
        'category': '抗组胺药',
        'ingredients': '氯雷他定',
        'is_otc': True,
        'symptom_tags': ['allergy', 'nasal'],
        'max_daily_dose': '每日 1 片',
        'min_interval_hours': 24,
        'population_caution': '肝功能不全者需减量；妊娠期及哺乳期慎用；少数人服药后嗜睡。',
        'description': '用于缓解过敏性鼻炎及慢性荨麻疹的症状。',
    },
    {
        'name': '西替利嗪片',
        'specification': '10mg*12片',
        'unit': '盒',
        'category': '抗组胺药',
        'ingredients': '盐酸西替利嗪',
        'is_otc': True,
        'symptom_tags': ['allergy'],
        'max_daily_dose': '每日 1 片',
        'min_interval_hours': 24,
        'population_caution': '肾功能不全者需减量；服药期间避免饮酒及驾驶。',
        'description': '用于季节性或常年性过敏性鼻炎、荨麻疹。',
    },
    {
        'name': '铝碳酸镁咀嚼片',
        'specification': '0.5g*20片',
        'unit': '盒',
        'category': '抗酸药',
        'ingredients': '铝碳酸镁',
        'is_otc': True,
        'symptom_tags': ['stomach'],
        'max_daily_dose': '每日不超过 4 次，每次 2 片',
        'min_interval_hours': 4,
        'population_caution': '严重肾功能不全者禁用；长期服用需监测血铝浓度。',
        'description': '用于胃酸过多引起的胃痛、烧心、反酸。',
    },
    {
        'name': '艾司唑仑片',
        'specification': '1mg*20片',
        'unit': '盒',
        'category': '镇静催眠药',
        'ingredients': '艾司唑仑',
        'is_otc': False,
        'symptom_tags': [],
        'max_daily_dose': '需遵医嘱，每日不超过 1 片',
        'min_interval_hours': 24,
        'population_caution': '精神药品，需医生处方；长期使用易产生依赖；服药后禁止驾驶。',
        'description': '处方镇静催眠药，仅作反例，系统不推荐自行使用。',
    },
]


class Command(BaseCommand):
    help = '初始化家庭药箱种子数据（12+ 种常用药与药箱样例）'

    def handle(self, *args, **options):
        created_meds = 0
        for item in MEDICATIONS:
            defaults = {k: v for k, v in item.items() if k != 'name'}
            _, created = Medication.objects.get_or_create(
                name=item['name'], defaults=defaults
            )
            if created:
                created_meds += 1
        self.stdout.write(f'药品创建 {created_meds} 条，共 {Medication.objects.count()} 条')

        owners = []
        admin_user = User.objects.filter(username='admin').first()
        if admin_user:
            owners.append(admin_user)
        patient_user = User.objects.filter(role='patient').order_by('id').first()
        if patient_user:
            owners.append(patient_user)
        if not owners:
            self.stdout.write('未找到 admin / patient 用户，跳过药箱样例')
            return

        today = date.today()
        samples = [
            {
                'medication': '对乙酰氨基酚片',
                'quantity': Decimal('3'),
                'unit': '盒',
                'expiry_date': today + timedelta(days=20),
                'opened_at': today - timedelta(days=10),
                'location': '客厅药箱',
                'notes': '感冒发热备用，20 天后过期',
            },
            {
                'medication': '布洛芬缓释胶囊',
                'quantity': Decimal('2'),
                'unit': '盒',
                'expiry_date': today - timedelta(days=10),
                'location': '客厅药箱',
                'notes': '已过期，请及时清理',
            },
            {
                'medication': '氯雷他定片',
                'quantity': Decimal('1'),
                'unit': '盒',
                'expiry_date': today + timedelta(days=200),
                'location': '卧室抽屉',
                'notes': '剩余 1 盒，库存偏低',
            },
            {
                'medication': '蒙脱石散',
                'quantity': Decimal('2'),
                'unit': '盒',
                'expiry_date': today + timedelta(days=365),
                'location': '随身包',
                'notes': '腹泻应急使用',
            },
        ]

        created_items = 0
        for owner in owners:
            for sample in samples:
                med = Medication.objects.filter(name=sample['medication']).first()
                if not med:
                    continue
                defaults = {k: v for k, v in sample.items() if k != 'medication'}
                _, created = HomeCabinetItem.objects.get_or_create(
                    owner=owner,
                    medication=med,
                    name=med.name,
                    defaults=defaults,
                )
                if created:
                    created_items += 1
        self.stdout.write(f'药箱样例创建 {created_items} 条')
        self.stdout.write(self.style.SUCCESS('种子数据初始化完成'))
