from django.contrib import admin

from apps.family.models import FamilyBinding


@admin.register(FamilyBinding)
class FamilyBindingAdmin(admin.ModelAdmin):
    list_display = ('patient', 'family_member', 'relation', 'is_authorized', 'created_at')
    list_filter = ('is_authorized', 'relation', 'created_at')
    search_fields = (
        'patient__username',
        'patient__first_name',
        'patient__last_name',
        'family_member__username',
        'family_member__first_name',
        'family_member__last_name',
    )
    readonly_fields = ('created_at',)
