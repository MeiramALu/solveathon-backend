from rest_framework import serializers


class AIRecommendationSerializer(serializers.Serializer):
    """Serializer for AI recommendation response"""
    success = serializers.BooleanField()
    decision = serializers.ChoiceField(choices=['sell', 'wait'])
    confidence = serializers.CharField()
    reason = serializers.CharField()
    forecast = serializers.ListField(child=serializers.FloatField())
    current_price = serializers.FloatField()
    predicted_peak = serializers.FloatField()
    peak_day = serializers.IntegerField()
    change_percent = serializers.FloatField()


class ForecastSerializer(serializers.Serializer):
    """Serializer for forecast response"""
    success = serializers.BooleanField()
    forecast = serializers.ListField(child=serializers.FloatField())
    days = serializers.IntegerField()
