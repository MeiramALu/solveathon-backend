from rest_framework import serializers
from .models import CottonBatch, Machine, MaintenanceLog

class CottonBatchSerializer(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='farmer.username', read_only=True)

    class Meta:
        model = CottonBatch
        fields = '__all__' # Автоматически подхватит все новые поля (cotton_image, hvi_file и т.д.)

class MachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = '__all__'

class MaintenanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MaintenanceLog
        fields = '__all__'