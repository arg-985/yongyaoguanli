from django.contrib import admin

from apps.medications.models import Medication


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'generic_name', 'specification', 'unit', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'generic_name', 'category')
