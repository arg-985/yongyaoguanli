from django.conf import settings
from django.db import models

from apps.medications.models import Medication
from apps.plans.models import MedicationPlan, PlanReminder


class MedicationRecord(models.Model):
    STATUS_TAKEN = 'TAKEN'
    STATUS_LATE = 'LATE'
    STATUS_MISSED = 'MISSED'
    STATUS_SKIPPED = 'SKIPPED'
    STATUS_CHOICES = [
        (STATUS_TAKEN, '按时'),
        (STATUS_LATE, '迟服'),
        (STATUS_MISSED, '漏服'),
        (STATUS_SKIPPED, '跳过'),
    ]

    reminder = models.OneToOneField(
        PlanReminder,
        on_delete=models.SET_NULL,
        related_name='record',
        null=True,
        blank=True,
        verbose_name='关联提醒',
    )
    plan = models.ForeignKey(
        MedicationPlan,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='用药计划',
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='患者',
    )
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='药物',
    )
    taken_time = models.DateTimeField(verbose_name='实际服药时间')
    scheduled_time = models.DateTimeField(verbose_name='原本计划时间')
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_TAKEN,
        verbose_name='状态',
    )
    delay_minutes = models.IntegerField(default=0, verbose_name='迟服分钟数')
    notes = models.TextField(blank=True, null=True, verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'medication_records'
        ordering = ['-taken_time']
        verbose_name = '服药记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.patient} - {self.medication} - {self.get_status_display()}'
