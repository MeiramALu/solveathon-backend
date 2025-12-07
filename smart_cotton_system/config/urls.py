from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# --- ВАЖНО: Импортируем наши новые views для Дашборда ---
from factory.views import dashboard_view, api_agronomy_predict

schema_view = get_schema_view(
    openapi.Info(title="Smart Cotton API", default_version='v1'),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
                  path('admin/', admin.site.urls),

                  # API приложений
                  path('api/factory/', include('factory.urls')),
                  path('api/agronomy/', include('agronomy.urls')),
                  path('api/logistics/', include('logistics.urls')),
                  path('api/market/', include('market.urls')),
                  path('api/safety/', include('safety.urls')),

                  # Авторизация (Djoser)
                  path('auth/', include('djoser.urls')),
                  path('auth/', include('djoser.urls.authtoken')),

                  # Swagger (Документация)
                  path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),

                  # --- НОВЫЕ ССЫЛКИ ДЛЯ КАРТЫ И ДАШБОРДА ---
                  path('dashboard/', dashboard_view, name='agronomy_dashboard'),  # Сама страница с картой
                  path('api/agronomy_predict/', api_agronomy_predict, name='api_agro'),
                  # API для JS (получение погоды/семян)

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)