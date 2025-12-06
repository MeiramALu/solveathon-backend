from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import CottonBatch, Machine, MaintenanceLog
from .serializers import CottonBatchSerializer, MachineSerializer, MaintenanceLogSerializer
from users.permissions import IsLabOrReadOnly

class CottonBatchViewSet(viewsets.ModelViewSet):
    """
    Управление партиями хлопка.
    - Смотреть список могут все авторизованные пользователи.
    - Создавать/Редактировать (вносить HVI данные) могут только Лаборанты (LAB).
    """
    queryset = CottonBatch.objects.all().order_by('-created_at')
    serializer_class = CottonBatchSerializer
    permission_classes = [IsAuthenticated, IsLabOrReadOnly]

    def perform_create(self, serializer):
        # При создании партии (если её создает фермер через приложение),
        # можно автоматически привязывать владельца, если нужно.
        # Пока оставляем стандартное сохранение.
        serializer.save()


class MachineViewSet(viewsets.ModelViewSet):
    """
    Станки. Управление доступно авторизованным сотрудникам завода.
    """
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    # Здесь пока просто требуем вход в систему.
    # В будущем можно создать пермишн IsFactoryManager.
    permission_classes = [IsAuthenticated]


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    """
    Журнал ремонта.
    """
    queryset = MaintenanceLog.objects.all().order_by('-timestamp')
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsAuthenticated]