import openpyxl
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView
from openpyxl.styles import Alignment, Font, PatternFill

from .forms import ApplicationForm
from .models import Application, Candidate, Job


def export_applications_excel(request):
    # Создаем новую книгу Excel
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = 'Заявки кандидатов'
    
    # Заголовки столбцов
    headers = [
        'ID', 'Кандидат', 'Email', 'Телефон', 'Вакансия', 'Компания', 
        'AI Оценка', 'Статус', 'Дата подачи', 'Сопроводительное письмо'
    ]
    
    # Записываем заголовки
    for col_num, header in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.value = header
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
        cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
    
    # Получаем данные заявок
    applications = Application.objects.select_related(
        'candidate', 'job', 'job__company'
    ).order_by('-applied_at')
    
    # Записываем данные
    for row_num, application in enumerate(applications, 2):
        worksheet.cell(row=row_num, column=1, value=application.id)
        worksheet.cell(row=row_num, column=2, value=application.candidate.full_name)
        worksheet.cell(row=row_num, column=3, value=application.candidate.email)
        worksheet.cell(row=row_num, column=4, value=application.candidate.phone or '-')
        worksheet.cell(row=row_num, column=5, value=application.job.title)
        worksheet.cell(row=row_num, column=6, value=application.job.company.name)
        worksheet.cell(row=row_num, column=7, value=application.ai_score or '-')
        worksheet.cell(row=row_num, column=8, value=application.get_status_display())
        worksheet.cell(row=row_num, column=9, value=application.applied_at.strftime('%d.%m.%Y %H:%M'))
        worksheet.cell(row=row_num, column=10, value=application.cover_letter[:100] + '...' if len(application.cover_letter) > 100 else application.cover_letter)
    
    # Автоподбор ширины столбцов
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # Создаем HTTP ответ с Excel файлом
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="applications_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    
    workbook.save(response)
    return response

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
