from django.contrib import admin
from .models import MarketPrice

@admin.register(MarketPrice)
class MarketPriceAdmin(admin.ModelAdmin):
    list_display = ('commodity', 'price', 'date', 'is_forecast', 'confidence_score')
    list_filter = ('commodity', 'is_forecast')
    ordering = ('-date',)