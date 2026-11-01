from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'phone', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'date_joined', 'is_active')
    search_fields = ('username', 'phone', 'email', 'real_name')
    ordering = ('-date_joined',)

    fieldsets = (
        ('基础信息', {'fields': ('username', 'password')}),
        ('个人资料', {
            'fields': (
                'phone', 'email', 'real_name', 'gender', 'birth_date',
                'address', 'emergency_contact', 'emergency_phone', 'avatar',
            ),
        }),
        ('权限', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('重要时间', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'phone', 'password1', 'password2', 'role', 'email'),
        }),
    )
