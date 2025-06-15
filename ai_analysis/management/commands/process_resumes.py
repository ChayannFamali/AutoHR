import logging

from django.core.management.base import BaseCommand
from django.db import transaction

from ai_analysis.services.analysis_engine import AnalysisEngine
from resume.models import Resume

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Process unanalyzed resumes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--resume-id',
            type=int,
            help='Process specific resume by ID'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of resumes to process in batch'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocess already analyzed resumes'
        )
    
    def handle(self, *args, **options):
        analysis_engine = AnalysisEngine()
        
        if options['resume_id']:
            # Обрабатываем конкретное резюме
            self.process_single_resume(analysis_engine, options['resume_id'])
        else:
            # Обрабатываем пакет резюме
            self.process_batch_resumes(
                analysis_engine, 
                options['batch_size'], 
                options['force']
            )
    
    def process_single_resume(self, analysis_engine, resume_id):
        """Обрабатывает одно резюме"""
        try:
            resume = Resume.objects.get(id=resume_id)
            self.stdout.write(f"Processing resume {resume_id}: {resume.original_filename}")
            
            result = analysis_engine.analyze_resume(resume_id)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully processed resume {resume_id}. "
                        f"Skills: {result['skills_count']}, "
                        f"Experience: {result['experience_years']} years"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to process resume {resume_id}: {result['error']}"
                    )
                )
                
        except Resume.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"Resume with ID {resume_id} not found")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error processing resume {resume_id}: {str(e)}")
            )
    
    def process_batch_resumes(self, analysis_engine, batch_size, force_reprocess):
        """Обрабатывает пакет резюме"""
        if force_reprocess:
            resumes = Resume.objects.all()[:batch_size]
            self.stdout.write(f"Force reprocessing {len(resumes)} resumes")
        else:
            resumes = Resume.objects.filter(
                status__in=['uploaded', 'error']
            )[:batch_size]
            self.stdout.write(f"Processing {len(resumes)} unanalyzed resumes")
        
        if not resumes:
            self.stdout.write("No resumes to process")
            return
        
        processed_count = 0
        error_count = 0
        
        for resume in resumes:
            try:
                self.stdout.write(f"Processing: {resume.original_filename}")
                
                result = analysis_engine.analyze_resume(resume.id)
                
                if result['success']:
                    processed_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Processed {resume.original_filename}")
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed {resume.original_filename}: {result['error']}")
                    )
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error {resume.original_filename}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nBatch processing completed:\n"
                f"Successfully processed: {processed_count}\n"
                f"Errors: {error_count}\n"
                f"Total: {processed_count + error_count}"
            )
        )
