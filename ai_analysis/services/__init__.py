"""
Фабрика AI-движка.

Идея: всё ядро (вьюхи, Celery-задачи, management-команды) зовёт только
`get_analysis_engine()` и не знает, реальный это движок или Null-объект.

Контракт:
- `get_analysis_engine()` -> экземпляр с `enabled: bool`
  и методами `analyze_resume(resume_id)` и `match_candidate_with_job(resume_id, job_id)`.
- При `AI_ENABLED=False` ИЛИ при отсутствии тяжёлых зависимостей
  возвращается `NullAnalysisEngine` (no-op, статус помечается как обработанный).

См. docs/AIisOptional.md.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class NullAnalysisEngine:
    """Заглушка: тот же интерфейс, что и AnalysisEngine, но без вычислений."""

    enabled = False

    def analyze_resume(self, resume_id: int):
        """Помечает резюме как обработанное без AI-данных."""
        from resume.models import Resume
        try:
            resume = Resume.objects.get(id=resume_id)
            if resume.status != 'processed':
                resume.status = 'processed'
                resume.save(update_fields=['status'])
        except Resume.DoesNotExist:
            pass
        return {
            'success': True,
            'resume_id': resume_id,
            'ai_enabled': False,
        }

    def match_candidate_with_job(self, resume_id: int, job_id: int):
        """Без скора — пусть HR оценивает руками."""
        return {
            'success': True,
            'ai_enabled': False,
            'overall_score': None,
            'recommendation': None,
        }


def get_analysis_engine():
    """
    Возвращает реальный AnalysisEngine или NullAnalysisEngine.

    Решения:
    1. settings.AI_ENABLED == False -> сразу NullAnalysisEngine (дешёвая ветка).
    2. Если AI включён, но тяжёлые зависимости недоступны -> NullAnalysisEngine
       с предупреждением в логе (graceful degradation).
    3. Иначе -> реальный AnalysisEngine (лениво импортируется здесь, чтобы
       веб-процесс не тянул sentence_transformers при AI_ENABLED=False).
    """
    if not getattr(settings, 'AI_ENABLED', False):
        return NullAnalysisEngine()

    try:
        from .analysis_engine import AnalysisEngine
        return AnalysisEngine()
    except ImportError as exc:
        logger.warning(
            "AI включён, но зависимости недоступны (%s) — работаем без AI",
            exc,
        )
        return NullAnalysisEngine()


__all__ = ('NullAnalysisEngine', 'get_analysis_engine')