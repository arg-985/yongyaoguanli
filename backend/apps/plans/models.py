from decimal import Decimal

from django.db import models
from django.conf import settings

from apps.medications.models import Medication


class MedicationPlan(models.Model):
    """用药计划"""

    class FrequencyChoices(models.TextChoices):
        DAILY = 'DAILY', '每日一次'
        BID = 'BID', '每日两次'
        TID = 'TID', '每日三次'
        QID = 'QID', '每日四次'
        ONCE_WEEKLY = 'ONCE_WEEKLY', '每周一次'
        CUSTOM = 'CUSTOM', '自定义'

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='plans',
        verbose_name='患者',
    )
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='plans',
        verbose_name='药物',
    )
    dosage_per_time = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('1.0'),
        verbose_name='每次剂量',
    )
    frequency = models.CharField(
        max_length=32,
        choices=FrequencyChoices.choices,
        verbose_name='频率',
    )
    custom_times = models.JSONField(
        blank=True,
        null=True,
        verbose_name='自定义时间点',
        help_text='如 ["08:00","20:00"]',
    )
    start_date = models.DateField(verbose_name='开始日期')
    end_date = models.DateField(blank=True, null=True, verbose_name='结束日期')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'medication_plans'
        ordering = ['-start_date']
        verbose_name = '用药计划'
        verbose_name_plural = '用药计划'

    def __str__(self):
        return f'{self.patient} - {self.medication} ({self.get_frequency_display()})'


class PlanReminder(models.Model):
    """待服提醒（APScheduler 生成）"""

    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', '待服药'
        TAKEN = 'TAKEN', '已服用'
        MISSED = 'MISSED', '已错过'
        SKIPPED = 'SKIPPED', '已跳过'

    plan = models.ForeignKey(
        MedicationPlan,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name='用药计划',
    )
    scheduled_time = models.DateTimeField(verbose_name='计划服药时间')
    status = models.CharField(
        max_length=16,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name='状态',
    )
    reminded = models.BooleanField(default=False, verbose_name='是否已提醒')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'plan_reminders'
        ordering = ['-scheduled_time']
        verbose_name = '服药提醒'
        verbose_name_plural = '服药提醒'

    def __str__(self):
        return f'{self.plan} - {self.scheduled_time:%Y-%m-%d %H:%M} ({self.status})'
