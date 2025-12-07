from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FieldViewSet, SensorLogViewSet, SeedVarietyViewSet
from . import views

router = DefaultRouter()

# Мы уже добавили basename для полей
router.register(r'fields', FieldViewSet, basename='field')

# --- ИСПРАВЛЕНИЕ: Добавляем basename='sensorlog' ---
# Это решит вашу текущую ошибку
router.register(r'sensors', SensorLogViewSet, basename='sensorlog')

# Для семян basename не нужен, так как там остался стандартный queryset
router.register(r'seeds', SeedVarietyViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('irrigation/predict/', views.predict_irrigation, name='predict-irrigation'),
    path('irrigation/simulate/', views.simulate_future_irrigation, name='simulate-irrigation'),
    path('irrigation/field/<int:field_id>/map/', views.field_irrigation_map, name='field-irrigation-map'),
    path('irrigation/field/<int:field_id>/summary/', views.field_summary, name='field-summary'),
    path('irrigation/timeseries/', views.field_timeseries, name='field-timeseries'),
    path('irrigation/bulk-predict/', views.bulk_generate_predictions, name='bulk-predictions'),
    
    # New comprehensive endpoints matching Flask app
    path('irrigation/field/<int:field_id>/dates/', views.get_available_dates, name='available-dates'),
    path('irrigation/field/<int:field_id>/map-data/', views.get_map_data, name='map-data'),
    path('irrigation/field/<int:field_id>/date-summary/', views.get_date_summary, name='date-summary'),
    path('irrigation/field/<int:field_id>/location-timeseries/', views.get_location_timeseries, name='location-timeseries'),
]