from rest_framework import serializers
from .models import Vehicle, GPSLog, Route

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = '__all__'

class GPSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSLog
        fields = '__all__'

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'