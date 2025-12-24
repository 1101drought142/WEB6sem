import os
import uuid
from django.db import models
from django.db.models.signals import pre_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


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
    
    def clean(self):
        """Валидация: пользователь не может быть одновременно пациентом и доктором"""
        super().clean()
        if self.user_id:
            # Проверяем, не является ли этот пользователь уже доктором
            # Если это новый объект или user изменился, проверяем наличие Doctor
            if not self.pk:
                # Новый объект - проверяем наличие Doctor
                if Doctor.objects.filter(user=self.user).exists():
                    raise ValidationError({
                        'user': 'Этот пользователь уже является доктором. Пользователь не может быть одновременно пациентом и доктором.'
                    })
            else:
                # Существующий объект - проверяем, не изменился ли user
                old_instance = UserProfile.objects.get(pk=self.pk)
                if old_instance.user_id != self.user_id:
                    # User изменился - проверяем наличие Doctor у нового user
                    if Doctor.objects.filter(user=self.user).exists():
                        raise ValidationError({
                            'user': 'Этот пользователь уже является доктором. Пользователь не может быть одновременно пациентом и доктором.'
                        })
    
    def save(self, *args, **kwargs):
        """Переопределяем save для вызова clean перед сохранением"""
        self.full_clean()
        super().save(*args, **kwargs)
    
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
    
    def clean(self):
        """Валидация: пользователь не может быть одновременно пациентом и доктором"""
        super().clean()
        if self.user_id:
            # Проверяем, не является ли этот пользователь уже пациентом
            # Если это новый объект или user изменился, проверяем наличие UserProfile
            if not self.pk:
                # Новый объект - проверяем наличие UserProfile
                if UserProfile.objects.filter(user=self.user).exists():
                    raise ValidationError({
                        'user': 'Этот пользователь уже является пациентом. Пользователь не может быть одновременно пациентом и доктором.'
                    })
            else:
                # Существующий объект - проверяем, не изменился ли user
                old_instance = Doctor.objects.get(pk=self.pk)
                if old_instance.user_id != self.user_id:
                    # User изменился - проверяем наличие UserProfile у нового user
                    if UserProfile.objects.filter(user=self.user).exists():
                        raise ValidationError({
                            'user': 'Этот пользователь уже является пациентом. Пользователь не может быть одновременно пациентом и доктором.'
                        })
    
    def save(self, *args, **kwargs):
        """Переопределяем save для вызова clean перед сохранением"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Доктор {self.get_full_name()} ({self.get_specialization_display()})"
    
    class Meta:
        verbose_name = "Доктор"
        verbose_name_plural = "Доктора"


# Helper-функции для проверки типа пользователя
def is_doctor(user):
    """Проверяет, является ли пользователь доктором"""
    return hasattr(user, 'doctor') and user.doctor is not None


def is_patient(user):
    """Проверяет, является ли пользователь пациентом"""
    return hasattr(user, 'profile') and user.profile is not None


def get_user_type(user):
    """Возвращает тип пользователя: 'doctor', 'patient' или None"""
    if is_doctor(user):
        return 'doctor'
    elif is_patient(user):
        return 'patient'
    return None


def is_admin_only(user):
    """Проверяет, является ли пользователь администратором без профиля/доктора"""
    if not user.is_authenticated:
        return False
    # Администратор - это пользователь с is_staff=True, но без профиля и без доктора
    return user.is_staff and not is_doctor(user) and not is_patient(user)


# Сигналы для дополнительной защиты на уровне БД
# Примечание: основная валидация выполняется в методах clean() и save() моделей
# Сигналы служат дополнительным уровнем защиты
@receiver(pre_save, sender=UserProfile)
def prevent_userprofile_doctor_conflict(sender, instance, **kwargs):
    """Дополнительная проверка перед сохранением UserProfile"""
    if instance.user_id:
        # Проверяем наличие Doctor у этого пользователя
        doctor_exists = Doctor.objects.filter(user=instance.user).exists()
        if doctor_exists:
            # Если это новый объект или user изменился
            if not instance.pk:
                raise ValidationError(
                    'Пользователь не может быть одновременно пациентом и доктором.'
                )
            else:
                # Проверяем, изменился ли user
                try:
                    old_instance = UserProfile.objects.get(pk=instance.pk)
                    if old_instance.user_id != instance.user_id:
                        raise ValidationError(
                            'Пользователь не может быть одновременно пациентом и доктором.'
                        )
                except UserProfile.DoesNotExist:
                    # Объект не существует в БД, значит это новый объект
                    raise ValidationError(
                        'Пользователь не может быть одновременно пациентом и доктором.'
                    )


@receiver(pre_save, sender=Doctor)
def prevent_doctor_userprofile_conflict(sender, instance, **kwargs):
    """Дополнительная проверка перед сохранением Doctor"""
    if instance.user_id:
        # Проверяем наличие UserProfile у этого пользователя
        profile_exists = UserProfile.objects.filter(user=instance.user).exists()
        if profile_exists:
            # Если это новый объект или user изменился
            if not instance.pk:
                raise ValidationError(
                    'Пользователь не может быть одновременно пациентом и доктором.'
                )
            else:
                # Проверяем, изменился ли user
                try:
                    old_instance = Doctor.objects.get(pk=instance.pk)
                    if old_instance.user_id != instance.user_id:
                        raise ValidationError(
                            'Пользователь не может быть одновременно пациентом и доктором.'
                        )
                except Doctor.DoesNotExist:
                    # Объект не существует в БД, значит это новый объект
                    raise ValidationError(
                        'Пользователь не может быть одновременно пациентом и доктором.'
                    )