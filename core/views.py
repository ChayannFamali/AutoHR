from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import CreateView, DetailView, ListView

from .forms import ApplicationForm
from .models import Application, Candidate, Job


class JobListView(ListView):
    model = Job
    template_name = 'core/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10
    
    def get_queryset(self):
        return Job.objects.filter(status='active').select_related('company')

class JobDetailView(DetailView):
    model = Job
    template_name = 'core/job_detail.html'
    context_object_name = 'job'
    
    def get_queryset(self):
        return Job.objects.filter(status='active').select_related('company')

def apply_for_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, status='active')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            # Создаем или получаем кандидата
            candidate, created = Candidate.objects.get_or_create(
                email=form.cleaned_data['email'],
                defaults={
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'phone': form.cleaned_data.get('phone', ''),
                }
            )
            
            # Создаем заявку
            application, created = Application.objects.get_or_create(
                candidate=candidate,
                job=job,
                defaults={
                    'cover_letter': form.cleaned_data.get('cover_letter', ''),
                }
            )
            
            if created:
                messages.success(request, 'Ваша заявка успешно отправлена!')
                return redirect('core:job_detail', pk=job.id)
            else:
                messages.warning(request, 'Вы уже подавали заявку на эту вакансию.')
    else:
        form = ApplicationForm()
    
    return render(request, 'core/apply_job.html', {'job': job, 'form': form})

class ApplicationListView(ListView):
    model = Application
    template_name = 'core/application_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        return Application.objects.select_related('candidate', 'job', 'job__company').order_by('-applied_at')
