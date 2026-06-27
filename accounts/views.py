from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from core.forms import EducationForm, SkillForm, WorkExperienceForm
from core.models import Candidate, Education, Skill, WorkExperience
from core.ratelimit import rate_limit, rate_limit_class

from .forms import (CandidateRegistrationForm, CustomLoginForm,
                    HRRegistrationForm, UserProfileForm)
from .models import User, UserProfile


@rate_limit_class(key='login', limit=10, period=60)
class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'accounts/login.html'

    def get_success_url(self):
        user = self.request.user
        if user.is_hr():
            return reverse_lazy('core:application_list')
        elif user.is_candidate():
            return reverse_lazy('core:job_list')
        else:
            return reverse_lazy('admin:index')


@rate_limit_class(key='register_hr', limit=5, period=300)
class HRRegistrationView(CreateView):
    form_class = HRRegistrationForm
    template_name = 'accounts/register_hr.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Регистрация успешна! Войдите в систему.')
        return response


@rate_limit_class(key='register_candidate', limit=5, period=300)
class CandidateRegistrationView(CreateView):
    form_class = CandidateRegistrationForm
    template_name = 'accounts/register_candidate.html'
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Регистрация успешна! Войдите в систему.')
        return response


def register_choice(request):
    """Выбор типа регистрации"""
    return render(request, 'accounts/register_choice.html')


@login_required
def profile_view(request):
    """Просмотр профиля пользователя (Этап 3.2 — табы)."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    candidate = Candidate.objects.filter(user=request.user).first()

    work_experiences = candidate.work_experiences.all() if candidate else []
    educations = candidate.educations.all() if candidate else []
    skills = candidate.skills.all() if candidate else []

    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'candidate': candidate,
        'work_experiences': work_experiences,
        'educations': educations,
        'skills': skills,
    })


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form})


def _get_candidate_for(user):
    """Хелпер: возвращает Candidate пользователя или None."""
    return Candidate.objects.filter(user=user).first()


@login_required
def add_work_experience(request):
    """Добавить место работы."""
    candidate = _get_candidate_for(request.user)
    if not candidate:
        messages.error(request, 'Сначала заполните профиль кандидата.')
        return redirect('accounts:profile_edit')

    if request.method == 'POST':
        form = WorkExperienceForm(request.POST)
        if form.is_valid():
            we = form.save(commit=False)
            we.candidate = candidate
            we.save()
            messages.success(request, 'Опыт работы добавлен.')
            return redirect('accounts:profile')
    else:
        form = WorkExperienceForm()
    return render(request, 'accounts/work_experience_form.html', {
        'form': form, 'candidate': candidate,
    })


@login_required
def edit_work_experience(request, we_id):
    """Редактировать место работы."""
    we = get_object_or_404(WorkExperience, id=we_id, candidate__user=request.user)

    if request.method == 'POST':
        form = WorkExperienceForm(request.POST, instance=we)
        if form.is_valid():
            form.save()
            messages.success(request, 'Опыт работы обновлён.')
            return redirect('accounts:profile')
    else:
        form = WorkExperienceForm(instance=we)
    return render(request, 'accounts/work_experience_form.html', {
        'form': form, 'we': we,
    })


@login_required
def delete_work_experience(request, we_id):
    """Удалить место работы."""
    we = get_object_or_404(WorkExperience, id=we_id, candidate__user=request.user)
    if request.method == 'POST':
        we.delete()
        messages.success(request, 'Опыт работы удалён.')
    return redirect('accounts:profile')


@login_required
def add_education(request):
    """Добавить образование."""
    candidate = _get_candidate_for(request.user)
    if not candidate:
        messages.error(request, 'Сначала заполните профиль кандидата.')
        return redirect('accounts:profile_edit')

    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            ed = form.save(commit=False)
            ed.candidate = candidate
            ed.save()
            messages.success(request, 'Образование добавлено.')
            return redirect('accounts:profile')
    else:
        form = EducationForm()
    return render(request, 'accounts/education_form.html', {
        'form': form, 'candidate': candidate,
    })


@login_required
def edit_education(request, ed_id):
    """Редактировать образование."""
    ed = get_object_or_404(Education, id=ed_id, candidate__user=request.user)

    if request.method == 'POST':
        form = EducationForm(request.POST, instance=ed)
        if form.is_valid():
            form.save()
            messages.success(request, 'Образование обновлено.')
            return redirect('accounts:profile')
    else:
        form = EducationForm(instance=ed)
    return render(request, 'accounts/education_form.html', {
        'form': form, 'ed': ed,
    })


@login_required
def delete_education(request, ed_id):
    """Удалить образование."""
    ed = get_object_or_404(Education, id=ed_id, candidate__user=request.user)
    if request.method == 'POST':
        ed.delete()
        messages.success(request, 'Образование удалено.')
    return redirect('accounts:profile')


@login_required
def add_skill(request):
    """Добавить навык."""
    candidate = _get_candidate_for(request.user)
    if not candidate:
        messages.error(request, 'Сначала заполните профиль кандидата.')
        return redirect('accounts:profile_edit')

    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Skill.objects.filter(candidate=candidate, name=name).exists():
                messages.warning(
                    request,
                    f'Навык «{name}» уже есть в профиле.',
                )
            else:
                sk = form.save(commit=False)
                sk.candidate = candidate
                sk.save()
                messages.success(request, f'Навык «{sk.name}» добавлен.')
            return redirect('accounts:profile')
    else:
        form = SkillForm()
    return render(request, 'accounts/skill_form.html', {
        'form': form, 'candidate': candidate,
    })


@login_required
def delete_skill(request, skill_id):
    """Удалить навык."""
    sk = get_object_or_404(Skill, id=skill_id, candidate__user=request.user)
    if request.method == 'POST':
        sk.delete()
        messages.success(request, 'Навык удалён.')
    return redirect('accounts:profile')


class CustomLogoutView(LogoutView):
    template_name = 'accounts/logout.html'
