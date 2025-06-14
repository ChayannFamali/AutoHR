# resume/forms.py
# resume/forms.py
from django import forms

from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file', 'language']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.docx',
                'id': 'resume_file'
            }),
            'language': forms.Select(attrs={
                'class': 'form-select'
            })
        }
        labels = {
            'file': 'Файл резюме',
            'language': 'Язык резюме'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['language'].initial = 'auto'
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        
        if file:
            # Проверка расширения
            allowed_extensions = ['.pdf', '.docx']
            file_extension = file.name.lower().split('.')[-1]
            if f'.{file_extension}' not in allowed_extensions:
                raise forms.ValidationError('Разрешены только файлы PDF и DOCX')
            
            # Проверка размера (10MB)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 10MB')
        
        return file
    
    def save(self, commit=True):
        resume = super().save(commit=False)
        
        if self.cleaned_data['file']:
            resume.original_filename = self.cleaned_data['file'].name
            resume.file_size = self.cleaned_data['file'].size
        
        if commit:
            resume.save()
        
        return resume
