from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Avg, Q
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.family.models import FamilyBinding
from apps.records.views import _default_patient_id, _is_authorized_for

from .catalog import SYMPTOM_CATALOG, get_symptom_options
from .models import HomeCabinetItem, MedicalCase, MedicationFeedback, SymptomConsultation
from .serializers import (
    HomeCabinetItemSerializer,
    MedicalCaseSerializer,
    MedicationFeedbackSerializer,
    SymptomConsultationSerializer,
)
from .services import (
    ask_llm,
    build_advice,
    check_interactions,
    collect_warnings,
    llm_enabled,
    llm_model_name,
    recommend,
)

User = get_user_model()


def _is_admin(user):
    return bool(user.is_staff or getattr(user, 'role', None) == 'admin')


def _family_patient_ids(user):
    return FamilyBinding.objects.filter(
        family_member=user, is_authorized=True
    ).values_list('patient_id', flat=True)


def _authorized_patient_qs(user):
    """非管理员可见的药品/反馈/病例：本人 + 已授权家属绑定的患者。"""
    if _is_admin(user):
        return None
    return [user.id, *_family_patient_ids(user)]


def _get_patient_id(request, data=None):
    """解析并校验 patient_id，返回 (patient_id, error_response)。"""
    raw = request.query_params.get('patient_id')
    if raw in (None, '') and data is not None:
        raw = data.get('patient_id')
    if raw in (None, ''):
        patient_id = _default_patient_id(request.user)
        if patient_id:
            return patient_id, None
        if _is_admin(request.user):
            return None, None
        return None, Response(
            {'detail': '请指定 patient_id 参数'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        patient_id = int(raw)
    except (TypeError, ValueError):
        return None, Response(
            {'detail': 'patient_id 必须为整数'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not _is_authorized_for(request.user, patient_id):
        return None, Response(
            {'detail': '无权访问该患者的数据'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return patient_id, None


def _to_int(value, default, low=None, high=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if low is not None:
        number = max(low, number)
    if high is not None:
        number = min(high, number)
    return number


class SymptomCatalogView(APIView):
    """症状目录（不分页）。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(get_symptom_options())


class ConsultView(APIView):
    """症状咨询：规则推荐 + 可选大模型建议。"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        patient_id, error = _get_patient_id(request, request.data)
        if error:
            return error
        if not patient_id:
            return Response(
                {'detail': '请指定 patient_id 参数'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        symptoms = request.data.get('symptoms') or []
        if not isinstance(symptoms, list):
            return Response(
                {'detail': 'symptoms 必须为数组'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        valid_symptoms = []
        for code in symptoms:
            if code in SYMPTOM_CATALOG and code not in valid_symptoms:
                valid_symptoms.append(code)

        free_text = (request.data.get('free_text') or '').strip()
        if not valid_symptoms and not free_text:
            return Response(
                {'detail': '请至少选择一个症状或填写补充描述'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        duration_days = _to_int(request.data.get('duration_days'), 1, low=1, high=365)
        severity = _to_int(request.data.get('severity'), 2, low=1, high=5)

        patient = User.objects.filter(id=patient_id).first()
        recommendations = recommend(patient, valid_symptoms, severity, duration_days)
        warnings = collect_warnings(valid_symptoms)
        advice = build_advice(
            valid_symptoms, severity, duration_days, recommendations, warnings
        )
        source = SymptomConsultation.SOURCE_RULE

        if llm_enabled():
            symptom_names = [
                SYMPTOM_CATALOG[code]['name'] for code in valid_symptoms
            ]
            med_text = '、'.join(rec['name'] for rec in recommendations) or '无'
            messages = [
                {
                    'role': 'system',
                    'content': (
                        '你是一位谨慎的社区药师。请用简体中文给出通俗的就医与用药建议，'
                        '不要推荐处方药，不要给出超说明书剂量，必须提示何时需要就医，'
                        '控制在 400 字以内。'
                    ),
                },
                {
                    'role': 'user',
                    'content': (
                        f'症状：{"、".join(symptom_names) or "未选择"}；'
                        f'严重程度 {severity}/5；持续 {duration_days} 天；'
                        f'补充描述：{free_text or "无"}。'
                        f'规则匹配的非处方药：{med_text}。'
                        f'危险信号：{"；".join(warnings) or "无"}。'
                        '请给出症状概述、用药建议、注意事项和何时就医。'
                    ),
                },
            ]
            llm_advice = ask_llm(messages)
            if llm_advice:
                advice = llm_advice
                source = SymptomConsultation.SOURCE_LLM

        consultation = SymptomConsultation.objects.create(
            patient_id=patient_id,
            symptoms=valid_symptoms,
            free_text=free_text,
            duration_days=duration_days,
            severity=severity,
            advice=advice,
            source=source,
            recommendations=recommendations,
            warnings=warnings,
        )

        return Response({
            'id': consultation.id,
            'symptoms': consultation.symptoms,
            'advice': consultation.advice,
            'source': consultation.source,
            'warnings': consultation.warnings,
            'recommendations': consultation.recommendations,
        }, status=status.HTTP_201_CREATED)


class InteractionsView(APIView):
    """用药相互作用 / 重复用药检测。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        patient_id, error = _get_patient_id(request)
        if error:
            return error
        if not patient_id:
            return Response({'patient_id': None, 'findings': []})
        return Response({
            'patient_id': patient_id,
            'findings': check_interactions(patient_id),
        })


class HomeCabinetItemViewSet(viewsets.ModelViewSet):
    """家庭药箱。"""

    queryset = HomeCabinetItem.objects.all()
    serializer_class = HomeCabinetItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = HomeCabinetItem.objects.select_related('medication', 'owner')

        patient_ids = _authorized_patient_qs(user)
        if patient_ids is not None:
            queryset = queryset.filter(owner_id__in=patient_ids)

        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            try:
                patient_id = int(patient_id)
            except (TypeError, ValueError):
                return HomeCabinetItem.objects.none()
            if not _is_authorized_for(user, patient_id):
                return HomeCabinetItem.objects.none()
            queryset = queryset.filter(owner_id=patient_id)

        return queryset

    def create(self, request, *args, **kwargs):
        user = request.user
        raw_patient_id = request.data.get('patient_id')
        if _is_admin(user) and raw_patient_id:
            try:
                owner_id = int(raw_patient_id)
            except (TypeError, ValueError):
                return Response(
                    {'detail': 'patient_id 必须为整数'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not User.objects.filter(id=owner_id).exists():
                return Response(
                    {'detail': '该患者不存在'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            owner_id = user.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner_id=owner_id)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=['get'], url_path='alerts')
    def alerts(self, request):
        """过期、临期（30 天内）与低库存（数量 <= 1）提醒。"""
        today = date.today()
        queryset = self.get_queryset()
        expired_qs = queryset.filter(expiry_date__lt=today)
        expiring_qs = queryset.filter(
            expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30)
        )
        low_stock_qs = queryset.filter(quantity__lte=1)

        return Response({
            'expired': self.get_serializer(expired_qs, many=True).data,
            'expiring': self.get_serializer(expiring_qs, many=True).data,
            'low_stock': self.get_serializer(low_stock_qs, many=True).data,
        })


class MedicationFeedbackViewSet(viewsets.ModelViewSet):
    """用药反馈（不良反应 / 疗效自评）。"""

    queryset = MedicationFeedback.objects.all()
    serializer_class = MedicationFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = MedicationFeedback.objects.select_related('medication', 'patient')

        patient_ids = _authorized_patient_qs(user)
        if patient_ids is not None:
            queryset = queryset.filter(patient_id__in=patient_ids)

        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            try:
                patient_id = int(patient_id)
            except (TypeError, ValueError):
                return MedicationFeedback.objects.none()
            if not _is_authorized_for(user, patient_id):
                return MedicationFeedback.objects.none()
            queryset = queryset.filter(patient_id=patient_id)

        kind = self.request.query_params.get('kind')
        if kind:
            queryset = queryset.filter(kind=kind)

        return queryset

    def create(self, request, *args, **kwargs):
        patient_id, error = _get_patient_id(request, request.data)
        if error:
            return error
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save(patient_id=patient_id)
        if feedback.medication and not feedback.medication_name:
            feedback.medication_name = feedback.medication.name
            feedback.save(update_fields=['medication_name'])
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """反馈汇总：不良反应次数、平均疗效、按药品统计。"""
        patient_id, error = _get_patient_id(request)
        if error:
            return error
        if not patient_id:
            return Response({
                'adverse_count': 0,
                'avg_efficacy': None,
                'items': [],
            })

        days = _to_int(request.query_params.get('days'), 30, low=1, high=365)
        since = timezone.now() - timedelta(days=days)
        queryset = MedicationFeedback.objects.filter(
            patient_id=patient_id, created_at__gte=since
        )

        adverse_count = queryset.filter(kind=MedicationFeedback.KIND_ADVERSE).count()
        avg_efficacy = queryset.filter(
            kind=MedicationFeedback.KIND_EFFICACY, efficacy_score__isnull=False
        ).aggregate(value=Avg('efficacy_score'))['value']
        avg_efficacy = round(float(avg_efficacy), 2) if avg_efficacy else None

        aggregated = {}
        rows = queryset.values_list(
            'medication_name', 'medication__name', 'kind', 'severity'
        )
        for med_name, bound_name, kind, severity in rows:
            name = med_name or bound_name or '未命名药品'
            entry = aggregated.setdefault(name, {'count': 0, 'severities': []})
            entry['count'] += 1
            if kind == MedicationFeedback.KIND_ADVERSE and severity:
                entry['severities'].append(severity)

        items = []
        for name, entry in aggregated.items():
            severities = entry['severities']
            items.append({
                'medication_name': name,
                'count': entry['count'],
                'avg_severity': (
                    round(sum(severities) / len(severities), 2) if severities else None
                ),
            })
        items.sort(key=lambda item: -item['count'])

        return Response({
            'adverse_count': adverse_count,
            'avg_efficacy': avg_efficacy,
            'items': items,
        })


class MedicalCaseViewSet(viewsets.ModelViewSet):
    """病例（支持 multipart 上传附件）。"""

    queryset = MedicalCase.objects.all()
    serializer_class = MedicalCaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = MedicalCase.objects.select_related('patient')

        patient_ids = _authorized_patient_qs(user)
        if patient_ids is not None:
            queryset = queryset.filter(patient_id__in=patient_ids)

        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            try:
                patient_id = int(patient_id)
            except (TypeError, ValueError):
                return MedicalCase.objects.none()
            if not _is_authorized_for(user, patient_id):
                return MedicalCase.objects.none()
            queryset = queryset.filter(patient_id=patient_id)

        return queryset

    def create(self, request, *args, **kwargs):
        patient_id, error = _get_patient_id(request, request.data)
        if error:
            return error
        if not patient_id:
            return Response(
                {'detail': '请指定 patient_id 参数'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(patient_id=patient_id)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class LLMStatusView(APIView):
    """大模型可用状态。"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'enabled': llm_enabled(),
            'model': llm_model_name(),
        })
