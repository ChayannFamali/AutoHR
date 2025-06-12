from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from .models import Interview, InterviewTimeSlot


@method_decorator(login_required, name='dispatch')
class InterviewListView(ListView):
    model = Interview
    template_name = 'calendar_app/interview_list.html'
    context_object_name = 'interviews'
    
    def get_queryset(self):
        return Interview.objects.select_related(
            'candidate', 'interviewer', 'application__job'
        ).order_by('scheduled_at')

@login_required
def interview_detail(request, pk):
    interview = get_object_or_404(Interview, pk=pk)
    return render(request, 'calendar_app/interview_detail.html', {'interview': interview})

@login_required
def interview_calendar(request):
    interviews = Interview.objects.filter(
        interviewer=request.user,
        status__in=['scheduled', 'confirmed']
    ).select_related('candidate').order_by('scheduled_at')
    
    return render(request, 'calendar_app/interview_calendar.html', {'interviews': interviews})
