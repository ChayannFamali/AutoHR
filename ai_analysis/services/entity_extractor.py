import logging
import re
from typing import Dict, List, Set, Tuple

from ..utils.skills_database import (SKILLS_SET, get_skill_category,
                                     normalize_skill)

logger = logging.getLogger(__name__)

class EntityExtractor:
    """Класс для извлечения сущностей из текста резюме"""
    
    def __init__(self):
        self.skills_set = SKILLS_SET
        
    def extract_skills(self, text: str) -> List[Dict[str, str]]:
        """
        Извлекает навыки из текста резюме
        
        Args:
            text: Текст резюме
            
        Returns:
            list: Список найденных навыков с категориями
        """
        found_skills = []
        text_lower = text.lower()
        
        for skill in self.skills_set:
            if self._is_skill_mentioned(skill, text_lower):
                normalized_skill = normalize_skill(skill)
                category = get_skill_category(normalized_skill)
                
                found_skills.append({
                    'name': normalized_skill,
                    'category': category,
                    'original': skill
                })
        
        unique_skills = []
        seen_skills = set()
        
        for skill in found_skills:
            if skill['name'] not in seen_skills:
                unique_skills.append(skill)
                seen_skills.add(skill['name'])
        
        logger.info(f"Extracted {len(unique_skills)} unique skills")
        return unique_skills
    
    def _is_skill_mentioned(self, skill: str, text: str) -> bool:
        """
        Проверяет, упоминается ли навык в тексте
        
        Args:
            skill: Название навыка
            text: Текст для поиска
            
        Returns:
            bool: True если навык найден
        """
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        return bool(re.search(pattern, text))
    
    def extract_work_experience(self, text: str) -> List[Dict[str, str]]:
        """
        Извлекает информацию об опыте работы
        
        Args:
            text: Текст резюме
            
        Returns:
            list: Список мест работы
        """
        experience_entries = []
        
        job_patterns = [
            # Паттерн: Должность в Компании (даты)
            r'([А-ЯA-Z][а-яa-z\s]+(?:разработчик|developer|менеджер|manager|аналитик|analyst|дизайнер|designer|инженер|engineer))\s+(?:в|at|@)\s+([А-ЯA-Z][а-яa-z\s&.]+)(?:\s+(\d{4}[-–—]\d{4}|\d{4}[-–—]н\.в\.|\d{4}[-–—]present))?',
            
            # Паттерн: Компания - Должность
            r'([А-ЯA-Z][а-яa-z\s&.]+)[-–—]\s*([А-ЯA-Z][а-яa-z\s]+(?:разработчик|developer|менеджер|manager|аналитик|analyst))',
            
            # Паттерн: Должность (период)
            r'([А-ЯA-Z][а-яa-z\s]+(?:разработчик|developer|менеджер|manager))\s*$$([^)]+)$$'
        ]
        
        for pattern in job_patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    experience_entries.append({
                        'position': match[0].strip(),
                        'company': match[1].strip() if len(match) > 1 else '',
                        'period': match[2].strip() if len(match) > 2 else '',
                        'description': ''
                    })
        
        logger.info(f"Extracted {len(experience_entries)} work experience entries")
        return experience_entries
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """
        Извлекает информацию об образовании
        
        Args:
            text: Текст резюме
            
        Returns:
            list: Список учебных заведений
        """
        education_entries = []
        
        # Ключевые слова для учебных заведений
        education_keywords = [
            'университет', 'институт', 'академия', 'college', 'university',
            'технический', 'государственный', 'федеральный', 'политехнический'
        ]
        
        # Степени образования
        degree_keywords = [
            'бакалавр', 'магистр', 'специалист', 'bachelor', 'master',
            'кандидат наук', 'доктор наук', 'phd', 'мба', 'mba'
        ]
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            # Проверяем, содержит ли строка информацию об образовании
            if any(keyword in line_lower for keyword in education_keywords):
                # Ищем степень в этой или соседних строках
                degree = ''
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    check_line = lines[j].lower()
                    for deg_keyword in degree_keywords:
                        if deg_keyword in check_line:
                            degree = deg_keyword
                            break
                
                # Извлекаем год
                year_match = re.search(r'(19|20)\d{2}', line)
                year = year_match.group() if year_match else ''
                
                education_entries.append({
                    'institution': line.strip(),
                    'degree': degree,
                    'year': year,
                    'field': ''
                })
        
        logger.info(f"Extracted {len(education_entries)} education entries")
        return education_entries
    
    def extract_languages(self, text: str) -> List[Dict[str, str]]:
        """
        Извлекает информацию о языках
        
        Args:
            text: Текст резюме
            
        Returns:
            list: Список языков с уровнями
        """
        languages = []
        text_lower = text.lower()
        
        language_variants = {
            'русский': ['русский', 'russian'],
            'английский': ['английский', 'english', 'англ'],
            'немецкий': ['немецкий', 'german', 'deutsch'],
            'французский': ['французский', 'french', 'français'],
            'испанский': ['испанский', 'spanish', 'español'],
            'итальянский': ['итальянский', 'italian', 'italiano'],
            'китайский': ['китайский', 'chinese', '中文'],
            'японский': ['японский', 'japanese', '日本語']
        }
        
        level_patterns = {
            'native': ['родной', 'native', 'носитель'],
            'fluent': ['свободно', 'fluent', 'c2', 'продвинутый'],
            'advanced': ['продвинутый', 'advanced', 'c1', 'хорошо'],
            'intermediate': ['средний', 'intermediate', 'b2', 'b1'],
            'beginner': ['начинающий', 'beginner', 'a2', 'a1', 'базовый']
        }
        
        for lang_name, variants in language_variants.items():
            for variant in variants:
                if variant in text_lower:
                    level = 'unknown'
                    for level_name, level_variants in level_patterns.items():
                        for level_variant in level_variants:
                            if level_variant in text_lower:
                                level = level_name
                                break
                        if level != 'unknown':
                            break
                    
                    languages.append({
                        'language': lang_name,
                        'level': level
                    })
                    break
        
        logger.info(f"Extracted {len(languages)} languages")
        return languages
