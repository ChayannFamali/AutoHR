"""AI-рекомендации вакансий (Этап 3.5, SKILL 6).

Использует уже посчитанные эмбеддинги `Job.requirements_embedding`.
При отсутствии эмбеддингов возвращает fallback по компании/уровню.
"""
import logging

from core.models import Job

logger = logging.getLogger(__name__)


def get_similar_jobs(job_id: int, top_n: int = 5):
    """Возвращает список похожих вакансий, отсортированных по убыванию similarity.

    Returns:
        list[(Job, float)]: пары (вакансия, similarity в диапазоне 0..1).
    """
    try:
        target = Job.objects.get(id=job_id, status='active')
    except Job.DoesNotExist:
        return []

    target_emb = target.requirements_embedding
    if not target_emb:
        return _fallback_similar(target, top_n)

    candidates = Job.objects.filter(
        status='active',
    ).exclude(id=target.id).exclude(
        requirements_embedding__isnull=True,
    )

    if not candidates.exists():
        return _fallback_similar(target, top_n)

    try:
        from .embedding_service import EmbeddingService
        svc = EmbeddingService.__new__(EmbeddingService)
        svc.model = None

        scored = []
        for cand in candidates:
            sim = svc.calculate_similarity(target_emb, cand.requirements_embedding)
            if sim > 0:
                scored.append((cand, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]
    except Exception as exc:
        logger.warning(
            'AI рекомендации: упал similarity (%s) — fallback на компанию/уровень',
            exc,
        )
        return _fallback_similar(target, top_n)


def _fallback_similar(target: Job, top_n: int):
    """Fallback без AI: по той же компании, потом по уровню опыта."""
    same_company = Job.objects.filter(
        status='active',
        company=target.company,
    ).exclude(id=target.id).order_by('-created_at')[:top_n]

    if same_company.count() >= top_n:
        return [(j, 0.5) for j in same_company]

    result = [(j, 0.5) for j in same_company]
    needed = top_n - len(result)
    if needed > 0:
        other = Job.objects.filter(
            status='active',
            experience_level=target.experience_level,
        ).exclude(id=target.id).exclude(
            id__in=[j.id for j in same_company],
        ).order_by('-created_at')[:needed]
        for j in other:
            result.append((j, 0.3))
    return result


def get_recommended_jobs_for_candidate(candidate, top_n: int = 5):
    """Рекомендации вакансий для кандидата (по навыкам профиля)."""
    if not candidate or not candidate.id:
        return []

    skills = list(candidate.skills.values_list('name', flat=True))
    if not skills:
        return Job.objects.filter(status='active').order_by('-created_at')[:top_n]

    from django.db.models import Q
    skill_q = Q()
    for skill in skills:
        skill_q |= Q(skills_required__icontains=f'"{skill}"')

    qs = Job.objects.filter(status='active').filter(skill_q)
    if qs.count() < top_n:
        extra_n = top_n - qs.count()
        extra = Job.objects.filter(status='active').exclude(
            id__in=qs.values_list('id', flat=True),
        ).order_by('-created_at')[:extra_n]
        result = list(qs) + list(extra)
    else:
        result = list(qs[:top_n])
    return result
