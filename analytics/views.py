from collections import Counter
from datetime import datetime, timedelta

from django.db.models import Avg, Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from calendar_app.models import Interview
from core.models import Application, Company, Job
from resume.models import Resume


def analytics_dashboard(request):
    """Главная страница аналитики"""
    context = {
        'total_applications': Application.objects.count(),
        'total_resumes': Resume.objects.count(),
        'total_interviews': Interview.objects.count(),
        'total_jobs': Job.objects.filter(status='active').count(),
        'avg_ai_score': Application.objects.filter(ai_score__isnull=False).aggregate(
            avg_score=Avg('ai_score')
        )['avg_score'] or 0,
    }
    return render(request, 'analytics/dashboard.html', context)


def applications_chart_data(request):
    """Данные для графика заявок по дням"""
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)

    applications = Application.objects.filter(
        applied_at__date__gte=start_date,
        applied_at__date__lte=end_date
    ).extra(
        select={'day': 'date(applied_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')

    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)

    app_dict = {item['day']: item['count'] for item in applications}
    data = [app_dict.get(date, 0) for date in date_range]

    return JsonResponse({
        'labels': [datetime.strptime(date, '%Y-%m-%d').strftime('%d.%m') for date in date_range],
        'data': data
    })


def ai_scores_distribution(request):
    """Распределение AI-оценок"""
    scores = Application.objects.filter(
        ai_score__isnull=False
    ).values_list('ai_score', flat=True)

    ranges = {
        '0.0-0.2': 0,
        '0.2-0.4': 0,
        '0.4-0.6': 0,
        '0.6-0.8': 0,
        '0.8-1.0': 0
    }

    for score in scores:
        if score < 0.2:
            ranges['0.0-0.2'] += 1
        elif score < 0.4:
            ranges['0.2-0.4'] += 1
        elif score < 0.6:
            ranges['0.4-0.6'] += 1
        elif score < 0.8:
            ranges['0.6-0.8'] += 1
        else:
            ranges['0.8-1.0'] += 1

    return JsonResponse({
        'labels': list(ranges.keys()),
        'data': list(ranges.values())
    })


def popular_skills_data(request):
    """Топ популярных навыков"""
    resumes = Resume.objects.filter(
        skills__isnull=False,
        status='processed'
    ).values_list('skills', flat=True)

    all_skills = []
    for skills_list in resumes:
        if skills_list:
            all_skills.extend(skills_list)

    skill_counter = Counter(all_skills)
    top_skills = skill_counter.most_common(10)

    return JsonResponse({
        'labels': [skill[0] for skill in top_skills],
        'data': [skill[1] for skill in top_skills]
    })


def application_status_data(request):
    """Статистика по статусам заявок"""
    statuses = Application.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')

    status_names = {
        'pending': 'Ожидает',
        'processing': 'Обрабатывается',
        'approved': 'Одобрено',
        'rejected': 'Отклонено',
        'interviewed': 'Собеседование'
    }

    return JsonResponse({
        'labels': [status_names.get(item['status'], item['status']) for item in statuses],
        'data': [item['count'] for item in statuses]
    })


def interview_completion_rate(request):
    """Статистика завершения собеседований"""
    total_interviews = Interview.objects.count()
    if total_interviews == 0:
        return JsonResponse({'labels': [], 'data': []})

    statuses = Interview.objects.values('status').annotate(
        count=Count('id')
    )

    status_names = {
        'scheduled': 'Запланировано',
        'confirmed': 'Подтверждено',
        'completed': 'Завершено',
        'cancelled': 'Отменено',
        'no_show': 'Не явился'
    }

    return JsonResponse({
        'labels': [status_names.get(item['status'], item['status']) for item in statuses],
        'data': [item['count'] for item in statuses]
    })


def top_jobs_by_applications(request):
    """Топ вакансий по количеству заявок"""
    jobs = Job.objects.annotate(
        app_count=Count('application')
    ).filter(app_count__gt=0).order_by('-app_count')[:10]

    return JsonResponse({
        'labels': [f"{job.title[:30]}..." if len(job.title) > 30 else job.title for job in jobs],
        'data': [job.app_count for job in jobs]
    })


def resume_processing_stats(request):
    """Статистика обработки резюме"""
    statuses = Resume.objects.values('status').annotate(
        count=Count('id')
    )

    status_names = {
        'uploaded': 'Загружено',
        'processing': 'Обрабатывается',
        'processed': 'Обработано',
        'error': 'Ошибка'
    }

    return JsonResponse({
        'labels': [status_names.get(item['status'], item['status']) for item in statuses],
        'data': [item['count'] for item in statuses]
    })


def recruitment_funnel(request):
    """Воронка рекрутинга: просмотры → отклики → одобрено → интервью → отклонено."""
    total_views = Job.objects.aggregate(s=Sum('views_count'))['s'] or 0
    total_applications = Application.objects.count()
    approved = Application.objects.filter(status='approved').count()
    interviewed = Application.objects.filter(status='interviewed').count()
    rejected = Application.objects.filter(status='rejected').count()

    labels = ['Просмотры', 'Отклики', 'Одобрено', 'Интервью', 'Отклонено']
    data = [total_views, total_applications, approved, interviewed, rejected]

    return JsonResponse({'labels': labels, 'data': data})


def conversion_rates(request):
    """Конверсия между этапами воронки (в %)."""
    total_views = Job.objects.aggregate(s=Sum('views_count'))['s'] or 0
    total_applications = Application.objects.count()
    approved = Application.objects.filter(status='approved').count()
    interviewed = Application.objects.filter(status='interviewed').count()

    def pct(num, den):
        if den == 0:
            return 0.0
        return round(100.0 * num / den, 1)

    labels = ['Просмотр → Отклик', 'Отклик → Одобрено', 'Одобрено → Интервью']
    data = [
        pct(total_applications, total_views),
        pct(approved, total_applications),
        pct(interviewed, approved),
    ]
    return JsonResponse({'labels': labels, 'data': data})


def time_to_hire(request):
    """Средний time-to-hire (дни) для одобренных/прошедших интервью откликов."""
    from django.db.models import DurationField, ExpressionWrapper, F

    apps = Application.objects.filter(
        status__in=['approved', 'interviewed'],
        processed_at__isnull=False,
        applied_at__isnull=False,
    ).annotate(
        duration=ExpressionWrapper(
            F('processed_at') - F('applied_at'),
            output_field=DurationField(),
        ),
    )

    durations = [
        a.duration.total_seconds() / 86400.0
        for a in apps if a.duration is not None
    ]
    avg_days = round(sum(durations) / len(durations), 1) if durations else None

    return JsonResponse({
        'avg_days': avg_days,
        'sample_size': len(durations),
        'unit': 'days',
    })


def top_employers(request):
    """Топ компаний по количеству активных вакансий и откликов."""
    companies = Company.objects.annotate(
        apps_count=Count('job__application', distinct=True),
        jobs_count=Count(
            'job', filter=Q(job__status='active'), distinct=True,
        ),
    ).order_by('-apps_count')[:10]

    return JsonResponse({
        'labels': [c.name for c in companies],
        'jobs_data': [c.jobs_count for c in companies],
        'apps_data': [c.apps_count for c in companies],
    })