"""
Автотесты для приложения personal (профили пользователей и докторов)
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

from personal.models import UserProfile, Doctor, is_doctor, is_patient, get_user_type


class UserProfileModelTest(TestCase):
    """Тесты для модели UserProfile"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='patient1',
            email='patient1@test.com',
            password='testpass123'
        )
    
    def test_create_user_profile(self):
        """Тест создания профиля пациента"""
        profile = UserProfile.objects.create(
            user=self.user,
            first_name='Иван',
            last_name='Иванов',
            middle_name='Иванович',
            date_of_birth=date(1990, 1, 1),
            height=180,
            weight=75.5
        )
        
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.first_name, 'Иван')
        self.assertEqual(profile.get_full_name(), 'Иванов Иван Иванович')
        self.assertEqual(profile.height, 180)
        self.assertEqual(float(profile.weight), 75.5)
    
    def test_get_full_name_without_middle_name(self):
        """Тест получения полного имени без отчества"""
        profile = UserProfile.objects.create(
            user=self.user,
            first_name='Петр',
            last_name='Петров'
        )
        self.assertEqual(profile.get_full_name(), 'Петров Петр')
    
    def test_get_full_name_empty(self):
        """Тест получения полного имени когда поля пустые"""
        profile = UserProfile.objects.create(user=self.user)
        self.assertEqual(profile.get_full_name(), '')
        self.assertEqual(str(profile), self.user.username)
    
    def test_height_validation_min(self):
        """Тест валидации минимального роста"""
        profile = UserProfile(
            user=self.user,
            height=49  # Меньше минимума
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_height_validation_max(self):
        """Тест валидации максимального роста"""
        profile = UserProfile(
            user=self.user,
            height=251  # Больше максимума
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_weight_validation_min(self):
        """Тест валидации минимального веса"""
        profile = UserProfile(
            user=self.user,
            weight=9.9  # Меньше минимума
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_weight_validation_max(self):
        """Тест валидации максимального веса"""
        profile = UserProfile(
            user=self.user,
            weight=501  # Больше максимума
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_cannot_be_doctor_and_patient(self):
        """Тест: пользователь не может быть одновременно доктором и пациентом"""
        # Создаем доктора
        doctor = Doctor.objects.create(
            user=self.user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        
        # Пытаемся создать профиль пациента для того же пользователя
        profile = UserProfile(user=self.user)
        with self.assertRaises(ValidationError):
            profile.full_clean()
            profile.save()
    
    def test_profile_photo_upload(self):
        """Тест загрузки фото профиля"""
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        profile = UserProfile.objects.create(
            user=self.user,
            photo=image
        )
        self.assertTrue(profile.photo)
        self.assertIn('profiles/photos/', profile.photo.name)


class DoctorModelTest(TestCase):
    """Тесты для модели Doctor"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user = User.objects.create_user(
            username='doctor1',
            email='doctor1@test.com',
            password='testpass123'
        )
    
    def test_create_doctor(self):
        """Тест создания доктора"""
        doctor = Doctor.objects.create(
            user=self.user,
            first_name='Алексей',
            last_name='Врачев',
            specialization=Doctor.Specialization.PSYCHOLOGIST,
            description='Опытный психолог'
        )
        
        self.assertEqual(doctor.user, self.user)
        self.assertEqual(doctor.get_full_name(), 'Врачев Алексей')
        self.assertEqual(doctor.specialization, Doctor.Specialization.PSYCHOLOGIST)
        self.assertTrue(doctor.is_active)
        self.assertIn('Доктор', str(doctor))
    
    def test_doctor_specialization_choices(self):
        """Тест выбора специализации"""
        specializations = [choice[0] for choice in Doctor.Specialization.choices]
        self.assertIn('nutritionist', specializations)
        self.assertIn('sports_doctor', specializations)
        self.assertIn('psychologist', specializations)
    
    def test_cannot_be_patient_and_doctor(self):
        """Тест: пользователь не может быть одновременно пациентом и доктором"""
        # Создаем профиль пациента
        profile = UserProfile.objects.create(
            user=self.user,
            first_name='Пациент',
            last_name='Тестов'
        )
        
        # Пытаемся создать доктора для того же пользователя
        doctor = Doctor(
            user=self.user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        with self.assertRaises(ValidationError):
            doctor.full_clean()
            doctor.save()
    
    def test_doctor_required_fields(self):
        """Тест обязательных полей доктора"""
        # first_name и last_name обязательны
        doctor = Doctor(
            user=self.user,
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        with self.assertRaises(ValidationError):
            doctor.full_clean()
    
    def test_doctor_inactive(self):
        """Тест деактивации доктора"""
        doctor = Doctor.objects.create(
            user=self.user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST,
            is_active=False
        )
        self.assertFalse(doctor.is_active)


class HelperFunctionsTest(TestCase):
    """Тесты для вспомогательных функций"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.patient_user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123'
        )
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='testpass123'
        )
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        
        UserProfile.objects.create(user=self.patient_user)
        Doctor.objects.create(
            user=self.doctor_user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
    
    def test_is_doctor(self):
        """Тест функции is_doctor"""
        self.assertTrue(is_doctor(self.doctor_user))
        self.assertFalse(is_doctor(self.patient_user))
        self.assertFalse(is_doctor(self.regular_user))
    
    def test_is_patient(self):
        """Тест функции is_patient"""
        self.assertTrue(is_patient(self.patient_user))
        self.assertFalse(is_patient(self.doctor_user))
        self.assertFalse(is_patient(self.regular_user))
    
    def test_get_user_type(self):
        """Тест функции get_user_type"""
        self.assertEqual(get_user_type(self.patient_user), 'patient')
        self.assertEqual(get_user_type(self.doctor_user), 'doctor')
        self.assertIsNone(get_user_type(self.regular_user))


class ProfileValidationTest(TestCase):
    """Тесты валидации профилей"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
    
    def test_user_profile_validation_on_save(self):
        """Тест валидации при сохранении UserProfile"""
        # Создаем доктора для user1
        Doctor.objects.create(
            user=self.user1,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        
        # Пытаемся создать профиль пациента для того же пользователя
        profile = UserProfile(user=self.user1)
        with self.assertRaises(ValidationError):
            profile.save()
    
    def test_doctor_validation_on_save(self):
        """Тест валидации при сохранении Doctor"""
        # Создаем профиль пациента для user1
        UserProfile.objects.create(user=self.user1)
        
        # Пытаемся создать доктора для того же пользователя
        doctor = Doctor(
            user=self.user1,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        with self.assertRaises(ValidationError):
            doctor.save()
    
    def test_valid_height_and_weight(self):
        """Тест валидных значений роста и веса"""
        profile = UserProfile(
            user=self.user1,
            height=175,
            weight=70.5
        )
        # Не должно быть ошибок
        profile.full_clean()
        profile.save()
        
        saved_profile = UserProfile.objects.get(user=self.user1)
        self.assertEqual(saved_profile.height, 175)
        self.assertEqual(float(saved_profile.weight), 70.5)
