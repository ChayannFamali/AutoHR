from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from core.models import Application

from .models import Interview, InterviewTimeSlot, InterviewType


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
        # Добавляем данные для модального окна
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
