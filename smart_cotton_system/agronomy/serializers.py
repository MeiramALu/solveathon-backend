from rest_framework import serializers
from .models import Field, SensorLog, SeedVariety, IrrigationPrediction, SensorReading, IrrigationEvent

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

class SensorReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = '__all__'

class IrrigationPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IrrigationPrediction
        fields = [
            'id',
            'field',
            'date',
            'location_x',
            'location_y',
            'predicted_humidity',
            'current_humidity',
            'dry_risk',
            'risk_level',
            'irrigation_action',
            'recommended_irrigation',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class IrrigationEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = IrrigationEvent
        fields = [
            'id',
            'field',
            'date',
            'location_x',
            'location_y',
            'irrigation_amount',
            'method',
            'notes',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
