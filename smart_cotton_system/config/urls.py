from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings  # Важно для медиа-файлов (фото)
from django.conf.urls.static import static

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=True)),
    path('admin/', admin.site.urls),

    # Все модули системы
    path('api/factory/', include('factory.urls')),
    path('api/agronomy/', include('agronomy.urls')),
    path('api/logistics/', include('logistics.urls')),
    path('api/market/', include('market.urls')),  # <-- Добавили
    path('api/safety/', include('safety.urls')),  # <-- Добавили
]

# Это нужно, чтобы открывались фото хлопка и скриншоты с камер безопасности
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)