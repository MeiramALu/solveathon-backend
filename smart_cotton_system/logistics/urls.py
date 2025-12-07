from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LogisticsMapViewSet, VehicleViewSet, optimize_routes, ai_summary

router = DefaultRouter()

# Register ViewSets
router.register(r'map-data', LogisticsMapViewSet, basename='logistics-map')
router.register(r'vehicles', VehicleViewSet, basename='vehicles')

urlpatterns = [
    path('', include(router.urls)),
    path('optimize/', optimize_routes, name='optimize-routes'),
    path('ai-summary/', ai_summary, name='ai-summary'),
]