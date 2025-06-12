from django import forms

from .models import Resume


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['file', 'language']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        resume = super().save(commit=False)
        if self.cleaned_data['file']:
            resume.original_filename = self.cleaned_data['file'].name
            resume.file_size = self.cleaned_data['file'].size
        if commit:
            resume.save()
        return resume
