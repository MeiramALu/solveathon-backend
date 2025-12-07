from rest_framework import serializers
from .models import SafetyAlert, Worker, WorkerHealthMetrics, Zone


class WorkerSerializer(serializers.ModelSerializer):
    """Serializer for Worker model with current state"""
    class Meta:
        model = Worker
        fields = [
            'id', 'worker_id', 'name', 'role',
            'latitude', 'longitude', 'altitude',
            'heart_rate', 'steps', 'activity_level',
            'temp_c', 'spo2', 'noise_level', 'hrv', 'sleep_score',
            'last_updated'
        ]


class WorkerHealthMetricsSerializer(serializers.ModelSerializer):
    """Serializer for health metrics time-series data"""
    worker_name = serializers.CharField(source='worker.name', read_only=True)
    
    class Meta:
        model = WorkerHealthMetrics
        fields = [
            'id', 'worker', 'worker_name', 'timestamp',
            'heart_rate', 'spo2', 'temp_c', 'hrv', 'steps',
            'activity_level', 'noise_level',
            'latitude', 'longitude', 'altitude',
            'alert_panic', 'alert_fall', 'alert_fatigue',
            'alert_environment', 'alert_acoustic', 'alert_geofence',
            'safety_status', 'zone'
        ]


class WorkerWithAnalysisSerializer(serializers.Serializer):
    """Combined worker data with safety analysis"""
    worker_id = serializers.IntegerField()
    name = serializers.CharField()
    role = serializers.CharField()
    
    # Location
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    altitude = serializers.FloatField()
    
    # Vitals
    heart_rate = serializers.FloatField()
    steps = serializers.IntegerField()
    activity_level = serializers.IntegerField()
    temp_c = serializers.FloatField()
    spo2 = serializers.IntegerField()
    noise_level = serializers.FloatField()
    hrv = serializers.FloatField()
    sleep_score = serializers.IntegerField()
    
    # Analysis results
    zone = serializers.CharField()
    safety_status = serializers.CharField()
    alert_panic = serializers.BooleanField()
    alert_fall = serializers.BooleanField()
    alert_fatigue = serializers.BooleanField()
    alert_environment = serializers.BooleanField()
    alert_acoustic = serializers.BooleanField()
    alert_geofence = serializers.BooleanField()


class ZoneSerializer(serializers.ModelSerializer):
    """Serializer for Zone model"""
    class Meta:
        model = Zone
        fields = '__all__'


class SafetyAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyAlert
        fields = '__all__'