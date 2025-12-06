from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SafetyAlertViewSet

router = DefaultRouter()
router.register(r'alerts', SafetyAlertViewSet)

urlpatterns = [
    path('', include(router.urls)),
]