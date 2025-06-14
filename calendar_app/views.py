from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q  # если еще не добавлен
from django.http import JsonResponse  # если еще не добавлен
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from core.models import Application

from .forms import ScheduleInterviewForm
from .models import Interview, InterviewTimeSlot, InterviewType

User = get_user_model()
import json
from datetime import datetime, timezone

from django.contrib import messages
# calendar_app/views.py
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from core.utils import can_manage_applications

from .models import Interview


@login_required
def interview_list(request):
    """Список всех собеседований"""
    
    # Фильтруем собеседования в зависимости от роли
    if request.user.is_hr() or request.user.is_admin_user():
        interviews = Interview.objects.select_related(
            'candidate', 'interviewer', 'application__job'
        ).order_by('scheduled_at')
    else:
        # Кандидаты видят только свои собеседования
        interviews = Interview.objects.filter(
            candidate__user=request.user
        ).select_related('interviewer', 'application__job').order_by('scheduled_at')
    
    # Применяем фильтры
    status_filter = request.GET.get('status')
    if status_filter:
        interviews = interviews.filter(status=status_filter)
    
    date_filter = request.GET.get('date')
    if date_filter:
        interviews = interviews.filter(scheduled_at__date=date_filter)
    
    context = {
        'interviews': interviews,
        'can_manage_interviews': can_manage_applications(request.user),
        'is_candidate': request.user.is_candidate(),
    }
    
    return render(request, 'calendar_app/interview_list.html', context)
@login_required
@require_http_methods(["POST"])
def save_interview_feedback(request, interview_id):
    try:
        interview = get_object_or_404(Interview, id=interview_id)
        data = json.loads(request.body)
        
        interview.feedback = data.get('feedback', '')
        interview.rating = data.get('rating', None)
        interview.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Отзыв сохранен'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def update_interview_status(request, interview_id):
    """Обновление статуса собеседования"""
    
    if not can_manage_applications(request.user):
        return JsonResponse({
            'success': False,
            'message': 'У вас нет прав для управления собеседованиями'
        })
    
    try:
        interview = get_object_or_404(Interview, id=interview_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status not in ['scheduled', 'confirmed', 'completed', 'cancelled', 'rescheduled']:
            return JsonResponse({
                'success': False,
                'message': 'Неверный статус'
            })
        
        interview.status = new_status
        interview.save()
        
        # Обновляем статус заявки при необходимости
        if new_status == 'completed':
            interview.application.status = 'interviewed'
            interview.application.save()
        elif new_status == 'cancelled':
            interview.application.status = 'pending'
            interview.application.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Статус собеседования обновлен: {interview.get_status_display()}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def reschedule_interview(request, interview_id):
    """Перенос собеседования"""
    
    if not can_manage_applications(request.user):
        return JsonResponse({
            'success': False,
            'message': 'У вас нет прав для переноса собеседований'
        })
    
    try:
        interview = get_object_or_404(Interview, id=interview_id)
        
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        reason = request.POST.get('reason', '')
        
        if not date_str or not time_str:
            return JsonResponse({
                'success': False,
                'message': 'Укажите новые дату и время'
            })
        
        # Парсим новую дату и время
        try:
            new_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            new_datetime = new_datetime.replace(tzinfo=timezone.utc)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Неверный формат даты или времени'
            })
        
        # Проверяем, что дата в будущем
        if new_datetime <= datetime.now(timezone.utc):
            return JsonResponse({
                'success': False,
                'message': 'Новая дата должна быть в будущем'
            })
        
        # Сохраняем старую дату для истории
        old_datetime = interview.scheduled_at
        
        # Обновляем собеседование
        interview.scheduled_at = new_datetime
        interview.status = 'rescheduled'
        if reason:
            interview.notes = f"Перенесено с {old_datetime.strftime('%d.%m.%Y %H:%M')}. Причина: {reason}"
        interview.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Собеседование перенесено на {new_datetime.strftime("%d.%m.%Y в %H:%M")}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })

@login_required
@require_http_methods(["POST"])
def add_interview_notes(request, interview_id):
    """Добавление заметок к собеседованию"""
    
    if not can_manage_applications(request.user):
        return JsonResponse({
            'success': False,
            'message': 'У вас нет прав для добавления заметок'
        })
    
    try:
        interview = get_object_or_404(Interview, id=interview_id)
        data = json.loads(request.body)
        notes = data.get('notes', '').strip()
        
        if not notes:
            return JsonResponse({
                'success': False,
                'message': 'Заметка не может быть пустой'
            })
        
        # Добавляем заметку с временной меткой
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
        user_name = request.user.get_full_name() or request.user.username
        new_note = f"[{timestamp}] {user_name}: {notes}"
        
        if interview.notes:
            interview.notes = f"{interview.notes}\n\n{new_note}"
        else:
            interview.notes = new_note
        
        interview.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Заметка добавлена',
            'notes': interview.notes
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })

@login_required
def schedule_interview(request):
    if request.method == 'POST':
        form = ScheduleInterviewForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                interview = form.save()
                
                # Обновляем статус заявки
                application = interview.application
                if application.status == 'pending':
                    application.status = 'approved'
                    application.save()
                
                # Отправляем уведомления
                try:
                    from notifications.services import NotificationService

                    # Уведомление кандидату о назначенном собеседовании
                    NotificationService.send_interview_scheduled(interview)
                    
                    # Уведомление HR о созданном собеседовании
                    hr_message = f'Собеседование запланировано:\n\n'
                    hr_message += f'Кандидат: {interview.candidate.full_name}\n'
                    hr_message += f'Вакансия: {interview.application.job.title}\n'
                    hr_message += f'Дата: {interview.scheduled_at.strftime("%d.%m.%Y %H:%M")}\n'
                    hr_message += f'Интервьюер: {interview.interviewer.get_full_name()}\n'
                    hr_message += f'Формат: {interview.get_format_display()}\n'
                    if interview.location:
                        hr_message += f'Место: {interview.location}\n'
                    
                    NotificationService.send_hr_notification(
                        'Собеседование запланировано',
                        hr_message,
                        interview.application.job.created_by.email
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомлений: {e}")
                
                messages.success(request, f'Собеседование с {interview.candidate.full_name} успешно запланировано! Уведомления отправлены.')
                
                # Если AJAX запрос
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Собеседование успешно запланировано!',
                        'redirect': '/calendar/interviews/'
                    })
                
                return redirect('calendar_app:interview_list')
                
            except Exception as e:
                error_msg = f'Ошибка при планировании собеседования: {str(e)}'
                messages.error(request, error_msg)
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_msg
                    })
        else:
            error_msg = 'Пожалуйста, исправьте ошибки в форме.'
            messages.error(request, error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_msg,
                    'errors': form.errors
                })
    
    return redirect('calendar_app:interview_list')


@method_decorator(login_required, name='dispatch')
class InterviewListView(ListView):
    model = Interview
    template_name = 'calendar_app/interview_list.html'
    context_object_name = 'interviews'
    paginate_by = 20
    
    def get_queryset(self):
        return Interview.objects.select_related(
            'candidate', 'interviewer', 'application__job', 'interview_type'
        ).order_by('scheduled_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['interview_types'] = InterviewType.objects.filter(is_active=True)
        context['pending_applications'] = Application.objects.filter(
            status__in=['approved', 'pending']
        ).select_related('candidate', 'job')
        context['interviewers'] = User.objects.filter(is_staff=True)
        return context



@login_required
def interview_detail(request, pk):
    interview = get_object_or_404(Interview, pk=pk)
    return render(request, 'calendar_app/interview_detail.html', {'interview': interview})

# @login_required
# def interview_calendar(request):
#     interviews = Interview.objects.filter(
#         interviewer=request.user,
#         status__in=['scheduled', 'confirmed']
#     ).select_related('candidate').order_by('scheduled_at')
    
#     return render(request, 'calendar_app/interview_calendar.html', {'interviews': interviews})


@login_required
def interview_calendar(request):
    interviews = Interview.objects.filter(
        interviewer=request.user,
        status__in=['scheduled', 'confirmed']
    ).select_related('candidate').order_by('scheduled_at')
    # Данные для модального окна
    interview_types = InterviewType.objects.filter(is_active=True)
    pending_applications = Application.objects.filter(
        status__in=['approved', 'pending']
    ).select_related('candidate', 'job')
    interviewers = User.objects.filter(is_staff=True)
    
    context = {
        'interviews': interviews,
        'interview_types': interview_types,
        'pending_applications': pending_applications,
        'interviewers': interviewers,
    }
    
    return render(request, 'calendar_app/interview_calendar.html', context)
