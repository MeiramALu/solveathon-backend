from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MarketPriceViewSet

router = DefaultRouter()
router.register(r'prices', MarketPriceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]