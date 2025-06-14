import json
from collections import Counter
from datetime import datetime, timedelta

from django.db.models import Avg, Count, Q
from django.http import JsonResponse
# Create your views here.
from django.shortcuts import render
from django.utils import timezone

from calendar_app.models import Interview
from core.models import Application, Job
from resume.models import Resume


def analytics_dashboard(request):
    """Главная страница аналитики"""
    # Основные метрики
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
    
    # Группируем заявки по дням
    applications = Application.objects.filter(
        applied_at__date__gte=start_date,
        applied_at__date__lte=end_date
    ).extra(
        select={'day': 'date(applied_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Создаем полный список дат
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Заполняем данные
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
    
    # Группируем по диапазонам
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
    
    # Собираем все навыки
    all_skills = []
    for skills_list in resumes:
        if skills_list:
            all_skills.extend(skills_list)
    
    # Подсчитываем частоту
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
