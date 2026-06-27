"""
Ставит задачи analyze_resume_task в Celery-очередь.

Не выполняет AI-анализ синхронно — для этого должен быть запущен воркер:
    celery -A autohr worker -l info

При AI_ENABLED=False задачи no-op (см. ai_analysis/tasks.py).
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from ai_analysis.tasks import analyze_resume_task
from resume.models import Resume


class Command(BaseCommand):
    help = 'Enqueue resume analysis tasks to Celery'

    def add_arguments(self, parser):
        parser.add_argument(
            '--resume-id',
            type=int,
            help='Process specific resume by ID',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of resumes to enqueue in batch',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-enqueue already analyzed resumes',
        )

    def handle(self, *args, **options):
        if not getattr(settings, 'AI_ENABLED', False):
            self.stdout.write(self.style.WARNING(
                'AI_ENABLED=False — задачи будут no-op. Включите AI_ENABLED=True '
                'и запустите воркер, чтобы выполнять анализ.',
            ))

        if options['resume_id']:
            self.enqueue_single(options['resume_id'])
        else:
            self.enqueue_batch(
                options['batch_size'],
                options['force'],
            )

    def enqueue_single(self, resume_id):
        try:
            Resume.objects.get(id=resume_id)
        except Resume.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Resume {resume_id} not found'))
            return
        analyze_resume_task.delay(resume_id)
        self.stdout.write(self.style.SUCCESS(
            f'Task enqueued for resume_id={resume_id}',
        ))

    def enqueue_batch(self, batch_size, force_reprocess):
        if force_reprocess:
            resumes = Resume.objects.all()[:batch_size]
        else:
            resumes = Resume.objects.filter(
                status__in=['uploaded', 'error']
            )[:batch_size]

        if not resumes:
            self.stdout.write('No resumes to enqueue')
            return

        for resume in resumes:
            analyze_resume_task.delay(resume.id)
            self.stdout.write(f'Enqueued resume_id={resume.id} ({resume.original_filename})')

        self.stdout.write(self.style.SUCCESS(
            f'\nEnqueued {len(resumes)} tasks to Celery.',
        ))