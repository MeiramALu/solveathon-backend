from rest_framework import serializers
from .models import SafetyAlert

class SafetyAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyAlert
        fields = '__all__'