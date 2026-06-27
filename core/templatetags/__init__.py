"""Template tags and filters для приложения core."""
from django import template

register = template.Library()


@register.filter
def ai_score_color(score):
    """Возвращает CSS-класс Bootstrap на основе AI-score (0..1)."""
    try:
        score = float(score)
    except (TypeError, ValueError):
        return 'secondary'
    if score >= 0.8:
        return 'success'
    if score >= 0.6:
        return 'warning'
    if score >= 0.4:
        return 'info'
    return 'danger'