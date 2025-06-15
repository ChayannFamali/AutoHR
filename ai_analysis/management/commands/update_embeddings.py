import logging

from django.core.management.base import BaseCommand

from ai_analysis.services.embedding_service import EmbeddingService
from core.models import Job
from resume.models import Resume

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update embeddings for jobs and resumes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['jobs', 'resumes', 'all'],
            default='all',
            help='Type of embeddings to update'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing embeddings'
        )
    
    def handle(self, *args, **options):
        embedding_service = EmbeddingService()
        
        if options['type'] in ['jobs', 'all']:
            self.update_job_embeddings(embedding_service, options['force'])
        
        if options['type'] in ['resumes', 'all']:
            self.update_resume_embeddings(embedding_service, options['force'])
    
    def update_job_embeddings(self, embedding_service, force_update):
        """Обновляет embeddings для вакансий"""
        self.stdout.write("Updating job embeddings...")
        
        if force_update:
            jobs = Job.objects.all()
        else:
            jobs = Job.objects.filter(requirements_embedding__isnull=True)
        
        updated_count = 0
        error_count = 0
        
        for job in jobs:
            try:
                job_text = f"{job.title} {job.description} {job.requirements}"
                
                embedding = embedding_service.create_text_embedding(job_text)
                
                if embedding:
                    job.requirements_embedding = embedding
                    job.save()
                    updated_count += 1
                    self.stdout.write(f"✓ Updated job: {job.title}")
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed to create embedding for job: {job.title}")
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error updating job {job.title}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Job embeddings update completed: {updated_count} updated, {error_count} errors"
            )
        )
    
    def update_resume_embeddings(self, embedding_service, force_update):
        """Обновляет embeddings для резюме"""
        self.stdout.write("Updating resume embeddings...")
        
        if force_update:
            resumes = Resume.objects.filter(status='processed')
        else:
            resumes = Resume.objects.filter(
                status='processed',
                text_embedding__isnull=True
            )
        
        updated_count = 0
        error_count = 0
        
        for resume in resumes:
            try:
                if not resume.extracted_text:
                    continue
                
                text_embedding = embedding_service.create_text_embedding(
                    resume.extracted_text
                )
                
                skills_embedding = None
                if resume.skills:
                    skills_embedding = embedding_service.create_skills_embedding(
                        resume.skills
                    )
                
                if text_embedding:
                    resume.text_embedding = text_embedding
                    if skills_embedding:
                        resume.skills_embedding = skills_embedding
                    resume.save()
                    updated_count += 1
                    self.stdout.write(f"✓ Updated resume: {resume.original_filename}")
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed to create embedding for resume: {resume.original_filename}")
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error updating resume {resume.original_filename}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Resume embeddings update completed: {updated_count} updated, {error_count} errors"
            )
        )
