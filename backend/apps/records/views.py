from datetime import timedelta, date

from django.db.models import Q, Count
from django.db.models.functions import TruncDate, ExtractIsoWeekDay
from django.utils import timezone
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.family.models import FamilyBinding
from apps.plans.models import PlanReminder
from apps.records.models import MedicationRecord
from apps.records.serializers import MedicationRecordSerializer


def _is_authorized_for(user, patient_id):
    """判断用户是否有权访问指定患者的服药记录（本人、绑定家属或管理员）。"""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff or getattr(user, 'role', None) == 'admin':
        return True
    if user.id == patient_id:
        return True
    if FamilyBinding.objects.filter(patient_id=patient_id, family_member=user, is_authorized=True).exists():
        return True
    return False


def _default_patient_id(user):
    """patient 返回自己，family 返回第一个绑定患者，其他返回 None。"""
    if getattr(user, 'role', None) == 'patient':
        return user.id
    if getattr(user, 'role', None) == 'family':
        fb = FamilyBinding.objects.filter(
            family_member=user, is_authorized=True
        ).order_by('id').first()
        return fb.patient_id if fb else None
    return None


class IsRecordOwnerOrFamilyOrAdmin(permissions.BasePermission):
    """服药记录访问权限：本人、绑定家属或管理员可访问。"""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return _is_authorized_for(request.user, obj.patient_id)


class MedicationRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicationRecord.objects.all()
    serializer_class = MedicationRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsRecordOwnerOrFamilyOrAdmin]

    def get_queryset(self):
        user = self.request.user
        queryset = MedicationRecord.objects.select_related('medication', 'plan', 'patient')

        # 基于用户角色过滤
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            family_patient_ids = FamilyBinding.objects.filter(
                family_member=user, is_authorized=True
            ).values_list('patient_id', flat=True)
            queryset = queryset.filter(
                Q(patient=user) | Q(patient_id__in=family_patient_ids)
            )

        # query_params 过滤
        patient_id = self.request.query_params.get('patient_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        status_param = self.request.query_params.get('status')
        ordering = self.request.query_params.get('ordering')

        if patient_id:
            if not _is_authorized_for(user, int(patient_id)):
                return MedicationRecord.objects.none()
            queryset = queryset.filter(patient_id=patient_id)
        if start_date:
            queryset = queryset.filter(scheduled_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_time__date__lte=end_date)
        if status_param:
            queryset = queryset.filter(status=status_param)
        if ordering:
            field = ordering.lstrip('-')
            if field in ('scheduled_time', 'taken_time', 'created_at'):
                queryset = queryset.order_by(ordering)

        return queryset

    def perform_create(self, serializer):
        # 强制写入当前用户为患者（除非管理员）
        user = self.request.user
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            serializer.save(patient=user)
        else:
            serializer.save()

    @action(detail=False, methods=['post'], url_path='mark-taken')
    def mark_taken(self, request):
        """根据 reminder_id 标记已服。"""
        reminder_id = request.data.get('reminder_id')
        if not reminder_id:
            return Response(
                {'detail': '缺少 reminder_id 参数'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            reminder = PlanReminder.objects.select_related(
                'plan', 'plan__medication', 'plan__patient'
            ).get(id=reminder_id)
        except PlanReminder.DoesNotExist:
            return Response(
                {'detail': '提醒不存在'},
                status=status.HTTP_404_NOT_FOUND,
            )

        patient = reminder.plan.patient

        # 权限校验
        if not _is_authorized_for(request.user, patient.id):
            return Response(
                {'detail': '无权操作该患者的提醒'},
                status=status.HTTP_403_FORBIDDEN,
            )

        taken_time = request.data.get('taken_time') or timezone.now()
        if isinstance(taken_time, str):
            from django.utils.dateparse import parse_datetime
            taken_time = parse_datetime(taken_time) or timezone.now()
        # 前端可能传 UTC ISO 串，USE_TZ=False 下需归一化为 naive 本地时间，避免差 8 小时
        if taken_time and taken_time.tzinfo is not None:
            taken_time = timezone.localtime(taken_time).replace(tzinfo=None)

        scheduled_time = reminder.scheduled_time
        delay_minutes = int((taken_time - scheduled_time).total_seconds() // 60)
        if delay_minutes <= 0:
            record_status = MedicationRecord.STATUS_TAKEN
            delay_minutes = 0
        else:
            record_status = MedicationRecord.STATUS_LATE

        notes = request.data.get('notes', '')

        # 更新 reminder 状态
        reminder.status = PlanReminder.StatusChoices.TAKEN
        reminder.save()

        record, created = MedicationRecord.objects.update_or_create(
            reminder=reminder,
            defaults={
                'plan': reminder.plan,
                'patient': patient,
                'medication': reminder.plan.medication,
                'taken_time': taken_time,
                'scheduled_time': scheduled_time,
                'status': record_status,
                'delay_minutes': delay_minutes,
                'notes': notes,
            },
        )
        # 服药冲突提醒：本次服用的药与患者其他在用药物存在重复成分/风险时返回警告
        warnings = []
        try:
            from apps.clinic.services import check_interactions

            for finding in check_interactions(patient.id):
                med_ids = {m.get('id') for m in finding.get('medications', [])}
                if (
                    reminder.plan.medication_id in med_ids
                    and finding.get('level') in ('high', 'medium')
                ):
                    warnings.append({
                        'level': finding['level'],
                        'title': finding['title'],
                        'detail': finding['detail'],
                        'medications': finding.get('medications', []),
                    })
        except Exception:
            warnings = []

        data = MedicationRecordSerializer(record).data
        data['warnings'] = warnings
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='adherence-stats')
    def adherence_stats(self, request):
        """依从率统计：概览 + 按天趋势 + 漏服星期分布。

        参数：patient_id（患者/家属可省略）、start_date、end_date、days（相对天数）。
        """
        user = request.user
        patient_id = request.query_params.get('patient_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        days = request.query_params.get('days')

        if not patient_id:
            patient_id = _default_patient_id(user)
            if not patient_id:
                return Response(
                    {'detail': '请指定 patient_id 参数'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif not _is_authorized_for(user, int(patient_id)):
            return Response(
                {'detail': '无权查看该患者的统计数据'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # days 参数：相对今天往前 N 天
        now = timezone.now()
        if days:
            try:
                start_date = (now - timedelta(days=int(days))).date().isoformat()
                end_date = now.date().isoformat()
            except ValueError:
                pass

        reminder_q = PlanReminder.objects.filter(
            plan__patient_id=patient_id
        ).exclude(status=PlanReminder.StatusChoices.SKIPPED)
        record_q = MedicationRecord.objects.filter(patient_id=patient_id)

        if start_date:
            reminder_q = reminder_q.filter(scheduled_time__date__gte=start_date)
            record_q = record_q.filter(scheduled_time__date__gte=start_date)
        if end_date:
            reminder_q = reminder_q.filter(scheduled_time__date__lte=end_date)
            record_q = record_q.filter(scheduled_time__date__lte=end_date)

        total = reminder_q.count()
        on_time = record_q.filter(status=MedicationRecord.STATUS_TAKEN).count()
        late = record_q.filter(status=MedicationRecord.STATUS_LATE).count()
        missed = record_q.filter(status=MedicationRecord.STATUS_MISSED).count()
        skipped = record_q.filter(status=MedicationRecord.STATUS_SKIPPED).count()
        taken_total = on_time + late
        rate = round(taken_total / total * 100, 1) if total else 0.0

        # 按天趋势：应服次数(提醒) 与 依从率
        daily = []
        if start_date and end_date:
            try:
                d = date.fromisoformat(start_date)
                end_d = date.fromisoformat(end_date)
            except ValueError:
                d = end_d = None
            if d and end_d and (end_d - d).days <= 400:
                rem_by_day = dict(
                    reminder_q.annotate(day=TruncDate('scheduled_time'))
                    .values_list('day').annotate(c=Count('id'))
                )
                rec_by_day = dict(
                    record_q.filter(
                        status__in=[MedicationRecord.STATUS_TAKEN, MedicationRecord.STATUS_LATE]
                    ).annotate(day=TruncDate('scheduled_time'))
                    .values_list('day').annotate(c=Count('id'))
                )
                while d <= end_d:
                    t = rem_by_day.get(d, 0)
                    k = rec_by_day.get(d, 0)
                    daily.append({
                        'date': d.isoformat(),
                        'total': t,
                        'adherence_rate': round(k / t * 100, 1) if t else 0.0,
                    })
                    d += timedelta(days=1)

        # 漏服按星期分布（ISO weekday: 1=周一 ... 7=周日）
        by_weekday = list(
            record_q.filter(status=MedicationRecord.STATUS_MISSED)
            .annotate(weekday=ExtractIsoWeekDay('scheduled_time'))
            .values('weekday').annotate(count=Count('id'))
            .order_by('weekday')
        )

        return Response({
            'patient_id': int(patient_id),
            'start_date': start_date,
            'end_date': end_date,
            'total': total,
            'on_time': on_time,
            'late': late,
            'missed': missed,
            'skipped': skipped,
            'adherence_rate': rate,
            'daily': daily,
            'by_weekday': by_weekday,
        })
