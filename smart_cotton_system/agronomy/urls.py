from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FieldViewSet, SensorLogViewSet, SeedVarietyViewSet

router = DefaultRouter()

# --- ВНИМАНИЕ: Добавляем basename='field' ---
# Это обязательно, потому что в FieldViewSet мы используем get_queryset() вместо queryset
router.register(r'fields', FieldViewSet, basename='field')

router.register(r'sensors', SensorLogViewSet)
router.register(r'seeds', SeedVarietyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]