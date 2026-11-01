from datetime import date

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, BasePermission

from .models import MedicationPlan, PlanReminder
from .scheduler import ensure_reminders_for_date
from .serializers import MedicationPlanSerializer, PlanReminderSerializer


class IsOwnerOrAdmin(BasePermission):
    """仅 owner 或 admin 可修改"""

    def has_permission(self, request, view):
        # list / retrieve 在单独 ViewSet 中控制，这里只拦截 create
        if view.action == 'create':
            return request.user and request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        # owner 判定
        if hasattr(obj, 'patient'):
            return obj.patient_id == user.id
        return False


class MedicationPlanViewSet(viewsets.ModelViewSet):
    """用药计划：list/retrieve 所有已登录用户可读，create/update/delete 仅 owner 或 admin"""

    queryset = MedicationPlan.objects.select_related('patient', 'medication').all()
    serializer_class = MedicationPlanSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsOwnerOrAdmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        patient_id = self.request.query_params.get('patient_id')
        status_param = self.request.query_params.get('status')

        # 患者默认只看自己的计划；家属/admin 可看全部（或按 patient_id 过滤）
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            if getattr(user, 'role', None) == 'patient':
                qs = qs.filter(patient=user)

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if status_param == 'active':
            qs = qs.filter(is_active=True)
        elif status_param == 'inactive':
            qs = qs.filter(is_active=False)
        return qs


class PlanReminderViewSet(viewsets.ReadOnlyModelViewSet):
    """服药提醒：仅可读，支持 ?patient_id= / ?date= / ?status= 过滤"""

    queryset = PlanReminder.objects.select_related('plan', 'plan__patient', 'plan__medication').all()
    serializer_class = PlanReminderSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'head', 'options']  # 只读

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        params = self.request.query_params

        # 患者默认只看自己的提醒；家属看绑定患者的；admin 可看全部
        if not (user.is_staff or getattr(user, 'role', None) == 'admin'):
            if getattr(user, 'role', None) == 'patient':
                qs = qs.filter(plan__patient=user)
            elif getattr(user, 'role', None) == 'family':
                from apps.family.models import FamilyBinding
                patient_ids = FamilyBinding.objects.filter(
                    family_member=user, is_authorized=True
                ).values_list('patient_id', flat=True)
                qs = qs.filter(plan__patient_id__in=patient_ids)

        patient_id = params.get('patient_id')
        date_param = params.get('date')
        status_param = params.get('status')

        if patient_id:
            qs = qs.filter(plan__patient_id=patient_id)
        if date_param:
            # 调度器未运行时，按需生成当天提醒，保证今日可操作
            try:
                ensure_reminders_for_date(date.fromisoformat(date_param))
            except ValueError:
                pass
            qs = qs.filter(scheduled_time__date=date_param)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs
