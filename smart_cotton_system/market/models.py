from django.db import models

class MarketPrice(models.Model):
    """Исторические данные и прогнозы цен"""
    commodity = models.CharField(max_length=50, default="Cotton") # Cotton, USD/KZT
    price = models.FloatField()
    date = models.DateField()
    is_forecast = models.BooleanField(default=False, verbose_name="Это прогноз AI?")
    confidence_score = models.FloatField(null=True, verbose_name="Уверенность AI %")

    class Meta:
        ordering = ['-date']