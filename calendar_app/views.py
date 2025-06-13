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
