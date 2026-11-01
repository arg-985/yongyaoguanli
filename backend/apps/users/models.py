from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class User(AbstractUser):
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
    ]
    ROLE_CHOICES = [
        ('patient', '患者'),
        ('doctor', '医生'),
        ('admin', '管理员'),
    ]

    username = models.CharField(max_length=150, unique=True, verbose_name='用户名')
    phone = models.CharField(max_length=20, unique=True, verbose_name='手机号')
    email = models.EmailField(max_length=255, blank=True, default='', verbose_name='邮箱')
    real_name = models.CharField(max_length=50, blank=True, default='', verbose_name='真实姓名')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, default='', verbose_name='性别')
    birth_date = models.DateField(null=True, blank=True, verbose_name='出生日期')
    address = models.CharField(max_length=255, blank=True, default='', verbose_name='地址')
    emergency_contact = models.CharField(max_length=50, blank=True, default='', verbose_name='紧急联系人')
    emergency_phone = models.CharField(max_length=20, blank=True, default='', verbose_name='紧急联系电话')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient', verbose_name='角色')
    department = models.CharField(max_length=64, blank=True, default='', verbose_name='所属科室')
    title = models.CharField(max_length=64, blank=True, default='', verbose_name='职称')
    allergies = models.CharField(max_length=255, blank=True, default='', verbose_name='过敏史')
    avatar = models.URLField(null=True, blank=True, verbose_name='头像URL')
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='注册时间')

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username
