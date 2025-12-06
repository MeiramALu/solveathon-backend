from rest_framework import serializers
from .models import Field, SensorLog, SeedVariety

class SeedVarietySerializer(serializers.ModelSerializer):
    class Meta:
        model = SeedVariety
        fields = '__all__'

class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = '__all__'

class SensorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorLog
        fields = '__all__'