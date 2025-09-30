from django import forms
from chat.models import Request, Message


class RequestCreateForm(forms.ModelForm):
    """Форма создания заявки"""
    
    class Meta:
        model = Request
        fields = ('title', 'description', 'specialization')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Например: Консультация по питанию'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишите вашу проблему подробно',
                'rows': 5
            }),
            'specialization': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Тема заявки',
            'description': 'Описание проблемы',
            'specialization': 'Специализация доктора',
        }


class MessageCreateForm(forms.ModelForm):
    """Форма отправки сообщения"""
    
    class Meta:
        model = Message
        fields = ('text', 'file')
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control message-input',
                'placeholder': 'Введите сообщение...',
                'rows': 3
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
        }
        labels = {
            'text': '',
            'file': 'Прикрепить файл',
        }
    
    def clean(self):
        cleaned_data = super().clean()
        text = cleaned_data.get('text')
        file = cleaned_data.get('file')
        
        # Проверяем, что хотя бы одно поле заполнено
        if not text and not file:
            raise forms.ValidationError('Необходимо ввести текст сообщения или прикрепить файл.')
        
        return cleaned_data
