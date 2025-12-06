from django.contrib import admin
from .models import SafetyAlert


@admin.register(SafetyAlert)
class SafetyAlertAdmin(admin.ModelAdmin):
    list_display = ('alert_type', 'location', 'timestamp', 'is_resolved', 'confidence')
    list_filter = ('alert_type', 'is_resolved')

    readonly_fields = ('confidence', 'detection_details', 'timestamp')