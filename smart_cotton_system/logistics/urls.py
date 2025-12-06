from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VehicleViewSet, GPSLogViewSet

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet)
router.register(r'gps', GPSLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]