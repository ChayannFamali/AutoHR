"""
Celery-задачи для AI-операций.

Принципы (см. docs/skills.md, SKILL 3):
- ML-модель грузится лениво внутри воркера, не веб-процесса.
- Если AI выключен (`settings.AI_ENABLED=False`) — задача no-op,
  чтобы Redis/воркер был опционален.
- При ошибках — `self.retry()` с `max_retries=3`.
"""
import logging

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_resume_task(self, resume_id: int):
    """Асинхронный анализ резюме (вызывается из resume/views.py)."""
    if not getattr(settings, 'AI_ENABLED', False):
        logger.info('AI выключен — analyze_resume_task no-op (resume_id=%s)', resume_id)
        from ai_analysis.services import NullAnalysisEngine
        return NullAnalysisEngine().analyze_resume(resume_id)

    try:
        from ai_analysis.services import get_analysis_engine
        engine = get_analysis_engine()
        return engine.analyze_resume(resume_id)
    except Exception as exc:
        logger.exception('analyze_resume_task failed (resume_id=%s): %s', resume_id, exc)
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def match_candidate_with_job_task(self, resume_id: int, job_id: int):
    """Асинхронное сопоставление кандидата и вакансии (вызывается из core/views.py)."""
    if not getattr(settings, 'AI_ENABLED', False):
        logger.info(
            'AI выключен — match_candidate_with_job_task no-op '
            '(resume_id=%s, job_id=%s)', resume_id, job_id,
        )
        from ai_analysis.services import NullAnalysisEngine
        return NullAnalysisEngine().match_candidate_with_job(resume_id, job_id)

    try:
        from ai_analysis.services import get_analysis_engine
        engine = get_analysis_engine()
        return engine.match_candidate_with_job(resume_id, job_id)
    except Exception as exc:
        logger.exception(
            'match_candidate_with_job_task failed (resume_id=%s, job_id=%s): %s',
            resume_id, job_id, exc,
        )
        raise self.retry(exc=exc)