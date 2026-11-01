from django.db import models


class Medication(models.Model):
    name = models.CharField(max_length=128, verbose_name='药品名称')
    generic_name = models.CharField(max_length=128, blank=True, null=True, verbose_name='通用名')
    specification = models.CharField(max_length=128, blank=True, default='', verbose_name='规格')
    unit = models.CharField(max_length=32, blank=True, default='', verbose_name='单位')
    category = models.CharField(max_length=64, blank=True, null=True, verbose_name='分类')
    description = models.TextField(blank=True, null=True, verbose_name='说明')
    side_effects = models.TextField(blank=True, null=True, verbose_name='不良反应')
    storage = models.CharField(max_length=255, blank=True, null=True, verbose_name='贮藏')
    ingredients = models.CharField(
        max_length=255, blank=True, default='', verbose_name='主要成分',
        help_text='多个成分用英文逗号分隔',
    )
    is_otc = models.BooleanField(default=True, verbose_name='是否非处方药')
    symptom_tags = models.JSONField(
        default=list, blank=True, verbose_name='适用症状编码'
    )
    max_daily_dose = models.CharField(
        max_length=64, blank=True, default='', verbose_name='每日最大剂量'
    )
    min_interval_hours = models.PositiveIntegerField(
        null=True, blank=True, verbose_name='最小间隔小时'
    )
    population_caution = models.TextField(
        blank=True, default='', verbose_name='特殊人群注意'
    )
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name='单价',
        help_text='元/单位，由管理员维护',
    )
    stock = models.IntegerField(default=0, verbose_name='库存',
                               help_text='仅管理员可维护库存')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'medications'
        ordering = ['-created_at']
        verbose_name = '药物'
        verbose_name_plural = '药物'

    def __str__(self):
        return self.name
