import logging
import re
import string
from typing import Dict, List, Set

logger = logging.getLogger(__name__)

class TextProcessor:
    """Класс для обработки и очистки текста резюме"""
    
    def __init__(self):
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'[\+]?[7-8]?[\s\-]?[$$]?[0-9]{3}[$$]?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}')
        self.url_pattern = re.compile(r'https?://[^\s]+')
        
    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s@.\-+()#]', ' ', text)
        text = ' '.join(text.split())
        
        return text.strip()
    
    def extract_contact_info(self, text: str) -> Dict[str, List[str]]:
        contacts = {
            'emails': [],
            'phones': [],
            'urls': []
        }
        
        emails = self.email_pattern.findall(text)
        contacts['emails'] = list(set(emails))
        
        phones = self.phone_pattern.findall(text)
        contacts['phones'] = list(set(phones))
        
        urls = self.url_pattern.findall(text)
        contacts['urls'] = list(set(urls))
        
        return contacts
    
    def split_into_sections(self, text: str) -> Dict[str, str]:
        sections = {
            'personal_info': '',
            'experience': '',
            'education': '',
            'skills': '',
            'other': ''
        }
        
        section_keywords = {
            'experience': ['опыт работы', 'experience', 'работа', 'карьера', 'должность'],
            'education': ['образование', 'education', 'университет', 'институт'],
            'skills': ['навыки', 'skills', 'умения', 'технологии']
        }
        
        lines = text.split('\n')
        current_section = 'other'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            for section, keywords in section_keywords.items():
                if any(keyword in line_lower for keyword in keywords):
                    current_section = section
                    break
            
            if sections[current_section]:
                sections[current_section] += '\n' + line
            else:
                sections[current_section] = line
        
        return sections
    
    def extract_years_of_experience(self, text: str) -> int:
        experience_patterns = [
            r'(\d+)\s*(?:лет|года|год)\s*(?:опыта|стажа)',
            r'(\d+)\+?\s*(?:years?)\s*(?:of\s*)?(?:experience|exp)',
        ]
        
        text_lower = text.lower()
        max_years = 0
        
        for pattern in experience_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    years = int(match)
                    if 0 <= years <= 50:
                        max_years = max(max_years, years)
                except ValueError:
                    continue
        
        return max_years
    
    def normalize_text_for_embedding(self, text: str) -> str:
        text = self.clean_text(text)
        text = self.email_pattern.sub('', text)
        text = self.phone_pattern.sub('', text)
        text = self.url_pattern.sub('', text)
        text = ' '.join(text.split())
        
        return text
