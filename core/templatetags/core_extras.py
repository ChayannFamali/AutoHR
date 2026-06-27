"""Custom template filters и inclusion tags для core. Импортируется как `{% load core_extras %}`."""
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


@register.filter
def times(value):
    """Повторить блок N раз: {% for i in 3|times %}...{% endfor %}"""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return []
    return range(n)


@register.inclusion_tag('core/partials/save_button.html', takes_context=True)
def show_save_button(context, job):
    """Inclusion-tag: рендерит кнопку «В избранное» с правильным состоянием.

    Ожидает в context:
      - user (request.user)
      - saved_job_ids (set/list id вакансий в избранном) — опц., для массовых списков
      - is_saved (bool) — если уже вычислен (например, на детальной странице)
    """
    user = context.get('user')
    is_saved = context.get('is_saved')

    if is_saved is None:
        saved_ids = context.get('saved_job_ids') or set()
        is_saved = job.id in saved_ids

    return {
        'job': job,
        'is_saved': bool(is_saved),
        'user': user,
        'csrf_token': context.get('csrf_token'),
    }
