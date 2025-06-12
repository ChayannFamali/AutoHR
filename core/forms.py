from django import forms

from .models import Application, Candidate


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
