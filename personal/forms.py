from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import (
    UserCreationForm, AuthenticationForm, PasswordResetForm,
    SetPasswordForm, PasswordChangeForm
)
from django.contrib.auth.models import User
from personal.models import UserProfile, Doctor


class UserRegistrationForm(UserCreationForm):
    """Форма регистрации пользователя"""
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    first_name = forms.CharField(
        max_length=100,
        required=True,
        label="Имя",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'})
    )
    last_name = forms.CharField(
        max_length=100,
        required=True,
        label="Фамилия",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'})
    )
    middle_name = forms.CharField(
        max_length=100,
        required=False,
        label="Отчество",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Отчество (необязательно)'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Логин'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтверждение пароля'})
    
    def clean_email(self):
        """Проверка уникальности email (исключая текущего пользователя)"""
        # Если поля нет в форме (удалено из-за отсутствия разрешения), пропускаем валидацию
        if 'email' not in self.fields:
            return self.initial.get('email', '')
        
        email = self.cleaned_data.get('email')
        if email:
            # Проверяем, не занят ли email другим пользователем
            # self.instance - это User объект (так как форма основана на User)
            query = User.objects.filter(email=email)
            if self.instance and self.instance.pk:
                # Исключаем текущего пользователя при редактировании
                query = query.exclude(pk=self.instance.pk)
            existing_user = query.first()
            if existing_user:
                raise ValidationError('Пользователь с таким email уже существует.')
        return email
    
    def clean_username(self):
        """Проверка уникальности username"""
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует.')
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            # Создаём профиль пользователя
            UserProfile.objects.create(
                user=user,
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                middle_name=self.cleaned_data.get('middle_name', '')
            )
        return user


class UserLoginForm(AuthenticationForm):
    """Форма входа пользователя с настройкой виджетов"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Настройка виджетов для стилизации
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Логин или Email'
        })
        self.fields['username'].label = 'Логин'
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
        self.fields['password'].label = 'Пароль'


class UserProfileForm(forms.ModelForm):
    """Форма редактирования профиля пользователя"""
    
    # Поле email из модели User
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    # Переопределяем поле даты как CharField для полного контроля формата
    date_of_birth = forms.CharField(
        required=False,
        label='Дата рождения',
        widget=forms.TextInput(attrs={
            'class': 'form-control date-input', 
            'placeholder': 'dd.mm.yyyy',
            'pattern': r'\d{2}\.\d{2}\.\d{4}',
            'maxlength': '10'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'middle_name', 'photo', 'height', 'weight')
        # date_of_birth и email исключены из fields, так как переопределены выше
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Отчество'}),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Рост (см)'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Вес (кг)', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем начальное значение email из связанного пользователя
        if self.instance and self.instance.user:
            self.initial['email'] = self.instance.user.email
        # Преобразуем дату из объекта date в формат dd.mm.yyyy для отображения
        if self.instance and hasattr(self.instance, 'date_of_birth') and self.instance.date_of_birth:
            self.initial['date_of_birth'] = self.instance.date_of_birth.strftime('%d.%m.%Y')

        # Проверяем разрешение на изменение email
        user = self.instance.user if self.instance and self.instance.user else None
        if user and not user.has_perm('personal.can_change_email'):
            if 'email' in self.fields:
                del self.fields['email']
    
    def clean_email(self):
        """Проверка уникальности email (исключая текущего пользователя)"""
        email = self.cleaned_data.get('email')
        if email and self.instance and self.instance.user:
            # Проверяем, не занят ли email другим пользователем
            existing_user = User.objects.filter(email=email).exclude(pk=self.instance.user.pk).first()
            if existing_user:
                raise ValidationError('Пользователь с таким email уже существует.')
        return email
    
    def clean_date_of_birth(self):
        """Валидирует дату в формате dd.mm.yyyy, возвращает строку"""
        date_str = self.cleaned_data.get('date_of_birth')
        if not date_str:
            return ''
        
        # Убираем пробелы
        date_str = date_str.strip()
        
        if not date_str:
            return ''
        
        # Валидируем формат dd.mm.yyyy
        from datetime import datetime
        try:
            # Пытаемся распарсить формат dd.mm.yyyy
            datetime.strptime(date_str, '%d.%m.%Y').date()
            return date_str  # Возвращаем строку для CharField
        except ValueError:
            # Если не получилось, пробуем другие форматы для обратной совместимости
            try:
                datetime.strptime(date_str, '%Y-%m-%d').date()
                # Преобразуем YYYY-MM-DD в dd.mm.yyyy
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                return date_obj.strftime('%d.%m.%Y')
            except ValueError:
                raise forms.ValidationError('Введите дату в формате dd.mm.yyyy (например, 31.12.2000)')
    
    def save(self, commit=True):
        """Сохраняет форму, преобразуя строку даты в объект date и обновляя email пользователя"""
        instance = super().save(commit=False)
        
        # Обновляем email в связанной модели User
        if 'email' in self.cleaned_data and instance.user:
            instance.user.email = self.cleaned_data['email']
            if commit:
                instance.user.save()
        
        # Преобразуем строку даты в объект date
        date_str = self.cleaned_data.get('date_of_birth', '').strip()
        if date_str:
            from datetime import datetime
            try:
                # Пытаемся распарсить формат dd.mm.yyyy
                instance.date_of_birth = datetime.strptime(date_str, '%d.%m.%Y').date()
            except ValueError:
                # Если не получилось, пробуем другие форматы
                try:
                    instance.date_of_birth = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    instance.date_of_birth = None
        else:
            instance.date_of_birth = None
        
        if commit:
            instance.save()
        return instance


class DoctorProfileForm(forms.ModelForm):
    """Форма редактирования профиля доктора"""
    
    # Поле email из модели User
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    
    class Meta:
        model = Doctor
        fields = ('first_name', 'last_name', 'middle_name', 'photo', 'specialization', 'description')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'middle_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Отчество'}),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'specialization': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Описание',
                'rows': 4
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем начальное значение email из связанного пользователя
        if self.instance and self.instance.user:
            self.initial['email'] = self.instance.user.email
    
    def clean_email(self):
        """Проверка уникальности email (исключая текущего пользователя)"""
        email = self.cleaned_data.get('email')
        if email and self.instance and self.instance.user:
            # Проверяем, не занят ли email другим пользователем
            existing_user = User.objects.filter(email=email).exclude(pk=self.instance.user.pk).first()
            if existing_user:
                raise ValidationError('Пользователь с таким email уже существует.')
        return email
    
    def save(self, commit=True):
        """Сохраняет форму и обновляет email пользователя"""
        instance = super().save(commit=False)
        
        # Обновляем email в связанной модели User
        if 'email' in self.cleaned_data and instance.user:
            instance.user.email = self.cleaned_data['email']
            if commit:
                instance.user.save()
        
        if commit:
            instance.save()
        return instance


class UserDeleteForm(forms.Form):
    """Форма подтверждения удаления аккаунта"""
    confirm = forms.BooleanField(
        required=True,
        label="Я подтверждаю удаление аккаунта",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class CustomPasswordResetForm(PasswordResetForm):
    """Кастомная форма восстановления пароля с стилизованными полями"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Email'
        })


class CustomSetPasswordForm(SetPasswordForm):
    """Кастомная форма установки нового пароля с стилизованными полями"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Новый пароль'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля'
        })


class CustomPasswordChangeForm(PasswordChangeForm):
    """Кастомная форма смены пароля с стилизованными полями"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Текущий пароль'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Новый пароль'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтверждение пароля'
        })
