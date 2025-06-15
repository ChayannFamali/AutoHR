import json
from venv import logger

import openpyxl
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView
from openpyxl.styles import Alignment, Font, PatternFill

from accounts.decorators import hr_required
from notifications.services import NotificationService
from resume.models import Resume

from .forms import ApplicationForm, JobCreateForm
from .models import Application, Candidate, Job
from .utils import (can_export_data, can_manage_applications,
                    can_view_sensitive_data)


@login_required
@require_http_methods(["POST"])
def add_note_to_application(request, application_id):
    # Только HR и админы могут добавлять заметки
    if not can_manage_applications(request.user):
        return JsonResponse({
            'success': False,
            'message': 'У вас нет прав для добавления заметок'
        })
    try:
        application = get_object_or_404(Application, id=application_id)
        
        data = json.loads(request.body)
        note_text = data.get('note', '').strip()
        
        if not note_text:
            return JsonResponse({
                'success': False,
                'message': 'Заметка не может быть пустой'
            })
        
        # Добавляем заметку к существующим заметкам
        current_notes = application.notes or ""
        timestamp = timezone.now().strftime("%d.%m.%Y %H:%M")
        new_note = f"[{timestamp}] {request.user.get_full_name() or request.user.username}: {note_text}"
        
        if current_notes:
            application.notes = f"{current_notes}\n\n{new_note}"
        else:
            application.notes = new_note
            
        application.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Заметка успешно добавлена',
            'notes': application.notes
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при добавлении заметки: {str(e)}'
        })
        
        
@hr_required
@require_POST
def update_application_status(request, application_id):
    """Обновление статуса заявки"""
    try:
        application = get_object_or_404(Application, id=application_id)
        data = json.loads(request.body)
        new_status = data.get('status')
        
        if new_status in ['approved', 'rejected']:
            application.status = new_status
            application.save()
            
            status_text = 'одобрена' if new_status == 'approved' else 'отклонена'
            
            return JsonResponse({
                'success': True,
                'message': f'Заявка {status_text}',
                'new_status': application.get_status_display()
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Неверный статус'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })

@hr_required
@login_required
@require_http_methods(["POST"])
def schedule_interview_for_application(request, application_id):
    """Быстрое планирование собеседования"""
    
    if not can_manage_applications(request.user):
        return JsonResponse({
            'success': False,
            'message': 'У вас нет прав для планирования собеседований'
        })
    
    try:
        application = get_object_or_404(Application, id=application_id)
        
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        format_type = request.POST.get('format')
        location = request.POST.get('location', '')
        
        if not all([date_str, time_str, format_type]):
            return JsonResponse({
                'success': False,
                'message': 'Заполните все обязательные поля (дата, время, формат)'
            })
        
        from datetime import datetime, timezone
        try:
            scheduled_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            scheduled_datetime = scheduled_datetime.replace(tzinfo=timezone.utc)
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Неверный формат даты или времени'
            })
        
        # Проверяем, что дата в будущем
        if scheduled_datetime <= datetime.now(timezone.utc):
            return JsonResponse({
                'success': False,
                'message': 'Дата собеседования должна быть в будущем'
            })
        
        from calendar_app.models import Interview, InterviewType

        # Получаем или создаем дефолтный тип собеседования
        interview_type, created = InterviewType.objects.get_or_create(
            name='Стандартное собеседование',
            defaults={
                'duration_minutes': 60,
                'is_active': True,
                'description': 'Стандартное собеседование с кандидатом'
            }
        )
        
        if created:
            print(f"Создан новый тип собеседования: {interview_type.name}")
        
        interview = Interview.objects.create(
            application=application,
            candidate=application.candidate,
            interviewer=request.user,
            interview_type=interview_type,
            scheduled_at=scheduled_datetime,
            format=format_type,
            location=location,
            status='scheduled',
            duration_minutes=interview_type.duration_minutes
        )
        
        application.status = 'approved'
        application.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Собеседование запланировано на {scheduled_datetime.strftime("%d.%m.%Y в %H:%M")}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка: {str(e)}'
        })



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
    
    for col_num, header in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.value = header
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
        cell.fill = PatternFill(start_color='CCCCCC', end_color='CCCCCC', fill_type='solid')
    
    applications = Application.objects.select_related(
        'candidate', 'job', 'job__company'
    ).order_by('-applied_at')
    
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

@hr_required
def create_job(request):
    """Создание новой вакансии"""
    if request.method == 'POST':
        form = JobCreateForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
            job.save()
            
            messages.success(request, f'Вакансия "{job.title}" успешно создана!')
            return redirect('core:job_detail', pk=job.id)
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = JobCreateForm()
    
    return render(request, 'core/create_job.html', {'form': form})

def job_list(request):
    """Список всех активных вакансий с фильтрами"""
    jobs = Job.objects.filter(status='active').select_related('company').order_by('-created_at')
    
    search_query = request.GET.get('search')
    if search_query:
        jobs = jobs.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(company__name__icontains=search_query)
        )
    
    experience_level = request.GET.get('experience_level')
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)
    
    remote_work = request.GET.get('remote_work')
    if remote_work:
        is_remote = remote_work == 'true'
        jobs = jobs.filter(remote_work=is_remote)
    
    location = request.GET.get('location')
    if location:
        jobs = jobs.filter(location__icontains=location)
    
    context = {
        'jobs': jobs,
        'search_query': search_query,
        'selected_experience': experience_level,
        'selected_remote': remote_work,
        'selected_location': location,
    }
    
    return render(request, 'core/job_list.html', context)

@login_required
@require_http_methods(["POST"])
def delete_job(request, job_id):
    """Удаление вакансии"""
    job = get_object_or_404(Job, id=job_id, created_by=request.user)
    
    try:
        job_title = job.title
        job.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Вакансия "{job_title}" успешно удалена'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Ошибка при удалении: {str(e)}'
        })

@hr_required
def job_list_hr(request):
    """Список вакансий для HR"""
    jobs = Job.objects.filter(created_by=request.user).order_by('-created_at')
    return render(request, 'core/job_list_hr.html', {'jobs': jobs})

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
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        return obj

def apply_for_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, status='active')
    
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            try:
                if request.user.is_authenticated and request.user.is_candidate():
                    candidate, created = Candidate.objects.get_or_create(
                        user=request.user,
                        defaults={
                            'first_name': form.cleaned_data['first_name'],
                            'last_name': form.cleaned_data['last_name'],
                            'email': form.cleaned_data['email'],
                            'phone': form.cleaned_data.get('phone', ''),
                        }
                    )
                    if not created:
                        candidate.first_name = form.cleaned_data['first_name']
                        candidate.last_name = form.cleaned_data['last_name']
                        candidate.email = form.cleaned_data['email']
                        candidate.phone = form.cleaned_data.get('phone', '')
                        candidate.save()
                else:
                    candidate, created = Candidate.objects.get_or_create(
                        email=form.cleaned_data['email'],
                        defaults={
                            'first_name': form.cleaned_data['first_name'],
                            'last_name': form.cleaned_data['last_name'],
                            'phone': form.cleaned_data.get('phone', ''),
                        }
                    )
                
                existing_application = Application.objects.filter(
                    candidate=candidate,
                    job=job
                ).first()
                
                if existing_application:
                    messages.warning(request, 'Вы уже подавали заявку на эту вакансию.')
                    return redirect('core:job_detail', pk=job.id)
                
                application = Application.objects.create(
                    candidate=candidate,
                    job=job,
                    cover_letter=form.cleaned_data.get('cover_letter', ''),
                    status='pending'
                )
                
                existing_resumes = Resume.objects.filter(
                    candidate=candidate,
                    status='processed'
                ).order_by('-uploaded_at')

                if existing_resumes.exists():
                    latest_resume = existing_resumes.first()
                    
                    try:
                        from ai_analysis.services.analysis_engine import \
                            AnalysisEngine
                        analysis_engine = AnalysisEngine()
                        
                        match_result = analysis_engine.match_candidate_with_job(
                            latest_resume.id, 
                            job.id
                        )
                        
                        if match_result['success']:
                            application.ai_score = match_result['overall_score']
                            application.ai_feedback = match_result['recommendation']
                            application.save()
                            
                            messages.success(
                                request, 
                                f'Заявка отправлена! AI оценка соответствия: {application.ai_score:.2f}'
                            )
                        else:
                            messages.success(request, 'Заявка отправлена! Загрузите резюме для AI-анализа.')
                    
                    except Exception as ai_error:
                        logger.error(f"AI matching error: {str(ai_error)}")
                        messages.success(request, 'Заявка отправлена! Загрузите резюме для AI-анализа.')
                else:
                    messages.success(request, 'Заявка отправлена! Загрузите резюме для AI-анализа.')

                try:
                    from notifications.services import NotificationService

                    # Уведомление кандидату
                    NotificationService.send_application_confirmation(application)
                    
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

                return redirect('resume:upload_resume_for_application', application_id=application.id)
                
            except Exception as e:
                messages.error(request, f'Произошла ошибка при отправке заявки: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = ApplicationForm()
    
    return render(request, 'core/apply_job.html', {'job': job, 'form': form})

class ApplicationListView(LoginRequiredMixin, ListView):
    model = Application
    template_name = 'core/application_list.html'
    context_object_name = 'applications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Application.objects.select_related('candidate', 'job', 'job__company').order_by('-applied_at')
        
        if self.request.user.is_candidate():
            try:
                candidate = Candidate.objects.get(user=self.request.user)
                queryset = queryset.filter(candidate=candidate)
            except Candidate.DoesNotExist:
                queryset = queryset.none()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        base_queryset = self.get_queryset()
        
        total_applications = base_queryset.count()
        pending_applications = base_queryset.filter(status='pending').count()
        approved_applications = base_queryset.filter(status='approved').count()
        
        context.update({
            'can_view_sensitive_data': can_view_sensitive_data(self.request.user),
            'can_manage_applications': can_manage_applications(self.request.user),
            'can_export_data': can_export_data(self.request.user),
            'is_candidate': self.request.user.is_candidate(),
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'approved_applications': approved_applications,
        })
        
        return context

@login_required
def application_detail(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    
    if request.user.is_candidate():
        try:
            candidate = Candidate.objects.get(user=request.user)
            if application.candidate != candidate:
                raise Http404("Заявка не найдена")
        except Candidate.DoesNotExist:
            raise Http404("Заявка не найдена")
    
    if request.method == 'GET':
        html = render_to_string('core/application_detail_modal.html', {
            'application': application,
            'can_view_sensitive_data': can_view_sensitive_data(request.user),
            'can_manage_applications': can_manage_applications(request.user),
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'html': html
        })


class JobEditView(LoginRequiredMixin, UpdateView):
    model = Job
    form_class = JobCreateForm
    template_name = 'core/edit_job.html'
    
    def get_queryset(self):
        # Пользователь может редактировать только свои вакансии
        return Job.objects.filter(created_by=self.request.user)
    
    def get_success_url(self):
        return reverse('core:job_list_hr')