"""URL-маршруты для health checks (Этап 5.4)."""
from django.urls import path

from . import views_health

app_name = 'health'

urlpatterns = [
    path('', views_health.health_overall, name='overall'),
    path('db/', views_health.health_db, name='db'),
    path('ready/', views_health.health_ready, name='ready'),
    path('live/', views_health.health_live, name='live'),
]