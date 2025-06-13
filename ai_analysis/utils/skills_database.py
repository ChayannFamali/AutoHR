"""
База данных навыков и технологий для извлечения из резюме
"""

PROGRAMMING_LANGUAGES = {
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
    'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash', 'powershell',
    'пайтон', 'джава', 'джаваскрипт', 'си++', 'си шарп', 'пхп', 'руби'
}

FRAMEWORKS_LIBRARIES = {
    'django', 'flask', 'fastapi', 'react', 'vue', 'angular', 'node.js', 'express',
    'spring', 'hibernate', 'laravel', 'symfony', 'rails', 'asp.net', 'jquery',
    'bootstrap', 'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy',
    'реакт', 'ангуляр', 'джанго', 'фласк'
}

DATABASES = {
    'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite', 'oracle',
    'sql server', 'cassandra', 'dynamodb', 'clickhouse', 'influxdb',
    'постгрес', 'постгресql', 'монго', 'редис', 'оракл'
}

TOOLS_TECHNOLOGIES = {
    'git', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'github', 'jira', 'confluence',
    'aws', 'azure', 'gcp', 'terraform', 'ansible', 'vagrant', 'nginx', 'apache',
    'linux', 'ubuntu', 'centos', 'windows', 'macos', 'vim', 'vscode', 'intellij',
    'гит', 'докер', 'кубернетес', 'линукс', 'убунту'
}

SOFT_SKILLS = {
    'leadership', 'teamwork', 'communication', 'problem solving', 'analytical thinking',
    'project management', 'time management', 'creativity', 'adaptability', 'mentoring',
    'лидерство', 'командная работа', 'коммуникация', 'решение проблем', 'аналитическое мышление',
    'управление проектами', 'управление временем', 'креативность', 'адаптивность', 'наставничество'
}

INDUSTRY_SKILLS = {
    'machine learning', 'data science', 'artificial intelligence', 'blockchain',
    'cybersecurity', 'devops', 'mobile development', 'web development', 'game development',
    'ui/ux design', 'product management', 'business analysis', 'quality assurance',
    'машинное обучение', 'наука о данных', 'искусственный интеллект', 'блокчейн',
    'кибербезопасность', 'девопс', 'мобильная разработка', 'веб разработка', 'тестирование'
}

# Объединенный словарь всех навыков
ALL_SKILLS = {
    'programming_languages': PROGRAMMING_LANGUAGES,
    'frameworks_libraries': FRAMEWORKS_LIBRARIES,
    'databases': DATABASES,
    'tools_technologies': TOOLS_TECHNOLOGIES,
    'soft_skills': SOFT_SKILLS,
    'industry_skills': INDUSTRY_SKILLS
}

# Плоский список всех навыков для быстрого поиска
SKILLS_SET = set()
for category_skills in ALL_SKILLS.values():
    SKILLS_SET.update(category_skills)

def get_skill_category(skill: str) -> str:
    """
    Определяет категорию навыка
    
    Args:
        skill: Название навыка
        
    Returns:
        str: Категория навыка
    """
    skill_lower = skill.lower()
    
    for category, skills in ALL_SKILLS.items():
        if skill_lower in skills:
            return category
    
    return 'other'

def normalize_skill(skill: str) -> str:
    """
    Нормализует название навыка
    
    Args:
        skill: Исходное название
        
    Returns:
        str: Нормализованное название
    """
    # Словарь для нормализации
    normalization_map = {
        'js': 'javascript',
        'ts': 'typescript',
        'пайтон': 'python',
        'джава': 'java',
        'джаваскрипт': 'javascript',
        'реакт': 'react',
        'ангуляр': 'angular',
        'джанго': 'django',
        'фласк': 'flask',
        'постгрес': 'postgresql',
        'монго': 'mongodb',
        'редис': 'redis',
        'гит': 'git',
        'докер': 'docker',
        'линукс': 'linux'
    }
    
    skill_lower = skill.lower().strip()
    return normalization_map.get(skill_lower, skill_lower)
