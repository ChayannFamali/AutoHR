from django import forms

from .models import Application, Candidate, Company, Job


class ApplicationForm(forms.Form):
    first_name = forms.CharField(max_length=100, label='Имя')
    last_name = forms.CharField(max_length=100, label='Фамилия')
    email = forms.EmailField(label='Email')
    phone = forms.CharField(max_length=20, required=False, label='Телефон')
    cover_letter = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5}),
        required=False,
        label='Сопроводительное письмо'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class JobCreateForm(forms.ModelForm):
    company_name = forms.CharField(
        max_length=200, 
        required=False,
        label="Или введите новую компанию",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Job
        fields = [
            'title', 'company', 'description', 'requirements', 
            'experience_level', 'salary_min', 'salary_max', 
            'location', 'remote_work'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'remote_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].required = False
        self.fields['company'].empty_label = "Выберите компанию"
    
    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get('company')
        company_name = cleaned_data.get('company_name')
        
        if not company and not company_name:
            raise forms.ValidationError('Выберите существующую компанию или введите название новой.')
        
        return cleaned_data
    
    def save(self, commit=True):
        job = super().save(commit=False)
        
        if self.cleaned_data.get('company_name') and not self.cleaned_data.get('company'):
            company, created = Company.objects.get_or_create(
                name=self.cleaned_data['company_name']
            )
            job.company = company
        
        if commit:
            job.save()
        return job
    
class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'company', 'description', 'requirements', 
            'location', 'experience_level', 'remote_work'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'remote_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = Company.objects.all()
