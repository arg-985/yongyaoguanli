from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.medications.models import Medication


class HomeCabinetItem(models.Model):
    """家庭药箱条目"""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cabinet_items',
        verbose_name='所有者',
    )
    medication = models.ForeignKey(
        Medication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='cabinet_items',
        verbose_name='关联药品',
        help_text='未绑定药品库时可留空，用 name 自由录入',
    )
    name = models.CharField(max_length=128, verbose_name='名称')
    quantity = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0'), verbose_name='数量'
    )
    unit = models.CharField(max_length=32, default='盒', verbose_name='单位')
    expiry_date = models.DateField(null=True, blank=True, verbose_name='有效期至')
    opened_at = models.DateField(null=True, blank=True, verbose_name='开封日期')
    location = models.CharField(
        max_length=64, blank=True, default='', verbose_name='存放位置'
    )
    notes = models.TextField(blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'home_cabinet_items'
        ordering = ['expiry_date', 'id']
        verbose_name = '家庭药箱'
        verbose_name_plural = '家庭药箱'

    def __str__(self):
        return f'{self.name} x {self.quantity}{self.unit}'

    @property
    def expiry_status(self):
        """expired / soon(<=30天) / normal / unknown"""
        if not self.expiry_date:
            return 'unknown'
        left = (self.expiry_date - date.today()).days
        if left < 0:
            return 'expired'
        if left <= 30:
            return 'soon'
        return 'normal'

    @property
    def days_left(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days


class SymptomConsultation(models.Model):
    """症状咨询记录"""

    SOURCE_RULE = 'rule'
    SOURCE_LLM = 'llm'
    SOURCE_CHOICES = [
        (SOURCE_RULE, '规则引擎'),
        (SOURCE_LLM, '大模型'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='consultations',
        verbose_name='患者',
    )
    symptoms = models.JSONField(default=list, verbose_name='症状编码')
    free_text = models.TextField(blank=True, default='', verbose_name='补充描述')
    duration_days = models.PositiveIntegerField(default=1, verbose_name='持续天数')
    severity = models.PositiveSmallIntegerField(default=2, verbose_name='严重程度')
    advice = models.TextField(blank=True, default='', verbose_name='建议')
    source = models.CharField(
        max_length=16, choices=SOURCE_CHOICES, default=SOURCE_RULE, verbose_name='建议来源'
    )
    recommendations = models.JSONField(default=list, blank=True, verbose_name='药品推荐')
    warnings = models.JSONField(default=list, blank=True, verbose_name='危险信号提醒')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'symptom_consultations'
        ordering = ['-created_at']
        verbose_name = '症状咨询'
        verbose_name_plural = '症状咨询'

    def __str__(self):
        return f'{self.patient} - {self.symptoms} ({self.created_at:%Y-%m-%d})'


class MedicationFeedback(models.Model):
    """用药反馈（不良反应 / 疗效自评）"""

    KIND_ADVERSE = 'adverse'
    KIND_EFFICACY = 'efficacy'
    KIND_CHOICES = [
        (KIND_ADVERSE, '不良反应'),
        (KIND_EFFICACY, '疗效自评'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medication_feedback',
        verbose_name='患者',
    )
    medication = models.ForeignKey(
        Medication,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='feedback',
        verbose_name='药物',
    )
    medication_name = models.CharField(
        max_length=128, blank=True, default='', verbose_name='药品名称'
    )
    kind = models.CharField(
        max_length=16, choices=KIND_CHOICES, default=KIND_ADVERSE, verbose_name='反馈类型'
    )
    severity = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='不良反应严重程度',
        help_text='仅不良反应使用，1-5',
    )
    efficacy_score = models.PositiveSmallIntegerField(
        null=True, blank=True, verbose_name='疗效评分',
        help_text='仅疗效自评使用，1-5',
    )
    description = models.TextField(blank=True, default='', verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'medication_feedback'
        ordering = ['-created_at']
        verbose_name = '用药反馈'
        verbose_name_plural = '用药反馈'

    def __str__(self):
        return f'{self.medication_name or self.medication} - {self.get_kind_display()}'


# ===================== 医生 / 患者 / 管理员业务闭环 =====================


class Department(models.Model):
    """科室（管理员维护）"""

    name = models.CharField(max_length=64, unique=True, verbose_name='科室名称')
    code = models.CharField(max_length=32, blank=True, default='', verbose_name='科室编码')
    description = models.TextField(blank=True, default='', verbose_name='科室简介')
    is_open = models.BooleanField(default=True, verbose_name='是否开放挂号')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'departments'
        ordering = ['id']
        verbose_name = '科室'
        verbose_name_plural = '科室'

    def __str__(self):
        return self.name


class DoctorSchedule(models.Model):
    """医生排班（管理员配置，医生查看）"""

    PERIOD_CHOICES = [('AM', '上午'), ('PM', '下午'), ('NIGHT', '夜班')]

    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='schedules', verbose_name='医生',
    )
    weekday = models.PositiveSmallIntegerField(
        default=0, verbose_name='星期', help_text='0=周一 … 6=周日',
    )
    period = models.CharField(max_length=8, choices=PERIOD_CHOICES, default='AM', verbose_name='时段')
    room = models.CharField(max_length=64, blank=True, default='', verbose_name='诊室')
    capacity = models.PositiveIntegerField(default=20, verbose_name='号源数量')

    class Meta:
        db_table = 'doctor_schedules'
        ordering = ['weekday', 'period']
        verbose_name = '医生排班'
        verbose_name_plural = '医生排班'

    def __str__(self):
        return f'{self.doctor} 周{self.weekday + 1} {self.get_period_display()}'


class Appointment(models.Model):
    """挂号预约"""

    STATUS_CHOICES = [
        ('BOOKED', '待就诊'),
        ('CANCELLED', '已取消'),
        ('DONE', '已完成'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='appointments', verbose_name='患者',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='doctor_appointments', verbose_name='医生',
    )
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='appointments', verbose_name='科室',
    )
    visit_date = models.DateField(verbose_name='就诊日期')
    time_slot = models.CharField(max_length=32, verbose_name='时间段')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='BOOKED', verbose_name='状态')
    fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('10'), verbose_name='挂号费')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'appointments'
        ordering = ['-visit_date', 'time_slot']
        verbose_name = '挂号预约'
        verbose_name_plural = '挂号预约'

    def __str__(self):
        return f'{self.patient} → {self.doctor} {self.visit_date} {self.time_slot}'


class Visit(models.Model):
    """一次接诊记录"""

    TYPE_CHOICES = [('FIRST', '初诊'), ('RETURN', '复诊')]
    STATUS_CHOICES = [('WAITING', '候诊'), ('IN_PROGRESS', '接诊中'), ('FINISHED', '已完成')]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='visits', verbose_name='患者',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='doctor_visits', verbose_name='医生',
    )
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='visits', verbose_name='关联挂号',
    )
    visit_type = models.CharField(max_length=8, choices=TYPE_CHOICES, default='FIRST', verbose_name='就诊类型')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='WAITING', verbose_name='状态')
    identity_verified = models.BooleanField(default=False, verbose_name='身份已核对')
    id_card_no = models.CharField(max_length=64, blank=True, default='', verbose_name='就诊卡/病历号')
    chief_complaint = models.TextField(blank=True, default='', verbose_name='主诉')
    history = models.TextField(blank=True, default='', verbose_name='现病史')
    diagnosis = models.TextField(blank=True, default='', verbose_name='诊断')
    advice = models.TextField(blank=True, default='', verbose_name='处置意见')
    is_archived = models.BooleanField(default=False, verbose_name='是否归档')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')

    class Meta:
        db_table = 'visits'
        ordering = ['-created_at']
        verbose_name = '接诊记录'
        verbose_name_plural = '接诊记录'

    def __str__(self):
        return f'{self.patient} - {self.doctor} ({self.get_status_display()})'


class ExamOrder(models.Model):
    """检查单"""

    CATEGORY_CHOICES = [('LAB', '检验'), ('IMG', '影像'), ('OTHER', '其他')]
    STATUS_CHOICES = [('PENDING', '待检查'), ('REPORTED', '已出报告')]

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name='exam_orders', verbose_name='接诊记录',
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_orders', verbose_name='患者',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_exam_orders', verbose_name='开单医生',
    )
    name = models.CharField(max_length=128, verbose_name='检查项目')
    category = models.CharField(max_length=8, choices=CATEGORY_CHOICES, default='LAB', verbose_name='类别')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDING', verbose_name='状态')
    result = models.TextField(blank=True, default='', verbose_name='检查结果')
    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0'), verbose_name='费用')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='开单时间')

    class Meta:
        db_table = 'exam_orders'
        ordering = ['-created_at']
        verbose_name = '检查单'
        verbose_name_plural = '检查单'

    def __str__(self):
        return f'{self.name} ({self.patient})'


class CommunicationNote(models.Model):
    """医患沟通记录（录音转文字后由医生确认录入）"""

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name='comm_notes', verbose_name='接诊记录',
    )
    transcript = models.TextField(verbose_name='沟通文字内容')
    confirmed = models.BooleanField(default=False, verbose_name='医生已确认')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='comm_notes', verbose_name='录入人',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'communication_notes'
        ordering = ['-created_at']
        verbose_name = '沟通记录'
        verbose_name_plural = '沟通记录'

    def __str__(self):
        return f'{self.visit_id} - {self.transcript[:20]}'


class Prescription(models.Model):
    """处方"""

    STATUS_CHOICES = [('ISSUED', '已开具'), ('CANCELLED', '已作废')]

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name='prescriptions', verbose_name='接诊记录',
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='prescriptions', verbose_name='患者',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='doctor_prescriptions', verbose_name='开方医生',
    )
    diagnosis = models.CharField(max_length=255, blank=True, default='', verbose_name='临床诊断')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='ISSUED', verbose_name='状态')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'), verbose_name='处方金额')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='开方时间')

    class Meta:
        db_table = 'prescriptions'
        ordering = ['-created_at']
        verbose_name = '处方'
        verbose_name_plural = '处方'

    def __str__(self):
        return f'处方#{self.id} {self.patient}'


class PrescriptionItem(models.Model):
    """处方明细"""

    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name='items', verbose_name='处方',
    )
    medication = models.ForeignKey(
        Medication, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='prescription_items', verbose_name='药品',
    )
    medication_name = models.CharField(max_length=128, verbose_name='药品名称')
    specification = models.CharField(max_length=128, blank=True, default='', verbose_name='规格')
    dosage = models.CharField(max_length=64, blank=True, default='', verbose_name='每次剂量')
    frequency = models.CharField(max_length=32, blank=True, default='', verbose_name='用法频次')
    days = models.PositiveIntegerField(default=1, verbose_name='天数')
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1'), verbose_name='数量')
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0'), verbose_name='单价')

    class Meta:
        db_table = 'prescription_items'
        ordering = ['id']
        verbose_name = '处方明细'
        verbose_name_plural = '处方明细'

    def __str__(self):
        return f'{self.medication_name} ×{self.quantity}'


class FollowUp(models.Model):
    """复诊预约"""

    visit = models.ForeignKey(
        Visit, on_delete=models.CASCADE, related_name='follow_ups', verbose_name='接诊记录',
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='follow_ups', verbose_name='患者',
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='doctor_follow_ups', verbose_name='医生',
    )
    due_date = models.DateField(verbose_name='复诊日期')
    note = models.CharField(max_length=255, blank=True, default='', verbose_name='复诊说明')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'follow_ups'
        ordering = ['due_date']
        verbose_name = '复诊预约'
        verbose_name_plural = '复诊预约'

    def __str__(self):
        return f'{self.patient} {self.due_date}'


class Payment(models.Model):
    """缴费单"""

    KIND_CHOICES = [('REG', '挂号费'), ('EXAM', '检查费'), ('DRUG', '药费')]
    STATUS_CHOICES = [('UNPAID', '待支付'), ('PAID', '已支付')]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='payments', verbose_name='患者',
    )
    kind = models.CharField(max_length=8, choices=KIND_CHOICES, default='REG', verbose_name='费用类型')
    title = models.CharField(max_length=128, blank=True, default='', verbose_name='费用说明')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'), verbose_name='金额')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='UNPAID', verbose_name='状态')
    appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payments', verbose_name='关联挂号',
    )
    prescription = models.ForeignKey(
        Prescription, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payments', verbose_name='关联处方',
    )
    exam_order = models.ForeignKey(
        ExamOrder, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payments', verbose_name='关联检查单',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='支付时间')

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        verbose_name = '缴费单'
        verbose_name_plural = '缴费单'

    def __str__(self):
        return f'{self.get_kind_display()} ¥{self.amount}'


class AuditLog(models.Model):
    """系统审计日志（管理员查看）"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs', verbose_name='操作人',
    )
    username = models.CharField(max_length=150, blank=True, default='', verbose_name='操作人账号')
    role = models.CharField(max_length=20, blank=True, default='', verbose_name='操作人角色')
    action = models.CharField(max_length=64, verbose_name='操作')
    target = models.CharField(max_length=128, blank=True, default='', verbose_name='操作对象')
    detail = models.TextField(blank=True, default='', verbose_name='详情')
    ip = models.CharField(max_length=64, blank=True, default='', verbose_name='来源IP')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='时间')

    class Meta:
        db_table = 'audit_logs'
        ordering = ['-created_at']
        verbose_name = '审计日志'
        verbose_name_plural = '审计日志'

    def __str__(self):
        return f'{self.username} {self.action} {self.target}'


class FeatureToggle(models.Model):
    """业务功能开关（管理员配置）"""

    key = models.CharField(max_length=64, unique=True, verbose_name='开关标识')
    name = models.CharField(max_length=128, verbose_name='名称')
    description = models.CharField(max_length=255, blank=True, default='', verbose_name='说明')
    enabled = models.BooleanField(default=True, verbose_name='是否启用')

    class Meta:
        db_table = 'feature_toggles'
        ordering = ['id']
        verbose_name = '功能开关'
        verbose_name_plural = '功能开关'

    def __str__(self):
        return f'{self.name}({"开" if self.enabled else "关"})'


class MedicalCase(models.Model):
    """病例记录"""

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='medical_cases',
        verbose_name='患者',
    )
    title = models.CharField(max_length=128, verbose_name='标题')
    hospital = models.CharField(max_length=128, blank=True, default='', verbose_name='医院')
    visit_date = models.DateField(null=True, blank=True, verbose_name='就诊日期')
    diagnosis = models.CharField(
        max_length=128, blank=True, default='', verbose_name='诊断'
    )
    description = models.TextField(blank=True, default='', verbose_name='描述')
    attachment = models.FileField(
        upload_to='cases/%Y/%m/', null=True, blank=True, verbose_name='附件'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'medical_cases'
        ordering = ['-visit_date', '-created_at']
        verbose_name = '病例'
        verbose_name_plural = '病例'

    def __str__(self):
        return f'{self.patient} - {self.title}'
