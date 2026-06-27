"""Context processors для шаблонов AutoHR."""


def ai_flag(request):
    """Пробрасывает settings.AI_ENABLED во все шаблоны.

    Использование:
        {% if AI_ENABLED %}...{% endif %}
        {% if AI_ENABLED and application.ai_score is not None %}...{% endif %}
    """
    from django.conf import settings
    return {'AI_ENABLED': getattr(settings, 'AI_ENABLED', False)}