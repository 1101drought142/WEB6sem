from django import forms
from django.core.validators import MinLengthValidator, MaxLengthValidator, RegexValidator
from django.core.exceptions import ValidationError
from .models import Feedback

def validate_no_spam_words(value):
    """
    Собственный валидатор для проверки на спам-слова.
    Проверяет, что в тексте нет запрещенных слов.
    """
    spam_words = ['спам', 'реклама', 'купить', 'скидка', 'бесплатно', 'spam']
    value_lower = value.lower()
    
    for spam_word in spam_words:
        if spam_word in value_lower:
            raise ValidationError(
                f'Текст содержит запрещенное слово: "{spam_word}". Пожалуйста, перефразируйте.'
            )


def validate_has_letters(value):
    """
    Собственный валидатор для проверки наличия букв в тексте.
    Проверяет, что значение содержит хотя бы одну букву.
    """
    if not any(char.isalpha() for char in value):
        raise ValidationError('Текст должен содержать хотя бы одну букву')


def validate_max_message_length(value):
    """
    Собственный валидатор для проверки максимальной длины сообщения.
    Проверяет, что сообщение не превышает 1000 символов.
    """
    if len(value) > 1000:
        raise ValidationError('Сообщение не должно превышать 1000 символов')


def validate_image_size(value):
    """
    Собственный валидатор для проверки размера загружаемого изображения.
    Ограничивает размер файла 5MB.
    """
    max_size = 5 * 1024 * 1024  # 5MB
    if value.size > max_size:
        raise ValidationError(f'Размер файла не должен превышать 5MB. Текущий размер: {value.size / (1024 * 1024):.2f}MB')


class FeedbackForm(forms.ModelForm):
    """
    Форма обратной связи, связанная с моделью Feedback.
    """
    class Meta:
        model = Feedback
        fields = ['name', 'email', 'subject', 'message', 'screenshot']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите ваше имя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@email.com'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'О чём вы хотите рассказать?'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Опишите ваши пожелания или вопросы...',
                'rows': 5
            }),
            'screenshot': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
        labels = {
            'name': 'Ваше имя',
            'email': 'Email',
            'subject': 'Тема обращения',
            'message': 'Ваше сообщение',
            'screenshot': 'Скриншот'
        }
        help_texts = {
            'email': 'Обязательное поле для связи с вами',
            'screenshot': 'Прикрепите скриншот проблемы. Максимум 5MB. Форматы: JPG, PNG, GIF'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем валидаторы к полям
        self.fields['name'].validators.extend([
            MinLengthValidator(2, message='Имя должно содержать минимум 2 символа'),
            RegexValidator(
                regex=r'^[а-яА-ЯёЁa-zA-Z\s-]+$',
                message='Имя может содержать только буквы, пробелы и дефис'
            ),
            validate_has_letters
        ])
        
        self.fields['subject'].validators.extend([
            MinLengthValidator(5, message='Тема должна содержать минимум 5 символов'),
            MaxLengthValidator(200, message='Тема не должна превышать 200 символов')
        ])
        
        self.fields['message'].validators.extend([
            MinLengthValidator(10, message='Сообщение должно содержать минимум 10 символов'),
            validate_max_message_length,
            validate_has_letters,
            validate_no_spam_words
        ])
        
        self.fields['screenshot'].validators.append(validate_image_size)
    
    def clean(self):
        """
        Общая валидация формы.
        Проверяет связанные поля.
        """
        cleaned_data = super().clean()
        subject = cleaned_data.get('subject')
        message = cleaned_data.get('message')
        
        # Проверка, что тема и сообщение не дублируют друг друга
        if subject and message and subject.lower() == message.lower():
            raise forms.ValidationError(
                'Тема и сообщение не должны полностью совпадать'
            )
        
        return cleaned_data


class CallbackForm(forms.Form):
    """
    Форма "Позвоните мне" - не связана с моделью.
    Содержит только имя и телефон.
    """
    name = forms.CharField(
        max_length=100,
        label='Ваше имя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше имя',
            'required': True
        }),
        validators=[
            MinLengthValidator(2, message='Имя должно содержать минимум 2 символа'),
            RegexValidator(
                regex=r'^[а-яА-ЯёЁa-zA-Z\s-]+$',
                message='Имя может содержать только буквы, пробелы и дефис'
            ),
            validate_has_letters
        ]
    )
    
    phone = forms.CharField(
        max_length=20,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 123-45-67',
            'required': True,
            'type': 'tel'
        }),
        validators=[
            MinLengthValidator(10, message='Телефон должен содержать минимум 10 символов'),
            RegexValidator(
                regex=r'^[\d\s\-\+\(\)]+$',
                message='Телефон может содержать только цифры, пробелы, дефисы, скобки и знак +'
            )
        ]
    )
    
    def clean_phone(self):
        """Очистка и валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Удаляем все нецифровые символы для проверки
            digits_only = ''.join(filter(str.isdigit, phone))
            if len(digits_only) < 10:
                raise forms.ValidationError('Телефон должен содержать минимум 10 цифр')
        return phone