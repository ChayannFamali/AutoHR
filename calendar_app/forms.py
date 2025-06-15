from django import forms
from django.contrib.auth.models import User

from core.models import Application

from .models import Interview, InterviewType


class QuickScheduleInterviewForm(forms.ModelForm):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'})
    )
    
    class Meta:
        model = Interview
        fields = ['format', 'location']
        widgets = {
            'format': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Адрес или ссылка на видеоконференцию'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.application = kwargs.pop('application', None)
        super().__init__(*args, **kwargs)
        
        # Устанавливаем минимальную дату
        from datetime import date, timedelta
        tomorrow = date.today() + timedelta(days=1)
        self.fields['date'].widget.attrs['min'] = tomorrow.isoformat()
    
    def clean(self):
        cleaned_data = super().clean()
        date_val = cleaned_data.get('date')
        time_val = cleaned_data.get('time')
        
        if date_val and time_val:
            from datetime import datetime, timezone
            scheduled_datetime = datetime.combine(date_val, time_val)
            
            if scheduled_datetime <= datetime.now():
                raise forms.ValidationError('Дата и время собеседования должны быть в будущем')
        
        return cleaned_data
    
    def save(self, commit=True):
        interview = super().save(commit=False)
        
        if self.application:
            interview.application = self.application
            interview.candidate = self.application.candidate
        
        if self.user:
            interview.interviewer = self.user
        
        from datetime import datetime, timezone
        scheduled_date = self.cleaned_data['date']
        scheduled_time = self.cleaned_data['time']
        interview.scheduled_at = datetime.combine(scheduled_date, scheduled_time).replace(tzinfo=timezone.utc)
        
        interview.status = 'scheduled'
        interview.duration_minutes = 60
        try:
            default_type = InterviewType.objects.filter(is_active=True).first()
            if default_type:
                interview.interview_type = default_type
                interview.duration_minutes = default_type.duration_minutes
        except:
            pass
        
        if commit:
            interview.save()
        
        return interview

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
        
        self.fields['application'].help_text = "Выберите заявку кандидата"
        self.fields['location'].help_text = "Укажите адрес офиса или ссылку на видеоконференцию"
    
    def save(self, commit=True):
        interview = super().save(commit=False)
        
        scheduled_date = self.cleaned_data['scheduled_date']
        scheduled_time = self.cleaned_data['scheduled_time']
        
        from datetime import datetime
        from datetime import timezone as tz
        interview.scheduled_at = datetime.combine(scheduled_date, scheduled_time).replace(tzinfo=tz.utc)
        
        interview.candidate = self.cleaned_data['application'].candidate
        
        interview.duration_minutes = self.cleaned_data['interview_type'].duration_minutes
        
        if commit:
            interview.save()
        
        return interview
