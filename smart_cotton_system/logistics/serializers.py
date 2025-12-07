from rest_framework import serializers
from .models import Vehicle, Route, GPSLog, Field, Depot, OptimizationJob

class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ['id', 'plate_number', 'status', 'marker_color', 'capacity', 'shift_minutes']


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        fields = ['id', 'name', 'latitude', 'longitude', 'demand', 'service_time_minutes', 'is_active']


class DepotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Depot
        fields = ['id', 'name', 'latitude', 'longitude', 'is_default']


class OptimizationJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptimizationJob
        fields = ['id', 'depot', 'created_at', 'request_data', 'ors_solution', 'ai_summary', 'status', 'error_message']
        read_only_fields = ['created_at']

class RouteMapSerializer(serializers.ModelSerializer):
    """
    Специальный сериалайзер для карты. 
    Возвращает чистый массив координат для Polyline Leaflet'а.
    """
    vehicle_info = VehicleSerializer(source='vehicle', read_only=True)
    coordinates = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = ['id', 'vehicle_info', 'coordinates', 'estimated_time']

    def get_coordinates(self, obj):
        # Извлекаем координаты из GeoJSON. 
        # Предполагаем структуру: {"coordinates": [[lat, lon], ...]}
        # Внимание: Leaflet ждет [lat, lon], а GeoJSON часто хранит [lon, lat].
        # Здесь нужно убедиться в порядке. Допустим, у нас уже правильный [lat, lon].
        data = obj.path_geojson
        if isinstance(data, dict) and 'coordinates' in data:
            return data['coordinates']
        return []