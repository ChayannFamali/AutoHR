"""Лёгкая CORS middleware без внешних зависимостей.

Включается через `CORS_ENABLED=True` в settings.py.
По умолчанию разрешает только same-origin (без CORS-заголовков).

Why: не тянуть django-cors-headers ради простой настройки.
     Для учебного проекта без внешнего фронта CORS обычно не нужен,
     но middleware подключена заранее — включить одной env-переменной.
"""
from django.conf import settings


class CORSMiddleware:
    """Добавляет CORS-заголовки если CORS_ENABLED=True.

    Читает:
      - CORS_ENABLED (bool)
      - CORS_ALLOWED_ORIGINS (list[str]) — список разрешённых origin
      - CORS_ALLOW_CREDENTIALS (bool)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'CORS_ENABLED', False)
        self.allowed_origins = set(getattr(settings, 'CORS_ALLOWED_ORIGINS', []))
        self.allow_credentials = getattr(settings, 'CORS_ALLOW_CREDENTIALS', True)

    def __call__(self, request):
        response = self.get_response(request)

        if not self.enabled:
            return response

        origin = request.META.get('HTTP_ORIGIN')
        if not origin:
            return response

        # Same-origin всегда ОК
        if origin in self.allowed_origins or '*' in self.allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
            if self.allow_credentials:
                response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Content-Type, X-CSRFToken, X-Requested-With, HX-Request, HX-Target, HX-Trigger'
            )
            response['Access-Control-Max-Age'] = '86400'

        return response

    def process_options_request(self, request):
        """Обработка preflight OPTIONS-запросов."""
        from django.http import HttpResponse
        response = HttpResponse(status=204)
        origin = request.META.get('HTTP_ORIGIN')

        if origin and (origin in self.allowed_origins or '*' in self.allowed_origins):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = (
                'Accept, Content-Type, X-CSRFToken, X-Requested-With, HX-Request, HX-Target, HX-Trigger'
            )
            if self.allow_credentials:
                response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
        return response