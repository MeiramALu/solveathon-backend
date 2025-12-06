from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FieldViewSet, SensorLogViewSet, SeedVarietyViewSet

router = DefaultRouter()

# Мы уже добавили basename для полей
router.register(r'fields', FieldViewSet, basename='field')

# --- ИСПРАВЛЕНИЕ: Добавляем basename='sensorlog' ---
# Это решит вашу текущую ошибку
router.register(r'sensors', SensorLogViewSet, basename='sensorlog')

# Для семян basename не нужен, так как там остался стандартный queryset
router.register(r'seeds', SeedVarietyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]