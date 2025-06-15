from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import (CandidateRegistrationForm, CustomLoginForm,
                    HRRegistrationForm, UserProfileForm)
from .models import User, UserProfile


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

class HRRegistrationView(CreateView):
    form_class = HRRegistrationForm
    template_name = 'accounts/register_hr.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Регистрация успешна! Войдите в систему.')
        return response

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
    """Просмотр профиля пользователя"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'accounts/profile.html', {'profile': profile})


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


class CustomLogoutView(LogoutView):
    template_name = 'accounts/logout.html'
