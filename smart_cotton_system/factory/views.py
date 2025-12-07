from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import google.generativeai as genai
from django.conf import settings

# Импорты моделей и сериализаторов
from .models import CottonBatch, Machine, MaintenanceLog
from .serializers import CottonBatchSerializer, MachineSerializer, MaintenanceLogSerializer

# Импорты всей нашей логики (AI, GeoIP, Agronomy)
from .services import (
    analyze_machine_health,
    get_seed_recommendations,
    get_agronomy_data,
    get_coords_by_ip
)


# ==========================================
# 1. VIEWSETS (API ДЛЯ ПРИЛОЖЕНИЯ)
# ==========================================

class CottonBatchViewSet(viewsets.ModelViewSet):
    queryset = CottonBatch.objects.all().order_by('-created_at')
    serializer_class = CottonBatchSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

    # --- API: Рекомендация семян (GET) ---
    @action(detail=False, methods=['get'])
    def recommend_seeds(self, request):
        """
        Возвращает топ-3 сорта для указанного региона.
        Пример: /api/factory/batches/recommend_seeds/?region=South
        """
        region = request.query_params.get('region', 'South')
        # Если передан pH почвы, используем его, иначе дефолт
        soil_ph = float(request.query_params.get('ph', 7.0))

        recommendations = get_seed_recommendations(region, soil_ph)
        return Response(recommendations)

    # --- API: Чат-бот Gemini (POST) ---
    @action(detail=False, methods=['post'])
    def ai_assistant(self, request):
        """
        Умный AI-консультант на базе Google Gemini.
        """
        user_msg = request.data.get('message', '')

        if not user_msg:
            return Response({"bot_answer": "Пожалуйста, напишите вопрос."})

        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            # Используем 1.5-flash (самая быстрая и стабильная на сегодня)
            model = genai.GenerativeModel('gemini-1.5-flash')

            system_prompt = (
                "Ты — умный ассистент платформы 'Smart Cotton System'. "
                "Твоя цель — помогать фермерам и технологам завода. "
                "Ты эксперт в агрономии хлопка, ценах на биржах, погоде и вредителях. "
                "Отвечай кратко, профессионально, но дружелюбно. "
                "Если спрашивают о системе, говори, что мы используем компьютерное зрение и IoT датчики. "
                "Вопрос пользователя: "
            )

            response = model.generate_content(system_prompt + user_msg)
            answer = response.text

        except Exception as e:
            print(f"❌ Ошибка Gemini: {e}")
            answer = "Извините, сейчас связь с нейросетью недоступна. Попробуйте позже."

        return Response({"bot_answer": answer})


class MachineViewSet(viewsets.ModelViewSet):
    queryset = Machine.objects.all()
    serializer_class = MachineSerializer
    permission_classes = [IsAuthenticated]

    # --- API: Данные для Графиков (GET) ---
    @action(detail=True, methods=['get'])
    def chart_data(self, request, pk=None):
        """
        Возвращает историю температуры и вибрации для построения графиков.
        URL: /api/factory/machines/{id}/chart_data/
        """
        machine = self.get_object()
        # Берем последние 30 записей
        logs = MaintenanceLog.objects.filter(machine=machine).order_by('-timestamp')[:30]
        # Разворачиваем (чтобы график шел слева направо по времени)
        logs = reversed(logs)

        data = {
            "timestamps": [],
            "temperature": [],
            "vibration": []
        }

        for log in logs:
            data["timestamps"].append(log.timestamp.strftime("%H:%M:%S"))
            data["temperature"].append(getattr(log, 'temperature', 0))
            data["vibration"].append(getattr(log, 'vibration', 0))

        return Response(data)

    # --- API: Прием данных с датчиков (POST) ---
    @action(detail=False, methods=['post'])
    def telemetry(self, request):
        """
        Принимает данные симуляции или реальных датчиков.
        """
        data = request.data
        machine_id = data.get('machine_id')

        try:
            machine, _ = Machine.objects.get_or_create(name=machine_id)

            temp = float(data.get('temperature', 0))
            vib = float(data.get('vibration', 0))
            load = float(data.get('motor_load', 0))
            hum = float(data.get('humidity', 0))

            machine.last_temp = temp
            machine.last_vibration = vib
            machine.last_motor_load = load
            machine.last_humidity = hum

            # AI Анализ риска
            risk, desc = analyze_machine_health(machine, temp, vib, load)

            if risk > 30:
                machine.status = 'WARNING' if risk < 70 else 'CRITICAL'
            else:
                machine.status = 'OK'

            machine.save()

            # Пишем лог ВСЕГДА (для истории графиков)
            MaintenanceLog.objects.create(
                machine=machine,
                description=desc,
                is_prediction=(risk > 0),
                probability_failure=risk,
                temperature=temp,
                vibration=vib
            )

            return Response({"status": "updated", "risk": risk, "msg": desc})

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MaintenanceLogViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceLog.objects.all().order_by('-timestamp')
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsAuthenticated]


# ==========================================
# 2. STANDALONE VIEWS (ДЛЯ ДАШБОРДА И КАРТЫ)
# ==========================================

def dashboard_view(request):
    """
    Отдает HTML страницу с картой.
    """
    return render(request, 'dashboard.html')


def api_agronomy_predict(request):
    """
    API для карты: принимает Lat/Lon (или определяет по IP) и отдает прогноз.
    """
    # 1. Пробуем взять координаты из клика по карте
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    # 2. Если координат нет (автозагрузка страницы) - определяем по IP
    if not lat or not lon:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Функция из services.py (GeoIP)
        lat, lon, region_name = get_coords_by_ip(ip)

    # 3. Получаем агрономический прогноз
    data = get_agronomy_data(lat, lon)

    return JsonResponse(data)