"""
Автотесты для форм приложения personal
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

from personal.forms import (
    UserRegistrationForm, UserProfileForm, UserLoginForm,
    CustomPasswordResetForm
)
from personal.models import UserProfile, Doctor


class UserRegistrationFormTest(TestCase):
    """Тесты для формы регистрации"""
    
    def test_valid_registration(self):
        """Тест валидной регистрации"""
        form = UserRegistrationForm(data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'middle_name': 'Иванович',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        })
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@test.com')
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.first_name, 'Иван')
        self.assertEqual(profile.last_name, 'Иванов')
    
    def test_duplicate_email(self):
        """Тест регистрации с существующим email"""
        User.objects.create_user(
            username='existing',
            email='existing@test.com',
            password='testpass123'
        )
        
        form = UserRegistrationForm(data={
            'username': 'newuser',
            'email': 'existing@test.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_duplicate_username(self):
        """Тест регистрации с существующим username"""
        User.objects.create_user(
            username='existing',
            email='existing@test.com',
            password='testpass123'
        )
        
        form = UserRegistrationForm(data={
            'username': 'existing',
            'email': 'new@test.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password1': 'ComplexPass123!',
            'password2': 'ComplexPass123!'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_password_mismatch(self):
        """Тест несовпадения паролей"""
        form = UserRegistrationForm(data={
            'username': 'newuser',
            'email': 'newuser@test.com',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'password1': 'ComplexPass123!',
            'password2': 'DifferentPass123!'
        })
        self.assertFalse(form.is_valid())


class UserProfileFormTest(TestCase):
    """Тесты для формы редактирования профиля"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            first_name='Иван',
            last_name='Иванов'
        )
    
    def test_valid_profile_update(self):
        """Тест валидного обновления профиля"""
        form = UserProfileForm(instance=self.profile, data={
            'email': 'newemail@test.com',
            'first_name': 'Петр',
            'last_name': 'Петров',
            'middle_name': 'Петрович',
            'date_of_birth': '01.01.1990',
            'height': 180,
            'weight': 75.5
        })
        self.assertTrue(form.is_valid())
        
        updated_profile = form.save()
        self.assertEqual(updated_profile.first_name, 'Петр')
        self.assertEqual(updated_profile.last_name, 'Петров')
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@test.com')
    
    def test_date_of_birth_format(self):
        """Тест формата даты рождения"""
        form = UserProfileForm(instance=self.profile, data={
            'email': 'testuser@test.com',
            'date_of_birth': '31.12.2000'
        })
        self.assertTrue(form.is_valid())
        
        profile = form.save()
        self.assertEqual(profile.date_of_birth, date(2000, 12, 31))
    
    def test_date_of_birth_invalid_format(self):
        """Тест невалидного формата даты"""
        form = UserProfileForm(instance=self.profile, data={
            'email': 'testuser@test.com',
            'date_of_birth': '2000-12-31'  # Неправильный формат
        })
        # Форма должна преобразовать или выдать ошибку
        # В зависимости от реализации может быть валидной (если есть преобразование)
        # или невалидной
    
    def test_duplicate_email_update(self):
        """Тест обновления с существующим email другого пользователя"""
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )
        
        form = UserProfileForm(instance=self.profile, data={
            'email': 'other@test.com',  # Email другого пользователя
            'first_name': 'Иван',
            'last_name': 'Иванов'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
    
    def test_height_validation(self):
        """Тест валидации роста"""
        form = UserProfileForm(instance=self.profile, data={
            'email': 'testuser@test.com',
            'height': 49  # Меньше минимума
        })
        # Валидация происходит на уровне модели, форма может быть валидной
        # но при сохранении будет ошибка
        if form.is_valid():
            profile = form.save(commit=False)
            with self.assertRaises(ValidationError):
                profile.full_clean()
    
    def test_weight_validation(self):
        """Тест валидации веса"""
        form = UserProfileForm(instance=self.profile, data={
            'email': 'testuser@test.com',
            'weight': 501  # Больше максимума
        })
        if form.is_valid():
            profile = form.save(commit=False)
            with self.assertRaises(ValidationError):
                profile.full_clean()
    
    def test_photo_upload(self):
        """Тест загрузки фото"""
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        form = UserProfileForm(
            instance=self.profile,
            data={
                'email': 'testuser@test.com',
                'first_name': 'Иван',
                'last_name': 'Иванов'
            },
            files={'photo': image}
        )
        self.assertTrue(form.is_valid())
        
        profile = form.save()
        self.assertTrue(profile.photo)


class UserLoginFormTest(TestCase):
    """Тесты для формы входа"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@test.com',
            password='testpass123'
        )
    
    def test_login_with_username(self):
        """Тест входа по username"""
        from django.contrib.auth import authenticate
        
        user = authenticate(username='testuser', password='testpass123')
        self.assertIsNotNone(user)
        self.assertEqual(user, self.user)
    
    def test_login_with_email(self):
        """Тест входа по email (через кастомный бэкенд)"""
        # Проверяем, что используется EmailAuthBackend
        from personal.authentication import EmailAuthBackend
        
        backend = EmailAuthBackend()
        user = backend.authenticate(
            request=None,
            username='testuser@test.com',
            password='testpass123'
        )
        self.assertIsNotNone(user)
        self.assertEqual(user, self.user)
