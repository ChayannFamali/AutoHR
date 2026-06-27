"""
Celery application для AutoHR.

Брокер и backend берутся из переменных окружения (см. settings.py):
- CELERY_BROKER_URL (по умолчанию redis://localhost:6379/0)
- CELERY_RESULT_BACKEND (по умолчанию redis://localhost:6379/1)

Запуск воркера:
    celery -A autohr worker -l info

Запуск beat-планировщика (cron-подобные задачи):
    celery -A autohr beat -l info
"""
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autohr.settings')

app = Celery('autohr')

# Загружаем настройки Celery из settings.py с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Авто-обнаружение tasks.py во всех приложениях из INSTALLED_APPS
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Диагностическая задача для проверки, что Celery подключён."""
    print(f'Request: {self.request!r}')