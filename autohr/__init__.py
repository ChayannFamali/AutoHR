"""
Инициализация Celery-приложения для Django.

Это гарантирует, что `app` (Celery) создаётся при старте Django и
общий декоратор `@shared_task` использует именно его.
"""
from .celery import app as celery_app

__all__ = ('celery_app',)