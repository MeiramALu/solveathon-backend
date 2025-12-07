from django.urls import path
from .views import AIRecommendationView, ForecastView

urlpatterns = [
    path('ai-recommendations/', AIRecommendationView.as_view(), name='ai-recommendations'),
    path('forecast/', ForecastView.as_view(), name='forecast'),
]
