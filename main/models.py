import os
import uuid
from django.db import models
from django.utils.text import slugify

def generate_unique_filename(instance, filename):
    """Генерирует уникальное имя файла для избежания конфликтов"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('feedback/', filename)

class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=News.Status.PUBLISHED)

class Category(models.Model):
    name = models.CharField(verbose_name="Название", max_length=127)
    slug = models.CharField(verbose_name="Слаг", max_length=127)
    
    def __str__(self): 
        return f"{self.name}"

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

class Tags(models.Model):
    name = models.CharField(verbose_name="Название", max_length=127)
    slug = models.CharField(verbose_name="Слаг", max_length=127)
    
    def __str__(self): 
        return f"{self.name}"

    class Meta:
        verbose_name = "Тэг"
        verbose_name_plural = "Тэги"

class News(models.Model):

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Черновик'
        PUBLISHED = 'published', 'Опубликовано'
    updated_at = models.DateTimeField(auto_now=True)

    image = models.FileField(verbose_name="Фотография", upload_to='uploads/news/', null=True, blank=True)
    name = models.CharField(verbose_name="Название", max_length=127)
    slug = models.CharField(verbose_name="Слаг", max_length=127)
    description = models.TextField(verbose_name="Название")
    category = models.ForeignKey(Category, verbose_name="Категория", on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(
        max_length=127,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Статус"
    )
    tags = models.ManyToManyField(Tags, verbose_name="Тэги", related_name='news', blank=True)

    objects = models.Manager()           
    published = PublishedManager() 

    def __str__(self): 
        return f"{self.name}"

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"

class Poll(models.Model):
    news = models.OneToOneField(
        News,
        on_delete=models.CASCADE,
        related_name='poll'
    )
    likes = models.IntegerField(verbose_name="Лайки")
    dislikes = models.IntegerField(verbose_name="Дизлайки")

    def __str__(self): 
        return f"Опрос по - {self.news.name}"

    class Meta:
        verbose_name = "Опрос"
        verbose_name_plural = "Опросы"


class Feedback(models.Model):
    """
    Модель для хранения обращений обратной связи.
    """
    name = models.CharField(
        max_length=100,
        verbose_name="Имя"
    )
    email = models.EmailField(
        verbose_name="Email"
    )
    subject = models.CharField(
        max_length=200,
        verbose_name="Тема обращения"
    )
    slug = models.SlugField(
        max_length=200, 
        unique=True, 
        blank=True, 
        verbose_name="Слаг"
    )
    message = models.TextField(
        verbose_name="Сообщение"
    )
    screenshot = models.ImageField(
        upload_to=generate_unique_filename,
        verbose_name="Скриншот",
        null=True,
        blank=True,
        help_text="Прикрепите скриншот проблемы"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    is_processed = models.BooleanField(
        default=False,
        verbose_name="Обработано"
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(str(self))
            if not base_slug:
                base_slug = f"photo-{self.pk or 'new'}"

            counter = 0
            slug = base_slug
            while Feedback.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"

            self.slug = slug

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.subject} - {self.name}"

    class Meta:
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратная связь"
        ordering = ['-created_at']