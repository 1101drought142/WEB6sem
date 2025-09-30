from django.db import models
from django.contrib.auth.models import User
from personal.models import Doctor


class Request(models.Model):
    """Модель заявки от пациента"""
    
    class Status(models.TextChoices):
        WAITING = 'waiting', 'Ожидает доктора'
        ASSIGNED = 'assigned', 'Доктор назначен'
        WAITING_DOCTOR = 'waiting_doctor', 'Ожидает ответа доктора'
        DOCTOR_REPLIED = 'doctor_replied', 'Доктор ответил'
        CLOSED = 'closed', 'Закрыта'
    
    class Specialization(models.TextChoices):
        NUTRITIONIST = 'nutritionist', 'Диетолог'
        SPORTS_DOCTOR = 'sports_doctor', 'Спортивный врач'
        PSYCHOLOGIST = 'psychologist', 'Психолог'
    
    # Основные поля
    patient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='requests',
        verbose_name="Пациент"
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='requests',
        verbose_name="Доктор"
    )
    
    # Информация о заявке
    title = models.CharField(max_length=255, verbose_name="Тема заявки")
    description = models.TextField(verbose_name="Описание проблемы")
    specialization = models.CharField(
        max_length=50,
        choices=Specialization.choices,
        verbose_name="Специализация"
    )
    
    # Статус
    status = models.CharField(
        max_length=50,
        choices=Status.choices,
        default=Status.WAITING,
        verbose_name="Статус"
    )
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    
    def __str__(self):
        return f"Заявка #{self.id} - {self.title}"
    
    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"
        ordering = ['-created_at']


class Chat(models.Model):
    """Модель чата между пациентом и доктором"""
    
    request = models.OneToOneField(
        Request,
        on_delete=models.CASCADE,
        related_name='chat',
        verbose_name="Заявка"
    )
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Последнее обновление")
    
    def __str__(self):
        return f"Чат #{self.id} - {self.request.title}"
    
    def get_last_message(self):
        """Возвращает последнее сообщение в чате"""
        return self.messages.order_by('-created_at').first()
    
    def get_unread_count_for_user(self, user):
        """Возвращает количество непрочитанных сообщений для пользователя"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    class Meta:
        verbose_name = "Чат"
        verbose_name_plural = "Чаты"
        ordering = ['-updated_at']


class Message(models.Model):
    """Модель сообщения в чате"""
    
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Чат"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Отправитель"
    )
    
    # Содержимое сообщения
    text = models.TextField(verbose_name="Текст сообщения", blank=True)
    file = models.FileField(
        upload_to='uploads/chat/',
        verbose_name="Файл",
        null=True,
        blank=True
    )
    
    # Статус
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    read_at = models.DateTimeField(null=True, blank=True, verbose_name="Время прочтения")
    
    def __str__(self):
        return f"Сообщение от {self.sender.username} в {self.created_at}"
    
    def mark_as_read(self):
        """Отмечает сообщение как прочитанное"""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['created_at']