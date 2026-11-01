"""医生接诊 / 患者自助 / 管理员后台业务接口。"""
import shutil
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.medications.models import Medication
from apps.plans.models import MedicationPlan

from .models import (
    Appointment, AuditLog, CommunicationNote, Department, DoctorSchedule,
    ExamOrder, FeatureToggle, FollowUp, Payment, Prescription,
    PrescriptionItem, Visit,
)

User = get_user_model()


def log(request, action_name, target='', detail=''):
    try:
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            username=getattr(request.user, 'username', '') or '',
            role=getattr(request.user, 'role', '') or '',
            action=action_name, target=target, detail=detail,
            ip=(request.META.get('REMOTE_ADDR') or '')[:64],
        )
    except Exception:
        pass


def is_admin(user):
    return bool(user.is_staff or getattr(user, 'role', None) == 'admin')


def is_doctor(user):
    return getattr(user, 'role', None) == 'doctor'


class IsDoctorOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (is_doctor(u) or is_admin(u)))


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and is_admin(u))


# ----------------------------- Serializers -----------------------------


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class DoctorScheduleSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.real_name', read_only=True)
    doctor_username = serializers.CharField(source='doctor.username', read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = '__all__'


class ExamOrderSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ExamOrder
        fields = '__all__'
        read_only_fields = ['visit', 'patient', 'doctor']


class CommunicationNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationNote
        fields = '__all__'
        read_only_fields = ['created_by']


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = ['id', 'medication', 'medication_name', 'specification', 'dosage',
                  'frequency', 'days', 'quantity', 'unit_price']


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='patient.real_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.real_name', read_only=True)

    class Meta:
        model = Prescription
        fields = ['id', 'visit', 'patient', 'patient_name', 'doctor', 'doctor_name',
                  'diagnosis', 'status', 'total_amount', 'created_at', 'items']
        read_only_fields = ['patient', 'doctor', 'total_amount', 'status']


class FollowUpSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.real_name', read_only=True)

    class Meta:
        model = FollowUp
        fields = '__all__'
        read_only_fields = ['patient', 'doctor']


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.real_name', read_only=True)
    patient_username = serializers.CharField(source='patient.username', read_only=True)
    doctor_name = serializers.CharField(source='doctor.real_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['patient', 'fee', 'status']


class PaymentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.real_name', read_only=True)
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['patient', 'amount', 'status', 'paid_at']


class VisitSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.real_name', read_only=True)
    patient_username = serializers.CharField(source='patient.username', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone', read_only=True)
    patient_allergies = serializers.CharField(source='patient.allergies', read_only=True)
    doctor_name = serializers.CharField(source='doctor.real_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    visit_type_display = serializers.CharField(source='get_visit_type_display', read_only=True)

    class Meta:
        model = Visit
        fields = '__all__'
        read_only_fields = ['doctor', 'is_archived', 'finished_at']


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'


class FeatureToggleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureToggle
        fields = '__all__'


# ----------------------------- Views -----------------------------


def _scope_visit(qs, user):
    if is_admin(user):
        return qs
    if is_doctor(user):
        return qs.filter(doctor=user)
    return qs.filter(patient=user)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdminRole()]


class DoctorScheduleViewSet(viewsets.ModelViewSet):
    queryset = DoctorSchedule.objects.select_related('doctor')
    serializer_class = DoctorScheduleSerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdminRole()]

    def get_queryset(self):
        qs = super().get_queryset()
        doctor = self.request.query_params.get('doctor')
        if doctor:
            qs = qs.filter(doctor_id=doctor)
        elif is_doctor(self.request.user) and self.action in ('list', 'retrieve'):
            qs = qs.filter(doctor=self.request.user)
        return qs


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.select_related('patient', 'doctor', 'department')
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_admin(self.request.user):
            if is_doctor(self.request.user):
                qs = qs.filter(doctor=self.request.user)
            else:
                qs = qs.filter(patient=self.request.user)
        d = self.request.query_params.get('visit_date')
        if d:
            qs = qs.filter(visit_date=d)
        st = self.request.query_params.get('status')
        if st:
            qs = qs.filter(status=st)
        return qs

    def perform_create(self, serializer):
        toggle = FeatureToggle.objects.filter(key='online_appointment').first()
        if toggle and not toggle.enabled:
            raise serializers.ValidationError({'detail': '网上预约挂号功能已关闭'})
        appointment = serializer.save(patient=self.request.user, fee=Decimal('10'))
        Payment.objects.create(
            patient=self.request.user, kind='REG',
            title=f'挂号费 · {appointment.visit_date} {appointment.time_slot}',
            amount=appointment.fee, appointment=appointment,
        )
        log(self.request, 'book_appointment', f'挂号#{appointment.id}', f'{appointment.visit_date} {appointment.time_slot}')

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status != 'BOOKED':
            return Response({'detail': '只有待就诊的预约才能取消'}, status=status.HTTP_400_BAD_REQUEST)
        appointment.status = 'CANCELLED'
        appointment.save()
        # 未支付的挂号费作废
        appointment.payments.filter(status='UNPAID').delete()
        log(request, 'cancel_appointment', f'挂号#{appointment.id}', '患者取消预约')
        return Response(AppointmentSerializer(appointment).data)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Payment.objects.select_related('patient')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if not is_admin(self.request.user):
            qs = qs.filter(patient=self.request.user)
        st = self.request.query_params.get('status')
        if st:
            qs = qs.filter(status=st)
        return qs

    @action(detail=True, methods=['post'], url_path='pay')
    def pay(self, request, pk=None):
        payment = self.get_object()
        if payment.status == 'PAID':
            return Response({'detail': '该费用已支付'}, status=status.HTTP_400_BAD_REQUEST)
        payment.status = 'PAID'
        payment.paid_at = timezone.now()
        payment.save()
        log(request, 'pay', f'{payment.get_kind_display()} ¥{payment.amount}', payment.title)
        return Response(PaymentSerializer(payment).data)


class VisitViewSet(viewsets.ModelViewSet):
    queryset = Visit.objects.select_related('patient', 'doctor', 'appointment')
    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = _scope_visit(super().get_queryset(), self.request.user)
        st = self.request.query_params.get('status')
        if st:
            qs = qs.filter(status=st)
        d = self.request.query_params.get('visit_date')
        if d:
            qs = qs.filter(created_at__date=d)
        pid = self.request.query_params.get('patient')
        if pid:
            qs = qs.filter(patient_id=pid)
        return qs

    def perform_create(self, serializer):
        if not (is_doctor(self.request.user) or is_admin(self.request.user)):
            raise serializers.ValidationError({'detail': '只有医生可以创建接诊记录'})
        visit = serializer.save(doctor=self.request.user)
        if visit.appointment:
            visit.appointment.status = 'DONE'
            visit.appointment.save()
        log(self.request, 'start_visit', f'接诊#{visit.id}', f'患者：{visit.patient.username}')

    def update(self, request, *args, **kwargs):
        visit = self.get_object()
        if visit.is_archived:
            return Response(
                {'detail': '该病历已归档，不能直接修改，请提交修改申请以便留痕'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        visit = self.get_object()
        if visit.is_archived:
            return Response(
                {'detail': '该病历已归档，不能直接修改，请提交修改申请以便留痕'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='finish')
    def finish(self, request, pk=None):
        visit = self.get_object()
        if visit.status == 'FINISHED':
            return Response({'detail': '该接诊已完成'}, status=status.HTTP_400_BAD_REQUEST)
        visit.status = 'FINISHED'
        visit.is_archived = True
        visit.finished_at = timezone.now()
        visit.save()
        log(request, 'finish_visit', f'接诊#{visit.id}', visit.diagnosis or '完成接诊')
        return Response(VisitSerializer(visit).data)

    @action(detail=True, methods=['post'], url_path='exam-orders')
    def add_exam_order(self, request, pk=None):
        visit = self.get_object()
        name = (request.data.get('name') or '').strip()
        if not name:
            return Response({'detail': '请填写检查项目'}, status=status.HTTP_400_BAD_REQUEST)
        price = Decimal(str(request.data.get('price') or '0'))
        order = ExamOrder.objects.create(
            visit=visit, patient=visit.patient, doctor=visit.doctor,
            name=name,
            category=request.data.get('category') or 'LAB',
            price=price,
        )
        Payment.objects.create(
            patient=visit.patient, kind='EXAM',
            title=f'检查费 · {name}', amount=price, exam_order=order,
        )
        log(request, 'create_exam_order', f'检查单#{order.id}', name)
        return Response(ExamOrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='notes')
    def add_note(self, request, pk=None):
        visit = self.get_object()
        transcript = (request.data.get('transcript') or '').strip()
        if not transcript:
            return Response({'detail': '沟通内容为空'}, status=status.HTTP_400_BAD_REQUEST)
        note = CommunicationNote.objects.create(
            visit=visit, transcript=transcript, created_by=request.user,
            confirmed=bool(request.data.get('confirmed', False)),
        )
        log(request, 'add_comm_note', f'接诊#{visit.id}', transcript[:50])
        return Response(CommunicationNoteSerializer(note).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='prescriptions')
    def add_prescription(self, request, pk=None):
        visit = self.get_object()
        items = request.data.get('items') or []
        if not items:
            return Response({'detail': '请至少添加一种药品'}, status=status.HTTP_400_BAD_REQUEST)

        prescription = Prescription.objects.create(
            visit=visit, patient=visit.patient, doctor=visit.doctor,
            diagnosis=request.data.get('diagnosis') or visit.diagnosis or '',
        )
        total = Decimal('0')
        today = date.today()
        for it in items:
            med_id = it.get('medication')
            med = Medication.objects.filter(id=med_id).first() if med_id else None
            name = it.get('medication_name') or (med.name if med else '')
            if not name:
                continue
            qty = Decimal(str(it.get('quantity') or '1'))
            unit_price = Decimal(str(it.get('unit_price') or (med.price if med else 0)))
            item = PrescriptionItem.objects.create(
                prescription=prescription, medication=med, medication_name=name,
                specification=(med.specification if med else '') or '',
                dosage=it.get('dosage') or '', frequency=it.get('frequency') or '',
                days=int(it.get('days') or 1), quantity=qty, unit_price=unit_price,
            )
            total += qty * unit_price
            # 处方药品同步进入患者用药计划（同药已有启用计划则不重复）
            if med:
                freq_map = {'每日一次': 'DAILY', '每日两次': 'BID', '每日三次': 'TID',
                            '每日四次': 'QID', 'QD': 'DAILY', 'BID': 'BID', 'TID': 'TID', 'QID': 'QID'}
                freq = freq_map.get(item.frequency) or 'DAILY'
                exists = MedicationPlan.objects.filter(
                    patient=visit.patient, medication=med, is_active=True
                ).exists()
                if not exists:
                    MedicationPlan.objects.create(
                        patient=visit.patient, medication=med,
                        dosage_per_time=Decimal(str(it.get('dosage') or '1').split('片')[0] or '1') if str(it.get('dosage') or '1').split('片')[0].replace('.', '', 1).isdigit() else Decimal('1'),
                        frequency=freq, start_date=today,
                        end_date=today + timedelta(days=item.days - 1),
                        notes=f'医生处方#{prescription.id}',
                    )
        prescription.total_amount = total
        prescription.save()
        Payment.objects.create(
            patient=visit.patient, kind='DRUG',
            title=f'药费 · 处方#{prescription.id}', amount=total, prescription=prescription,
        )
        log(request, 'create_prescription', f'处方#{prescription.id}', f'共 {len(items)} 种药，¥{total}')
        return Response(PrescriptionSerializer(prescription).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='follow-up')
    def add_follow_up(self, request, pk=None):
        visit = self.get_object()
        due = request.data.get('due_date')
        if not due:
            return Response({'detail': '请选择复诊日期'}, status=status.HTTP_400_BAD_REQUEST)
        fu = FollowUp.objects.create(
            visit=visit, patient=visit.patient, doctor=visit.doctor,
            due_date=due, note=request.data.get('note') or '',
        )
        log(request, 'create_follow_up', f'复诊#{fu.id}', str(due))
        return Response(FollowUpSerializer(fu).data, status=status.HTTP_201_CREATED)


class ExamOrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ExamOrder.objects.select_related('patient', 'doctor', 'visit')
    serializer_class = ExamOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if is_admin(self.request.user):
            return qs
        if is_doctor(self.request.user):
            return qs.filter(doctor=self.request.user)
        return qs.filter(patient=self.request.user)


class PrescriptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Prescription.objects.select_related('patient', 'doctor', 'visit').prefetch_related('items')
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if is_admin(self.request.user):
            return qs
        if is_doctor(self.request.user):
            return qs.filter(doctor=self.request.user)
        return qs.filter(patient=self.request.user)


class CommunicationNoteViewSet(viewsets.ModelViewSet):
    queryset = CommunicationNote.objects.select_related('visit', 'created_by')
    serializer_class = CommunicationNoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if is_admin(self.request.user):
            return qs
        if is_doctor(self.request.user):
            return qs.filter(visit__doctor=self.request.user)
        return qs.filter(visit__patient=self.request.user)

    def perform_create(self, serializer):
        visit = serializer.validated_data.get('visit')
        if visit and visit.doctor_id != self.request.user.id and not is_admin(self.request.user):
            raise serializers.ValidationError({'detail': '只能为本人接诊记录录入沟通内容'})
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        note = self.get_object()
        note.confirmed = True
        note.save()
        log(request, 'confirm_comm_note', f'沟通记录#{note.id}', '医生确认录入')
        return Response(CommunicationNoteSerializer(note).data)


class FollowUpViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FollowUp.objects.select_related('patient', 'doctor')
    serializer_class = FollowUpSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if is_admin(self.request.user):
            return qs
        if is_doctor(self.request.user):
            return qs.filter(doctor=self.request.user)
        return qs.filter(patient=self.request.user)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class FeatureToggleViewSet(viewsets.ModelViewSet):
    queryset = FeatureToggle.objects.all()
    serializer_class = FeatureToggleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsAdminRole()]

    def perform_update(self, serializer):
        obj = serializer.save()
        log(self.request, 'toggle_feature', obj.name, '开启' if obj.enabled else '关闭')


class WorkbenchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if is_doctor(user):
            today = date.today()
            weekday = today.weekday()
            schedules = DoctorScheduleSerializer(
                DoctorSchedule.objects.filter(doctor=user, weekday=weekday), many=True
            ).data
            waiting = VisitSerializer(
                Visit.objects.filter(doctor=user, status__in=['WAITING', 'IN_PROGRESS'])
                .select_related('patient'), many=True
            ).data
            exams = ExamOrder.objects.filter(doctor=user, status='PENDING').count()
            follow = FollowUp.objects.filter(
                doctor=user, due_date__lte=today + timedelta(days=7)
            ).count()
            total_today = Visit.objects.filter(doctor=user, created_at__date=today).count()
            return Response({
                'schedules': schedules,
                'waiting': waiting,
                'pending_exams': exams,
                'pending_followups': follow,
                'today_visits': total_today,
            })

        if is_admin(user):
            today = date.today()
            return Response({
                'today_visits': Visit.objects.filter(created_at__date=today).count(),
                'waiting': Visit.objects.filter(status__in=['WAITING', 'IN_PROGRESS']).count(),
                'unpaid': Payment.objects.filter(status='UNPAID').count(),
                'users': User.objects.count(),
            })

        # 患者：查自己的待办
        today = date.today()
        return Response({
            'appointments': AppointmentSerializer(
                Appointment.objects.filter(patient=user, status='BOOKED').order_by('visit_date'), many=True
            ).data,
            'unpaid': PaymentSerializer(
                Payment.objects.filter(patient=user, status='UNPAID'), many=True
            ).data,
            'followups': FollowUpSerializer(
                FollowUp.objects.filter(patient=user, due_date__gte=today), many=True
            ).data,
        })


class DoctorListView(APIView):
    """可选医生列表（患者挂号、管理员排班使用）"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = User.objects.filter(role='doctor', is_active=True).order_by('department', 'id')
        data = [{
            'id': u.id,
            'username': u.username,
            'real_name': u.real_name or u.username,
            'department': u.department or '',
            'title': u.title or '',
            'phone': u.phone or '',
        } for u in qs]
        return Response(data)


class BackupView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request):
        src = Path(settings.BASE_DIR) / 'db.sqlite3'
        if not src.exists():
            return Response({'detail': '数据库文件不存在'}, status=status.HTTP_404_NOT_FOUND)
        out_dir = Path(settings.BASE_DIR) / 'backups'
        out_dir.mkdir(exist_ok=True)
        name = f'db_backup_{timezone.now().strftime("%Y%m%d_%H%M%S")}.sqlite3'
        dst = out_dir / name
        shutil.copy2(src, dst)
        log(request, 'backup_database', name, f'{dst.stat().st_size} bytes')
        return Response({'file': name, 'size': dst.stat().st_size, 'created_at': timezone.now().isoformat()})
