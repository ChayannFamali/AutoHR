import openpyxl
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView
from openpyxl.styles import Alignment, Font, PatternFill

from notifications.services import NotificationService

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
            try:
                # Создаем или получаем кандидата
                candidate, created = Candidate.objects.get_or_create(
                    email=form.cleaned_data['email'],
                    defaults={
                        'first_name': form.cleaned_data['first_name'],
                        'last_name': form.cleaned_data['last_name'],
                        'phone': form.cleaned_data.get('phone', ''),
                    }
                )
                
                # Проверяем, не подавал ли уже заявку
                existing_application = Application.objects.filter(
                    candidate=candidate,
                    job=job
                ).first()
                
                if existing_application:
                    messages.warning(request, 'Вы уже подавали заявку на эту вакансию.')
                    return redirect('core:job_detail', pk=job.id)
                
                # Создаем заявку
                application = Application.objects.create(
                    candidate=candidate,
                    job=job,
                    cover_letter=form.cleaned_data.get('cover_letter', ''),
                    status='pending'
                )
                
                # Отправляем уведомления
                try:
                    from notifications.services import NotificationService

                    # Уведомление кандидату
                    NotificationService.send_application_confirmation(application)
                    
                    # Уведомление HR
                    hr_message = f'Новая заявка от {candidate.full_name} на вакансию "{job.title}"\n\n'
                    hr_message += f'Email кандидата: {candidate.email}\n'
                    hr_message += f'Телефон: {candidate.phone or "Не указан"}\n'
                    hr_message += f'Дата подачи: {application.applied_at.strftime("%d.%m.%Y %H:%M")}\n\n'
                    if application.cover_letter:
                        hr_message += f'Сопроводительное письмо:\n{application.cover_letter}'
                    
                    NotificationService.send_hr_notification(
                        'Новая заявка',
                        hr_message,
                        job.created_by.email
                    )
                except Exception as e:
                    print(f"Ошибка отправки уведомлений: {e}")
                
                messages.success(request, 'Ваша заявка успешно отправлена! Теперь вы можете загрузить резюме.')
                return redirect('resume:upload_resume_for_application', application_id=application.id)
                
            except Exception as e:
                messages.error(request, f'Произошла ошибка при отправке заявки: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
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
