from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class UserProfile(models.Model):
    """Расширенный профиль пользователя (пациента)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="Пользователь")
    
    # Личные данные
    first_name = models.CharField(max_length=100, verbose_name="Имя", blank=True)
    last_name = models.CharField(max_length=100, verbose_name="Фамилия", blank=True)
    middle_name = models.CharField(max_length=100, verbose_name="Отчество", blank=True)
    
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
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    def __str__(self):
        full_name = self.get_full_name()
        return full_name if full_name else self.user.username
    
    def get_full_name(self):
        """Возвращает полное ФИО"""
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join([p for p in parts if p])
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class Doctor(models.Model):
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
    
    # Личные данные
    first_name = models.CharField(max_length=100, verbose_name="Имя")
    last_name = models.CharField(max_length=100, verbose_name="Фамилия")
    middle_name = models.CharField(max_length=100, verbose_name="Отчество", blank=True)
    
    # Статус
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    
    def __str__(self):
        return f"Доктор {self.get_full_name()} ({self.get_specialization_display()})"
    
    def get_full_name(self):
        """Возвращает полное ФИО"""
        parts = [self.last_name, self.first_name, self.middle_name]
        return " ".join([p for p in parts if p])
    
    class Meta:
        verbose_name = "Доктор"
        verbose_name_plural = "Доктора"