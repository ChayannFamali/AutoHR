"""Простой rate-limiter на Django cache.

Использование:
    from core.ratelimit import rate_limit

    @rate_limit(key='login', limit=5, period=60)
    def login_view(request):
        ...

    # или как декоратор метода:
    @rate_limit(key='apply', limit=10, period=3600)
    def apply_for_job(request, job_id):
        ...

Хранилище: Django cache framework. Если cache не настроен (LocMemCache по умолчанию),
работает в рамках одного процесса — для dev достаточно. Для prod нужно Redis.

Why: легковесная альтернатива django-ratelimit (без внешних зависимостей).
"""
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse


def _get_client_key(request, prefix):
    """Ключ для неавторизованного пользователя — IP, для авторизованного — user_id."""
    user = getattr(request, 'user', None)
    if user is not None and getattr(user, 'is_authenticated', False):
        return f"rl:{prefix}:user:{user.id}"
    # X-Forwarded-For учитываем (для reverse-proxy в prod)
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', 'unknown')
    return f"rl:{prefix}:ip:{ip}"


def rate_limit(key=None, limit=10, period=60):
    """Декоратор: разрешает не более `limit` вызовов за `period` секунд.

    Поддерживает как function-based view, так и class-based view (CBV).
    Для CBV декоратор надо применять к методам, например:
        @rate_limit(key='login', limit=10, period=60)
        def post(self, request, *args, **kwargs):
            return super().post(request, *args, **kwargs)

    Args:
        key: имя действия (используется в ключе кэша). Если None — берётся имя функции.
        limit: максимум вызовов за период (default 10).
        period: окно в секундах (default 60).
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            cache_key = _get_client_key(request, key or view_func.__name__)
            current = cache.get(cache_key, 0)

            if current >= limit:
                # Возвращаем дружелюбную HTML-страницу (не голый 429)
                if request.headers.get('HX-Request'):
                    return HttpResponse(
                        '<div class="alert alert-warning alert-dismissible fade show" role="alert">'
                        f'<i class="fas fa-exclamation-triangle me-2"></i>'
                        f'Слишком много запросов. Подождите немного (лимит: {limit} в {period} сек).'
                        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
                        '</div>',
                        status=429,
                    )
                return HttpResponse(
                    f'<html><body style="font-family:sans-serif;text-align:center;padding:60px;">'
                    f'<h1>429 — Слишком много запросов</h1>'
                    f'<p>Лимит: {limit} запросов в {period} секунд. Подождите немного.</p>'
                    f'</body></html>',
                    status=429,
                )

            cache.set(cache_key, current + 1, timeout=period)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def rate_limit_class(key=None, limit=10, period=60):
    """Декоратор для class-based view: применяет rate_limit к dispatch.

    Использование:
        @rate_limit_class(key='register', limit=5, period=300)
        class MyRegistrationView(CreateView):
            ...
    """
    def decorator(cls):
        # Получаем оригинальный dispatch
        original_dispatch = cls.dispatch

        def new_dispatch(self, request, *args, **kwargs):
            cache_key = _get_client_key(request, f'{key or cls.__name__}:{request.method}')
            current = cache.get(cache_key, 0)

            if current >= limit:
                # Только для POST/PUT/PATCH/DELETE (не для GET)
                if request.method != 'GET':
                    if request.headers.get('HX-Request'):
                        return HttpResponse(
                            '<div class="alert alert-warning alert-dismissible fade show" role="alert">'
                            f'<i class="fas fa-exclamation-triangle me-2"></i>'
                            f'Слишком много запросов. Подождите немного.'
                            '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
                            '</div>',
                            status=429,
                        )
                    return HttpResponse(
                        f'<html><body style="font-family:sans-serif;text-align:center;padding:60px;">'
                        f'<h1>429 — Слишком много запросов</h1>'
                        f'<p>Лимит: {limit} запросов в {period} секунд. Подождите немного.</p>'
                        f'</body></html>',
                        status=429,
                    )

            cache.set(cache_key, current + 1, timeout=period)
            return original_dispatch(self, request, *args, **kwargs)

        cls.dispatch = new_dispatch
        return cls
    return decorator