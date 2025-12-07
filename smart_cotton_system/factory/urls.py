from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CottonBatchViewSet, MachineViewSet, MaintenanceLogViewSet

router = DefaultRouter()
router.register(r'batches', CottonBatchViewSet)
router.register(r'machines', MachineViewSet)
router.register(r'maintenance', MaintenanceLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]