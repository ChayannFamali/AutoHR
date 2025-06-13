import logging
from typing import Dict, List, Optional

from django.utils import timezone

from ai_analysis.models import AnalysisTask, JobCandidateMatch
from ai_analysis.services.document_parser import DocumentParser
from ai_analysis.services.embedding_service import EmbeddingService
from ai_analysis.services.entity_extractor import EntityExtractor
from ai_analysis.services.matching_service import MatchingService
from ai_analysis.services.text_processor import TextProcessor
from core.models import Application, Job
from resume.models import Resume, ResumeAnalysis

logger = logging.getLogger(__name__)

class AnalysisEngine:
    """Главный движок для анализа резюме и сопоставления с вакансиями"""
    
    def __init__(self):
        self.document_parser = DocumentParser()
        self.text_processor = TextProcessor()
        self.entity_extractor = EntityExtractor()
        self.embedding_service = EmbeddingService()
        self.matching_service = MatchingService()
    
    def analyze_resume(self, resume_id: int) -> Dict:
        """
        Полный анализ резюме
        
        Args:
            resume_id: ID резюме для анализа
            
        Returns:
            dict: Результаты анализа
        """
        try:
            # Получаем резюме
            resume = Resume.objects.get(id=resume_id)
            
            # Создаем задачу анализа
            task = AnalysisTask.objects.create(
                task_type='resume_analysis',
                resume=resume,
                status='running'
            )
            
            logger.info(f"Starting resume analysis for resume_id={resume_id}")
            
            # 1. Парсинг документа
            if not resume.extracted_text:
                text, metadata = self.document_parser.parse_document(resume.file.path)
                resume.extracted_text = text
                resume.save()
            else:
                text = resume.extracted_text
                metadata = {}
            
            if not text:
                raise Exception("No text extracted from document")
            
            # 2. Обработка текста
            cleaned_text = self.text_processor.clean_text(text)
            sections = self.text_processor.split_into_sections(text)
            contacts = self.text_processor.extract_contact_info(text)
            years_experience = self.text_processor.extract_years_of_experience(text)
            
            # 3. Извлечение сущностей
            skills = self.entity_extractor.extract_skills(text)
            work_experience = self.entity_extractor.extract_work_experience(text)
            education = self.entity_extractor.extract_education(text)
            languages = self.entity_extractor.extract_languages(text)
            
            # 4. Создание embeddings
            normalized_text = self.text_processor.normalize_text_for_embedding(text)
            text_embedding = self.embedding_service.create_text_embedding(normalized_text)
            
            skills_list = [skill['name'] for skill in skills]
            skills_embedding = self.embedding_service.create_skills_embedding(skills_list)
            
            # 5. Обновляем данные резюме
            resume.skills = skills_list
            resume.experience_years = years_experience
            resume.work_experience = work_experience
            resume.education = education
            resume.text_embedding = text_embedding
            resume.skills_embedding = skills_embedding
            resume.status = 'processed'
            resume.processed_at = timezone.now()
            resume.save()
            
            # 6. Создаем или обновляем анализ резюме
            analysis, created = ResumeAnalysis.objects.get_or_create(
                resume=resume,
                defaults={
                    'key_skills': skills_list,
                    'experience_summary': self._generate_experience_summary(work_experience),
                    'education_level': self._determine_education_level(education),
                    'completeness_score': self._calculate_completeness_score(resume, contacts),
                    'relevance_keywords': self._extract_relevance_keywords(skills, work_experience)
                }
            )
            
            if not created:
                # Обновляем существующий анализ
                analysis.key_skills = skills_list
                analysis.experience_summary = self._generate_experience_summary(work_experience)
                analysis.education_level = self._determine_education_level(education)
                analysis.completeness_score = self._calculate_completeness_score(resume, contacts)
                analysis.relevance_keywords = self._extract_relevance_keywords(skills, work_experience)
                analysis.save()
            
            # 7. Завершаем задачу
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.result_data = {
                'skills_count': len(skills),
                'experience_years': years_experience,
                'completeness_score': analysis.completeness_score
            }
            task.save()
            
            logger.info(f"Resume analysis completed for resume_id={resume_id}")
            
            return {
                'success': True,
                'resume_id': resume_id,
                'skills_count': len(skills),
                'experience_years': years_experience,
                'completeness_score': analysis.completeness_score,
                'analysis_id': analysis.id
            }
            
        except Exception as e:
            logger.error(f"Error analyzing resume {resume_id}: {str(e)}")
            
            # Обновляем статус задачи при ошибке
            if 'task' in locals():
                task.status = 'failed'
                task.error_message = str(e)
                task.save()
            
            # Обновляем статус резюме
            try:
                resume = Resume.objects.get(id=resume_id)
                resume.status = 'error'
                resume.processing_error = str(e)
                resume.save()
            except:
                pass
            
            return {
                'success': False,
                'error': str(e),
                'resume_id': resume_id
            }
    
    def match_candidate_with_job(self, resume_id: int, job_id: int) -> Dict:
        """
        Сопоставляет кандидата с вакансией
        
        Args:
            resume_id: ID резюме
            job_id: ID вакансии
            
        Returns:
            dict: Результаты сопоставления
        """
        try:
            resume = Resume.objects.get(id=resume_id)
            job = Job.objects.get(id=job_id)
            
            logger.info(f"Matching resume_id={resume_id} with job_id={job_id}")
            
            # Убеждаемся, что резюме проанализировано
            if resume.status != 'processed':
                self.analyze_resume(resume_id)
                resume.refresh_from_db()
            
            # Создаем embeddings для вакансии, если их нет
            if not job.requirements_embedding:
                job_text = f"{job.description} {job.requirements}"
                job.requirements_embedding = self.embedding_service.create_text_embedding(job_text)
                job.save()
            
            # Подготавливаем данные для сопоставления
            resume_data = {
                'skills': resume.skills or [],
                'experience_years': resume.experience_years or 0,
                'work_experience': resume.work_experience or [],
                'text_embedding': resume.text_embedding or []
            }
            
            job_data = {
                'required_skills': self._extract_job_skills(job),
                'required_experience': self._get_required_experience_years(job.experience_level),
                'experience_level': job.experience_level,
                'requirements_embedding': job.requirements_embedding or []
            }
            
            # Выполняем сопоставление
            match_result = self.matching_service.calculate_candidate_job_match(
                resume_data, job_data
            )
            
            # Генерируем рекомендацию
            recommendation = self.matching_service.generate_recommendation(match_result)
            
            # Сохраняем результат в базе данных
            job_match, created = JobCandidateMatch.objects.get_or_create(
                job=job,
                candidate=resume.candidate,
                resume=resume,
                defaults={
                    'overall_score': match_result['overall_score'],
                    'skills_score': match_result['skills_score'],
                    'experience_score': match_result['experience_score'],
                    'matched_skills': match_result['matched_skills'],
                    'missing_skills': match_result['missing_skills'],
                    'experience_analysis': match_result['experience_analysis'],
                    'recommendation': self._get_recommendation_level(match_result['overall_score']),
                    'reasoning': recommendation
                }
            )
            
            if not created:
                # Обновляем существующее соответствие
                job_match.overall_score = match_result['overall_score']
                job_match.skills_score = match_result['skills_score']
                job_match.experience_score = match_result['experience_score']
                job_match.matched_skills = match_result['matched_skills']
                job_match.missing_skills = match_result['missing_skills']
                job_match.experience_analysis = match_result['experience_analysis']
                job_match.recommendation = self._get_recommendation_level(match_result['overall_score'])
                job_match.reasoning = recommendation
                job_match.save()
            
            logger.info(f"Match completed: score={match_result['overall_score']:.3f}")
            
            return {
                'success': True,
                'match_id': job_match.id,
                'overall_score': match_result['overall_score'],
                'recommendation': recommendation,
                'matched_skills': match_result['matched_skills'],
                'missing_skills': match_result['missing_skills']
            }
            
        except Exception as e:
            logger.error(f"Error matching resume {resume_id} with job {job_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_experience_summary(self, work_experience: List[Dict]) -> str:
        """Генерирует краткое описание опыта работы"""
        if not work_experience:
            return "Опыт работы не указан"
        
        positions = [exp.get('position', '') for exp in work_experience if exp.get('position')]
        companies = [exp.get('company', '') for exp in work_experience if exp.get('company')]
        
        summary = f"Работал на {len(work_experience)} позициях"
        if positions:
            summary += f", включая: {', '.join(positions[:3])}"
        if companies:
            summary += f" в компаниях: {', '.join(companies[:3])}"
        
        return summary
    
    def _determine_education_level(self, education: List[Dict]) -> str:
        """Определяет уровень образования"""
        if not education:
            return "Не указано"
        
        degrees = [edu.get('degree', '').lower() for edu in education]
        
        if any('доктор' in degree or 'phd' in degree for degree in degrees):
            return "Докторская степень"
        elif any('магистр' in degree or 'master' in degree for degree in degrees):
            return "Магистратура"
        elif any('бакалавр' in degree or 'bachelor' in degree for degree in degrees):
            return "Бакалавриат"
        elif any('специалист' in degree for degree in degrees):
            return "Специалитет"
        else:
            return "Высшее образование"
    
    def _calculate_completeness_score(self, resume: Resume, contacts: Dict) -> float:
        """Вычисляет полноту резюме"""
        score = 0.0
        max_score = 10.0
        
        # Проверяем наличие основных элементов
        if resume.extracted_text and len(resume.extracted_text) > 100:
            score += 2.0  # Есть содержательный текст
        
        if resume.skills:
            score += 2.0  # Есть навыки
        
        if resume.work_experience:
            score += 2.0  # Есть опыт работы
        
        if resume.education:
            score += 1.5  # Есть образование
        
        if contacts.get('emails'):
            score += 1.0  # Есть email
        
        if contacts.get('phones'):
            score += 1.0  # Есть телефон
        
        if resume.experience_years and resume.experience_years > 0:
            score += 0.5  # Указан опыт в годах
        
        return min(score / max_score, 1.0)
    
    def _extract_relevance_keywords(self, skills: List[Dict], work_experience: List[Dict]) -> List[str]:
        """Извлекает ключевые слова для релевантности"""
        keywords = []
        
        # Добавляем навыки
        for skill in skills:
            keywords.append(skill.get('name', ''))
        
        # Добавляем должности
        for exp in work_experience:
            if exp.get('position'):
                keywords.append(exp['position'])
        
        return list(set(filter(None, keywords)))
    
    def _extract_job_skills(self, job: Job) -> List[str]:
        """Извлекает навыки из описания вакансии"""
        # Простое извлечение - можно улучшить
        text = f"{job.description} {job.requirements}".lower()
        skills = self.entity_extractor.extract_skills(text)
        return [skill['name'] for skill in skills]
    
    def _get_required_experience_years(self, experience_level: str) -> int:
        """Преобразует уровень опыта в годы"""
        level_mapping = {
            'junior': 1,
            'middle': 3,
            'senior': 5
        }
        
        for level, years in level_mapping.items():
            if level in experience_level.lower():
                return years
        
        return 0
    
    def _get_recommendation_level(self, score: float) -> str:
        """Преобразует оценку в уровень рекомендации"""
        if score >= 0.8:
            return 'strong_match'
        elif score >= 0.6:
            return 'good_match'
        elif score >= 0.4:
            return 'partial_match'
        else:
            return 'weak_match'
