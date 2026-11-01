from django.contrib import admin

from .models import MedicationPlan, PlanReminder


@admin.register(MedicationPlan)
class MedicationPlanAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medication', 'frequency', 'dosage_per_time', 'start_date', 'end_date', 'is_active')
    list_filter = ('frequency', 'is_active', 'start_date')
    search_fields = ('patient__username', 'medication__name', 'notes')
    autocomplete_fields = ('patient', 'medication')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PlanReminder)
class PlanReminderAdmin(admin.ModelAdmin):
    list_display = ('plan', 'scheduled_time', 'status', 'reminded')
    list_filter = ('status', 'reminded', 'scheduled_time')
    search_fields = ('plan__patient__username', 'plan__medication__name')
    readonly_fields = ('created_at',)
