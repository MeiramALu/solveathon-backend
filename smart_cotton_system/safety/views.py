from rest_framework import viewsets
from .models import SafetyAlert
from .serializers import SafetyAlertSerializer

class SafetyAlertViewSet(viewsets.ModelViewSet):
    # Сначала показываем новые и нерешенные проблемы
    queryset = SafetyAlert.objects.all().order_by('is_resolved', '-timestamp')
    serializer_class = SafetyAlertSerializer