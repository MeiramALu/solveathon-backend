from rest_framework import viewsets, status
from rest_framework.decorators import action  # <-- Этого не хватало
from rest_framework.response import Response  # <-- Этого не хватало
from rest_framework.permissions import IsAuthenticated

from .models import CottonBatch, Machine, MaintenanceLog
from .serializers import CottonBatchSerializer, MachineSerializer, MaintenanceLogSerializer
from users.permissions import IsLabOrReadOnly
from .services import analyze_machine_health

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
        serializer.save()


class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def telemetry(self, request):
        """
        Принимает данные датчиков (как в Excel).
        Пример: {"machine_id": "GIN-01", "temperature": 63.8, "vibration": 0.22, "motor_load": 52, "humidity": 17.84}
        """
        data = request.data
        machine_id = data.get('machine_id')

        try:
            # Ищем станок по имени, или создаем новый если нет
            machine, _ = Machine.objects.get_or_create(name=machine_id)

            # 1. Обновляем показатели (используем float для защиты от ошибок)
            temp = float(data.get('temperature', 0))
            vib = float(data.get('vibration', 0))
            load = float(data.get('motor_load', 0))
            hum = float(data.get('humidity', 0))

            machine.last_temp = temp
            machine.last_vibration = vib
            machine.last_motor_load = load
            machine.last_humidity = hum

            # 2. Запускаем AI анализ (функция из services.py)
            risk, desc = analyze_machine_health(machine, temp, vib, load)

            # Если риск высокий - меняем статус и создаем лог
            if risk > 30:
                machine.status = 'WARNING' if risk < 70 else 'CRITICAL'
                # Создаем запись о предсказании поломки
                MaintenanceLog.objects.create(
                    machine=machine,
                    description=desc,
                    is_prediction=True,
                    probability_failure=risk
                )
            else:
                machine.status = 'OK'

            machine.save()

            return Response({"status": "updated", "risk": risk, "msg": desc})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceLog.objects.all().order_by('-timestamp')
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsAuthenticated]