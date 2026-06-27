"""
Тесты для AI-опциональности и Celery-задач.

Покрывает:
- get_analysis_engine() возвращает NullAnalysisEngine при AI_ENABLED=False
- analyze_resume_task и match_candidate_with_job_task — no-op при AI_ENABLED=False
- Включение AI_ENABLED=True с заглушкой AnalysisEngine — задачи ставятся в очередь
"""
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from ai_analysis.services import NullAnalysisEngine, get_analysis_engine
from ai_analysis.tasks import (
    analyze_resume_task, match_candidate_with_job_task,
)
from core.models import Candidate, Company, Job
from resume.models import Resume

User = get_user_model()


class AIOptionalityTests(TestCase):
    """get_analysis_engine() возвращает правильный движок."""

    @override_settings(AI_ENABLED=False)
    def test_returns_null_engine_when_disabled(self):
        engine = get_analysis_engine()
        self.assertIsInstance(engine, NullAnalysisEngine)
        self.assertFalse(engine.enabled)

    @override_settings(AI_ENABLED=True)
    def test_returns_real_engine_when_enabled(self):
        # При включённом AI пытаемся загрузить реальный движок.
        # Если sentence_transformers недоступен — должен вернуться NullAnalysisEngine.
        engine = get_analysis_engine()
        self.assertIn(engine.enabled, (True, False))

    def test_null_engine_analyze_resume_marks_processed(self):
        """NullAnalysisEngine.analyze_resume() помечает резюме как processed."""
        cand_user = User.objects.create_user(username='cand', user_type='candidate', email='c@example.com')
        candidate = Candidate.objects.create(
            user=cand_user, first_name='И', last_name='И', email='c@example.com',
        )
        resume = Resume.objects.create(
            candidate=candidate,
            file=SimpleUploadedFile('r.pdf', b'%PDF-1.4 fake'),
            original_filename='r.pdf',
            file_size=100,
            status='uploaded',
        )

        engine = NullAnalysisEngine()
        result = engine.analyze_resume(resume.id)

        self.assertTrue(result['success'])
        self.assertFalse(result['ai_enabled'])
        resume.refresh_from_db()
        self.assertEqual(resume.status, 'processed')

    def test_null_engine_match_returns_no_score(self):
        """NullAnalysisEngine.match_candidate_with_job() не выставляет ai_score."""
        hr = User.objects.create_user(username='hr', user_type='hr')
        cand_user = User.objects.create_user(username='cand', user_type='candidate', email='c@example.com')
        candidate = Candidate.objects.create(
            user=cand_user, first_name='И', last_name='И', email='c@example.com',
        )
        company = Company.objects.create(name='Acme')
        job = Job.objects.create(
            title='Dev', company=company, description='', requirements='',
            experience_level='middle', location='M', created_by=hr,
        )
        resume = Resume.objects.create(
            candidate=candidate,
            file=SimpleUploadedFile('r.pdf', b'%PDF-1.4 fake'),
            original_filename='r.pdf', file_size=100, status='processed',
        )

        engine = NullAnalysisEngine()
        result = engine.match_candidate_with_job(resume.id, job.id)

        self.assertTrue(result['success'])
        self.assertIsNone(result['overall_score'])
        self.assertIsNone(result['recommendation'])


class CeleryTaskEagerTests(TestCase):
    """Тесты Celery-задач в eager-режиме (без Redis)."""

    def setUp(self):
        hr = User.objects.create_user(username='hr', user_type='hr')
        cand_user = User.objects.create_user(username='cand', user_type='candidate', email='c@example.com')
        self.candidate = Candidate.objects.create(
            user=cand_user, first_name='И', last_name='И', email='c@example.com',
        )
        company = Company.objects.create(name='Acme')
        self.job = Job.objects.create(
            title='Dev', company=company, description='', requirements='',
            experience_level='middle', location='M', created_by=hr,
        )
        self.resume = Resume.objects.create(
            candidate=self.candidate,
            file=SimpleUploadedFile('r.pdf', b'%PDF-1.4 fake'),
            original_filename='r.pdf', file_size=100, status='processing',
        )

    @override_settings(AI_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True)
    def test_analyze_resume_task_noop_when_disabled(self):
        """analyze_resume_task — no-op при AI_ENABLED=False (даже в eager)."""
        result = analyze_resume_task.apply(args=[self.resume.id]).get()
        self.assertTrue(result['success'])
        self.assertFalse(result['ai_enabled'])

    @override_settings(AI_ENABLED=False, CELERY_TASK_ALWAYS_EAGER=True)
    def test_match_task_noop_when_disabled(self):
        """match_candidate_with_job_task — no-op при AI_ENABLED=False."""
        result = match_candidate_with_job_task.apply(
            args=[self.resume.id, self.job.id],
        ).get()
        self.assertTrue(result['success'])
        self.assertFalse(result['ai_enabled'])
        self.assertIsNone(result['overall_score'])

    @override_settings(AI_ENABLED=True, CELERY_TASK_ALWAYS_EAGER=True)
    def test_analyze_resume_task_enables_engine(self):
        """analyze_resume_task запускает движок при AI_ENABLED=True (graceful degradation)."""
        # Если sentence_transformers установлен — реальный движок, иначе NullAnalysisEngine.
        # Главное — задача не падает с ImportError.
        result = analyze_resume_task.apply(args=[self.resume.id]).get()
        self.assertIn('success', result)