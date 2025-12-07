from rest_framework import serializers
from .models import CottonBatch, Machine, MaintenanceLog


class CottonBatchSerializer(serializers.ModelSerializer):
    # Добавляем имя фермера текстом для удобства идентификации
    farmer_name = serializers.CharField(source='farmer.username', read_only=True)

    class Meta:
        model = CottonBatch
        fields = [
            # --- Идентификация (Output ID) ---
            'id',
            'batch_code',
            'farmer',
            'farmer_name',

            # --- Результат (Target) ---
            'quality_class',
            'status',

            # --- Детальные параметры HVI ---
            'micronaire', 'strength', 'length', 'uniformity',
            'trash_grade', 'trash_cnt', 'trash_area',
            'sfi', 'sci', 'color_grade',

            # --- Файлы и даты ---
            'cotton_image', 'hvi_file', 'created_at'
        ]


# Остальные сериалайзеры
class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = '__all__'


class MaintenanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceLog
        fields = '__all__'