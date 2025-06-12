from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from core.models import Application

from .forms import ResumeUploadForm
from .models import Resume


def upload_resume(request, application_id=None):
    application = None
    if application_id:
        application = get_object_or_404(Application, id=application_id)
    
    if request.method == 'POST':
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            if application:
                resume.candidate = application.candidate
                resume.application = application
            resume.save()
            
            messages.success(request, 'Резюме успешно загружено!')
            if application:
                return redirect('core:application_list')
            return redirect('resume:resume_list')
    else:
        form = ResumeUploadForm()
    
    return render(request, 'resume/upload_resume.html', {
        'form': form,
        'application': application
    })

def resume_list(request):
    resumes = Resume.objects.select_related('candidate').order_by('-uploaded_at')
    return render(request, 'resume/resume_list.html', {'resumes': resumes})

def resume_detail(request, pk):
    resume = get_object_or_404(Resume, pk=pk)
    return render(request, 'resume/resume_detail.html', {'resume': resume})
