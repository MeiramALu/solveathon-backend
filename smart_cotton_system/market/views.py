from rest_framework import viewsets
from .models import MarketPrice
from .serializers import MarketPriceSerializer

class MarketPriceViewSet(viewsets.ModelViewSet):
    # Сортируем: сначала свежие, и сначала прогнозы
    queryset = MarketPrice.objects.all().order_by('-date', '-is_forecast')
    serializer_class = MarketPriceSerializer