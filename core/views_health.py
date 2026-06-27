"""Health check эндпоинты для Docker / мониторинга (Этап 5.4).

Эндпоинты:
  /health/         — общий health: БД, cache, миграции
  /health/db/      — только БД
  /health/ready/   — readiness (всё ОК для приёма трафика)
  /health/live/    — liveness (приложение живо)

Возвращают JSON: {"status": "ok"/"degraded"/"error", "checks": {...}, "version": "..."}
"""
import json
import logging
import sys

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@csrf_exempt
@require_GET
def health_overall(request):
    """Общий health: проверка БД + cache."""
    checks = {}
    overall_ok = True

    # 1) БД
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        checks['database'] = {'status': 'ok', 'vendor': connection.vendor}
    except Exception as e:
        checks['database'] = {'status': 'error', 'message': str(e)[:200]}
        overall_ok = False

    # 2) Cache
    try:
        from django.core.cache import cache
        cache_key = '_health_check_test'
        cache.set(cache_key, '1', timeout=10)
        value = cache.get(cache_key)
        if value == '1':
            checks['cache'] = {'status': 'ok'}
        else:
            checks['cache'] = {'status': 'error', 'message': 'cache write/read mismatch'}
            overall_ok = False
    except Exception as e:
        checks['cache'] = {'status': 'error', 'message': str(e)[:200]}
        overall_ok = False

    # 3) Pending migrations (если можно)
    try:
        from django.db.migrations.executor import MigrationExecutor
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if plan:
            checks['migrations'] = {
                'status': 'warning',
                'message': f'{len(plan)} pending migration(s)',
            }
        else:
            checks['migrations'] = {'status': 'ok'}
    except Exception as e:
        checks['migrations'] = {'status': 'unknown', 'message': str(e)[:100]}

    status = 'ok' if overall_ok else 'degraded'
    http_status = 200 if overall_ok else 503

    return JsonResponse({
        'status': status,
        'checks': checks,
        'version': getattr(settings, 'APP_VERSION', 'dev'),
        'python': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
        'django': settings.Django.__version__ if hasattr(settings, 'Django') else 'unknown',
    }, status=http_status)


@csrf_exempt
@require_GET
def health_db(request):
    """Только БД — для отдельного мониторинга."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            cursor.fetchone()
        return JsonResponse({
            'status': 'ok',
            'vendor': connection.vendor,
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)[:200],
        }, status=503)


@csrf_exempt
@require_GET
def health_ready(request):
    """Readiness probe — приложение готово принимать трафик."""
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return JsonResponse({'status': 'ready'})
    except Exception:
        return JsonResponse({'status': 'not_ready'}, status=503)


@csrf_exempt
@require_GET
def health_live(request):
    """Liveness probe — приложение живо (просто отвечает)."""
    return JsonResponse({'status': 'alive'})