from django.contrib import admin

from apps.clinic.models import (
    HomeCabinetItem,
    MedicalCase,
    MedicationFeedback,
    SymptomConsultation,
)


@admin.register(HomeCabinetItem)
class HomeCabinetItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'owner', 'medication', 'quantity', 'unit',
        'expiry_date', 'expiry_status', 'location', 'created_at',
    )
    list_filter = ('owner', 'medication', 'expiry_date')
    search_fields = ('name', 'owner__username', 'medication__name', 'location')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SymptomConsultation)
class SymptomConsultationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'symptoms', 'duration_days', 'severity',
        'source', 'created_at',
    )
    list_filter = ('source', 'severity', 'created_at')
    search_fields = ('patient__username', 'free_text', 'advice')
    readonly_fields = ('created_at',)


@admin.register(MedicationFeedback)
class MedicationFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'medication_name', 'kind',
        'severity', 'efficacy_score', 'created_at',
    )
    list_filter = ('kind', 'patient', 'medication', 'created_at')
    search_fields = ('patient__username', 'medication_name', 'description')
    readonly_fields = ('created_at',)


@admin.register(MedicalCase)
class MedicalCaseAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'patient', 'title', 'hospital', 'visit_date',
        'diagnosis', 'attachment', 'created_at',
    )
    list_filter = ('visit_date', 'hospital', 'patient')
    search_fields = ('patient__username', 'title', 'hospital', 'diagnosis')
    readonly_fields = ('created_at',)
