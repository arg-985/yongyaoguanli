from rest_framework import serializers

from apps.records.models import MedicationRecord


class MedicationRecordSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(
        source='medication.name', read_only=True, label='药品名称'
    )

    class Meta:
        model = MedicationRecord
        fields = '__all__'
