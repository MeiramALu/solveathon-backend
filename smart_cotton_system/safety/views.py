from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SafetyAlert
from .serializers import SafetyAlertSerializer


class SafetyAlertViewSet(viewsets.ModelViewSet):
    queryset = SafetyAlert.objects.all().order_by('-timestamp')
    serializer_class = SafetyAlertSerializer

    @action(detail=False, methods=['post'])
    def webhook(self, request):
        """
        Принимает JSON от AI-камеры.
        Ожидаемый формат:
        {
            "location": "Camera_1",
            "predictions": [
                { "class": "Fire-Smoke", "confidence": 0.558, "x": 92, "y": 74, "width": 124, "height": 148 }
            ]
        }
        """
        data = request.data
        location = data.get('location', 'Unknown Camera')
        predictions = data.get('predictions', [])

        alerts_created = []

        for pred in predictions:
            # 1. Фильтр по уверенности (если AI не уверен, не сохраняем)
            conf = pred.get('confidence', 0)
            if conf < 0.4:
                continue

            # 2. Маппинг классов (JSON -> Django Model)
            raw_class = pred.get('class', '')
            alert_type = 'DANGER_ZONE'  # Значение по умолчанию

            if 'Fire' in raw_class or 'Smoke' in raw_class:
                alert_type = 'FIRE'
            elif 'Helmet' in raw_class:
                alert_type = 'NO_HELMET'

            # 3. Создаем запись в БД
            alert = SafetyAlert.objects.create(
                alert_type=alert_type,
                location=location,
                confidence=conf,
                # Сохраняем x, y, w, h прямо в JSON поле, чтобы потом нарисовать квадратик
                detection_details={
                    "x": pred.get('x'),
                    "y": pred.get('y'),
                    "w": pred.get('width'),
                    "h": pred.get('height')
                }
            )
            alerts_created.append(alert.id)

        return Response({
            "status": "processed",
            "alerts_created": len(alerts_created)
        }, status=status.HTTP_201_CREATED)