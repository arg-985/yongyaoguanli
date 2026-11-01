from django.conf import settings
from django.db import models


class FamilyBinding(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='family_bindings',
        limit_choices_to={'role': 'patient'},
        verbose_name='患者',
    )
    family_member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_bindings',
        limit_choices_to={'role': 'family'},
        verbose_name='家属',
    )
    relation = models.CharField(
        max_length=32,
        verbose_name='关系',
        help_text='如：父亲 / 母亲 / 配偶 / 子女',
    )
    is_authorized = models.BooleanField(
        default=True,
        verbose_name='是否授权查看服药数据',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
    )

    class Meta:
        db_table = 'family_bindings'
        unique_together = [('patient', 'family_member')]
        ordering = ['-created_at']
        verbose_name = '家属绑定'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.patient} ↔ {self.family_member} ({self.relation})'
