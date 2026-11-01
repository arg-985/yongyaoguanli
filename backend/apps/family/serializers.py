from rest_framework import serializers

from apps.family.models import FamilyBinding


class FamilyBindingSerializer(serializers.ModelSerializer):
    patient_username = serializers.CharField(source='patient.username', read_only=True)
    family_username = serializers.CharField(source='family_member.username', read_only=True)

    class Meta:
        model = FamilyBinding
        fields = [
            'id', 'patient', 'family_member',
            'patient_username', 'family_username',
            'relation', 'is_authorized', 'created_at',
        ]
        read_only_fields = ['patient', 'family_member', 'is_authorized']
