from django.contrib import admin

from apps.records.models import MedicationRecord


@admin.register(MedicationRecord)
class MedicationRecordAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'medication', 'status',
        'scheduled_time', 'taken_time', 'delay_minutes', 'created_at',
    )
    list_filter = ('status', 'patient', 'medication', 'created_at')
    search_fields = ('patient__username', 'medication__name', 'notes')
    readonly_fields = ('created_at',)
    date_hierarchy = 'scheduled_time'
