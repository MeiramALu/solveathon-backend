from django.urls import path
from .views import MarketDataView, ExportOptimizationView

urlpatterns = [
    path('', MarketDataView.as_view(), name='market-data'),
    path('optimize/', ExportOptimizationView.as_view(), name='export-optimize'),
]