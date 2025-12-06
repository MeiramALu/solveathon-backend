from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Field, SensorLog, SeedVariety
from .serializers import FieldSerializer, SensorLogSerializer, SeedVarietySerializer
from users.permissions import IsFarmer


class SeedVarietyViewSet(viewsets.ModelViewSet):
    """
    Справочник семян. Обычно фермеры его только читают.
    """
    queryset = SeedVariety.objects.all()
    serializer_class = SeedVarietySerializer
    permission_classes = [IsAuthenticated]


class FieldViewSet(viewsets.ModelViewSet):
    """
    Поля. Здесь главная логика разделения.
    """
    serializer_class = FieldSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Магия разделения данных:
        1. Получаем текущего пользователя (request.user).
        2. Если он Фермер -> возвращаем только поля, где owner = он сам.
        3. Если он Админ или Лаборант -> возвращаем всё.
        """
        user = self.request.user

        # Проверяем роль (если у пользователя есть атрибут role)
        if hasattr(user, 'role') and user.role == 'FARMER':
            return Field.objects.filter(owner=user)

        # Для всех остальных (админов, менеджеров) показываем всё
        return Field.objects.all()

    def perform_create(self, serializer):
        """
        При создании поля автоматически прописываем владельца.
        Фермеру не нужно выбирать себя из списка, система сама подставит его ID.
        """
        serializer.save(owner=self.request.user)


class SensorLogViewSet(viewsets.ModelViewSet):
    """
    Логи датчиков.
    """
    queryset = SensorLog.objects.all().order_by('-timestamp')
    serializer_class = SensorLogSerializer
    permission_classes = [IsAuthenticated]