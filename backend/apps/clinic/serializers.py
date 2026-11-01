from rest_framework import serializers

from .models import HomeCabinetItem, MedicalCase, MedicationFeedback, SymptomConsultation


class HomeCabinetItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(
        source='medication.name', read_only=True, label='药品名称'
    )
    expiry_status = serializers.CharField(read_only=True, label='有效期状态')
    days_left = serializers.IntegerField(read_only=True, label='剩余天数')

    class Meta:
        model = HomeCabinetItem
        fields = '__all__'
        read_only_fields = ('owner', 'created_at', 'updated_at')


class SymptomConsultationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.__str__', read_only=True)

    class Meta:
        model = SymptomConsultation
        fields = '__all__'
        read_only_fields = ('patient', 'created_at')


class MedicationFeedbackSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.__str__', read_only=True)

    class Meta:
        model = MedicationFeedback
        fields = '__all__'
        read_only_fields = ('patient', 'created_at')


class MedicalCaseSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.__str__', read_only=True)
    attachment_url = serializers.SerializerMethodField(label='附件完整地址')

    class Meta:
        model = MedicalCase
        fields = '__all__'
        read_only_fields = ('patient', 'created_at')

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return ''
        url = obj.attachment.url
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url
