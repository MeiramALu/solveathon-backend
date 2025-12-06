from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Field, SensorLog, SeedVariety
from .serializers import FieldSerializer, SensorLogSerializer, SeedVarietySerializer
from users.permissions import IsFarmer  # Импортируем, если нужно проверять роль


class SeedVarietyViewSet(viewsets.ModelViewSet):
    """
    Справочник семян.
    """
    queryset = SeedVariety.objects.all()
    serializer_class = SeedVarietySerializer
    permission_classes = [IsAuthenticated]


class FieldViewSet(viewsets.ModelViewSet):
    """
    Поля. Фильтрация: Фермер видит только свои поля.
    """
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Если Фермер -> возвращаем только его поля
        if hasattr(user, 'role') and user.role == 'FARMER':
            return Field.objects.filter(owner=user)
        # Если Админ/Лаборант -> возвращаем всё
        return Field.objects.all()

    def perform_create(self, serializer):
        # При создании поля авто-владелец
        serializer.save(owner=self.request.user)


class SensorLogViewSet(viewsets.ModelViewSet):
    """
    Логи датчиков.
    Здесь тоже добавляем фильтрацию, чтобы фермер видел логи ТОЛЬКО со своих полей.
    """
    serializer_class = SensorLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Берем базовый запрос
        queryset = SensorLog.objects.all().order_by('-timestamp')

        user = self.request.user

        # Если Фермер -> фильтруем логи через поле (field__owner)
        if hasattr(user, 'role') and user.role == 'FARMER':
            return queryset.filter(field__owner=user)

        return queryset