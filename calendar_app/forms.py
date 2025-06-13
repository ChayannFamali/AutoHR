from django import forms
from django.contrib.auth.models import User

from core.models import Application

from .models import Interview, InterviewType


class ScheduleInterviewForm(forms.ModelForm):
    application = forms.ModelChoiceField(
        queryset=Application.objects.filter(status__in=['approved', 'pending']),
        empty_label="Выберите заявку",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    interview_type = forms.ModelChoiceField(
        queryset=InterviewType.objects.filter(is_active=True),
        empty_label="Выберите тип",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    interviewer = forms.ModelChoiceField(
        queryset=None,
        empty_label="Выберите интервьюера",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    scheduled_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    scheduled_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    
    class Meta:
        model = Interview
        fields = ['application', 'interview_type', 'interviewer', 'format', 'location', 'preparation_notes']
        widgets = {
            'format': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Адрес или ссылка'}),
            'preparation_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['interviewer'].queryset = User.objects.filter(is_staff=True)
        if user:
            self.fields['interviewer'].initial = user
        
        # Добавляем описания к полям
        self.fields['application'].help_text = "Выберите заявку кандидата"
        self.fields['location'].help_text = "Укажите адрес офиса или ссылку на видеоконференцию"
    
    def save(self, commit=True):
        interview = super().save(commit=False)
        
        # Объединяем дату и время
        scheduled_date = self.cleaned_data['scheduled_date']
        scheduled_time = self.cleaned_data['scheduled_time']
        
        from datetime import datetime
        from datetime import timezone as tz
        interview.scheduled_at = datetime.combine(scheduled_date, scheduled_time).replace(tzinfo=tz.utc)
        
        # Устанавливаем кандидата из заявки
        interview.candidate = self.cleaned_data['application'].candidate
        
        # Устанавливаем длительность из типа собеседования
        interview.duration_minutes = self.cleaned_data['interview_type'].duration_minutes
        
        if commit:
            interview.save()
        
        return interview
