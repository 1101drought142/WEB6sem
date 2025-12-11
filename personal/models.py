import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


def generate_profile_photo_filename(instance, filename):
    """Генерирует уникальное имя файла для фото профиля"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('profiles/photos/', filename)


class BaseProfile(models.Model):
    """
    Базовая абстрактная модель профиля с общей функциональностью.
    Содержит общие поля и методы для UserProfile и Doctor.
    """
    
    # Личные данные (общие для всех профилей)
    first_name = models.CharField(max_length=100, verbose_name="Имя", blank=True)
    last_name = models.CharField(max_length=100, verbose_name="Фамилия", blank=True)
    middle_name = models.CharField(max_length=100, verbose_name="Отчество", blank=True)
    
    # Фото профиля
    photo = models.ImageField(
        upload_to=generate_profile_photo_filename,
        verbose_name="Фото",
        blank=True,
        null=True,
        help_text="Загрузите фото профиля"
    )
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    def get_full_name(self):
        """Возвращает полное ФИО"""
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join([p for p in parts if p])
    
    class Meta:
        abstract = True




class UserProfile(BaseProfile):
    """Расширенный профиль пользователя (пациента)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    
    # Дополнительные личные данные
    date_of_birth = models.DateField(verbose_name="Дата рождения", null=True, blank=True)
    
    # Медицинские данные
    height = models.IntegerField(
        verbose_name="Рост (см)", 
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(250)]
    )
    weight = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="Вес (кг)", 
        null=True, 
        blank=True,
        validators=[MinValueValidator(10), MaxValueValidator(500)]
    )
    
    # Дополнительные метаданные
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name else self.user.username
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
        permissions = [
            ("can_change_email", "Может изменять email адрес аккаунта"),
        ]


class Doctor(BaseProfile):
    """Модель доктора"""
    
    class Specialization(models.TextChoices):
        NUTRITIONIST = 'nutritionist', 'Диетолог'
        SPORTS_DOCTOR = 'sports_doctor', 'Спортивный врач'
        PSYCHOLOGIST = 'psychologist', 'Психолог'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor', verbose_name="Пользователь")
    
    # Профессиональные данные
    specialization = models.CharField(
        max_length=50,
        choices=Specialization.choices,
        verbose_name="Специализация"
    )
    description = models.TextField(verbose_name="Описание", blank=True)
    
    # Статус
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    # Переопределяем поля имени для обязательности (кроме middle_name)
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    
    def __str__(self):
        return f"Доктор {self.get_full_name()} ({self.get_specialization_display()})"
    
    class Meta:
        verbose_name = "Доктор"
        verbose_name_plural = "Доктора"