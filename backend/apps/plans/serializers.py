from rest_framework import serializers

from .models import MedicationPlan, PlanReminder


class MedicationPlanSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.__str__', read_only=True)
    medication_name = serializers.CharField(source='medication.name', read_only=True)

    class Meta:
        model = MedicationPlan
        fields = '__all__'


class PlanReminderSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='plan.medication.name', read_only=True)
    patient_id_real = serializers.IntegerField(source='plan.patient_id', read_only=True)

    class Meta:
        model = PlanReminder
        fields = '__all__'
