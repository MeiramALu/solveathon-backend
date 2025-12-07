from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SafetyAlertViewSet, WorkerViewSet, WorkerHealthMetricsViewSet, ZoneViewSet

router = DefaultRouter()
router.register(r'alerts', SafetyAlertViewSet)
router.register(r'workers', WorkerViewSet)
router.register(r'health-metrics', WorkerHealthMetricsViewSet)
router.register(r'zones', ZoneViewSet)

urlpatterns = [
    path('', include(router.urls)),
]