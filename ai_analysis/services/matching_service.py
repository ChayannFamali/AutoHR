import logging
from typing import Dict, List, Optional, Tuple

from ..utils.skills_database import get_skill_category
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class MatchingService:
    """Сервис для сопоставления кандидатов и вакансий"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def calculate_candidate_job_match(self, 
                                    resume_data: Dict, 
                                    job_data: Dict) -> Dict[str, float]:
        """
        Вычисляет соответствие между кандидатом и вакансией
        
        Args:
            resume_data: Данные резюме
            job_data: Данные вакансии
            
        Returns:
            dict: Метрики соответствия
        """
        try:
            match_result = {
                'overall_score': 0.0,
                'skills_score': 0.0,
                'experience_score': 0.0,
                'text_similarity': 0.0,
                'matched_skills': [],
                'missing_skills': [],
                'experience_analysis': {}
            }
            
            # 1. Анализ навыков
            skills_analysis = self._analyze_skills_match(
                resume_data.get('skills', []),
                job_data.get('required_skills', [])
            )
            
            match_result['skills_score'] = skills_analysis['score']
            match_result['matched_skills'] = skills_analysis['matched']
            match_result['missing_skills'] = skills_analysis['missing']
            
            # 2. Анализ опыта
            experience_analysis = self._analyze_experience_match(
                resume_data.get('experience_years', 0),
                job_data.get('required_experience', 0),
                resume_data.get('work_experience', []),
                job_data.get('experience_level', '')
            )
            
            match_result['experience_score'] = experience_analysis['score']
            match_result['experience_analysis'] = experience_analysis
            
            # 3. Семантическое сходство текстов
            text_similarity = self._calculate_text_similarity(
                resume_data.get('text_embedding', []),
                job_data.get('requirements_embedding', [])
            )
            
            match_result['text_similarity'] = text_similarity
            
            # 4. Общая оценка (взвешенная сумма)
            weights = {
                'skills': 0.4,
                'experience': 0.3,
                'text': 0.3
            }
            
            match_result['overall_score'] = (
                weights['skills'] * match_result['skills_score'] +
                weights['experience'] * match_result['experience_score'] +
                weights['text'] * match_result['text_similarity']
            )
            
            logger.info(f"Match calculated: overall_score={match_result['overall_score']:.3f}")
            return match_result
            
        except Exception as e:
            logger.error(f"Error calculating candidate-job match: {str(e)}")
            return {
                'overall_score': 0.0,
                'skills_score': 0.0,
                'experience_score': 0.0,
                'text_similarity': 0.0,
                'matched_skills': [],
                'missing_skills': [],
                'experience_analysis': {}
            }
    
    def _analyze_skills_match(self, 
                            candidate_skills: List[str], 
                            required_skills: List[str]) -> Dict:
        """Анализирует соответствие навыков"""
        if not required_skills:
            return {
                'score': 1.0,
                'matched': candidate_skills,
                'missing': []
            }
        
        candidate_skills_lower = [skill.lower().strip() for skill in candidate_skills]
        required_skills_lower = [skill.lower().strip() for skill in required_skills]
        
        matched_skills = []
        for req_skill in required_skills:
            req_skill_lower = req_skill.lower().strip()
            if req_skill_lower in candidate_skills_lower:
                matched_skills.append(req_skill)
        
        for req_skill in required_skills:
            if req_skill in matched_skills:
                continue
            
            req_skill_lower = req_skill.lower().strip()
            for cand_skill in candidate_skills:
                cand_skill_lower = cand_skill.lower().strip()
                
                if (req_skill_lower in cand_skill_lower or 
                    cand_skill_lower in req_skill_lower):
                    matched_skills.append(req_skill)
                    break
        
        missing_skills = [skill for skill in required_skills if skill not in matched_skills]
        
        if not required_skills:
            score = 1.0
        else:
            score = len(matched_skills) / len(required_skills)
        
        return {
            'score': score,
            'matched': matched_skills,
            'missing': missing_skills
        }
    
    def _analyze_experience_match(self, 
                                candidate_years: int,
                                required_years: int,
                                work_experience: List[Dict],
                                experience_level: str) -> Dict:
        """Анализирует соответствие опыта работы"""
        
        analysis = {
            'score': 0.0,
            'years_match': False,
            'level_match': False,
            'relevant_experience': []
        }
        
        # 1. Сравнение по годам опыта
        if required_years == 0:
            analysis['years_match'] = True
            years_score = 1.0
        elif candidate_years >= required_years:
            analysis['years_match'] = True
            years_score = 1.0
        else:
            # Частичное соответствие, если опыта меньше требуемого
            years_score = candidate_years / required_years if required_years > 0 else 0.0
        
        # 2. Сравнение по уровню (junior/middle/senior)
        level_score = self._match_experience_level(candidate_years, experience_level)
        if level_score > 0.7:
            analysis['level_match'] = True
        
        # 3. Анализ релевантного опыта работы
        relevant_exp = self._find_relevant_experience(work_experience, experience_level)
        analysis['relevant_experience'] = relevant_exp
        
        # Общая оценка опыта
        analysis['score'] = (years_score * 0.6 + level_score * 0.4)
        
        return analysis
    
    def _match_experience_level(self, candidate_years: int, required_level: str) -> float:
        """Сопоставляет уровень опыта"""
        if not required_level:
            return 1.0
        
        required_level = required_level.lower()
        
        level_mapping = {
            'junior': (0, 2),
            'middle': (2, 5),
            'senior': (5, 100)
        }
        
        for level, (min_years, max_years) in level_mapping.items():
            if level in required_level:
                if min_years <= candidate_years <= max_years:
                    return 1.0
                elif candidate_years > max_years:
                    return 0.8
                else:
                    return candidate_years / min_years if min_years > 0 else 0.0
        
        return 0.5
    
    def _find_relevant_experience(self, work_experience: List[Dict], job_context: str) -> List[Dict]:
        """Находит релевантный опыт работы"""
        relevant = []
        
        if not work_experience or not job_context:
            return relevant
        
        job_context_lower = job_context.lower()
        
        for exp in work_experience:
            position = exp.get('position', '').lower()
            company = exp.get('company', '').lower()
            description = exp.get('description', '').lower()
            
            if any(keyword in position + company + description 
                   for keyword in job_context_lower.split()):
                relevant.append(exp)
        
        return relevant
    
    def _calculate_text_similarity(self, 
                                 resume_embedding: List[float], 
                                 job_embedding: List[float]) -> float:
        """Вычисляет семантическое сходство текстов"""
        if not resume_embedding or not job_embedding:
            return 0.0
        
        return self.embedding_service.calculate_similarity(
            resume_embedding, 
            job_embedding
        )
    
    def generate_recommendation(self, match_result: Dict[str, float]) -> str:
        """
        Генерирует рекомендацию на основе анализа соответствия
        
        Args:
            match_result: Результат анализа соответствия
            
        Returns:
            str: Текстовая рекомендация
        """
        overall_score = match_result.get('overall_score', 0.0)
        skills_score = match_result.get('skills_score', 0.0)
        experience_score = match_result.get('experience_score', 0.0)
        
        if overall_score >= 0.8:
            recommendation = "strong_match"
            reason = "Кандидат отлично подходит для данной позиции."
        elif overall_score >= 0.6:
            recommendation = "good_match"
            reason = "Кандидат хорошо подходит для позиции."
        elif overall_score >= 0.4:
            recommendation = "partial_match"
            reason = "Кандидат частично подходит для позиции."
        else:
            recommendation = "weak_match"
            reason = "Кандидат слабо подходит для данной позиции."
        
        details = []
        
        if skills_score < 0.5:
            missing_count = len(match_result.get('missing_skills', []))
            details.append(f"Недостает {missing_count} ключевых навыков.")
        
        if experience_score < 0.5:
            details.append("Недостаточный опыт работы.")
        
        if skills_score > 0.8:
            details.append("Отличное соответствие по навыкам.")
        
        if experience_score > 0.8:
            details.append("Подходящий уровень опыта.")
        
        full_reason = reason
        if details:
            full_reason += " " + " ".join(details)
        
        return full_reason
