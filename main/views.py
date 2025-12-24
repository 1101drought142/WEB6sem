from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView, FormView, CreateView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.http import Http404, JsonResponse
from django.db.models import Q, F, BooleanField, Case, When, Value, Count
from django.db.models.functions import Length
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from main.models import News, Tags, Category, Feedback, Poll
from main.forms import FeedbackForm, CallbackForm
from shared.utils import DataMixin
from django.shortcuts import get_object_or_404


class HomePageView(DataMixin, TemplateView):
    """Главная страница"""
    template_name = "main.html"
    title_page = 'Главная страница'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, feedback_form=FeedbackForm())




class NewsListView(DataMixin, ListView):
    """Список новостей с пагинацией и фильтрацией"""
    model = News
    template_name = "news.html"
    context_object_name = 'news'
    title_page = 'Новости'
    
    def get_queryset(self):
        # Базовый queryset с оптимизацией
        queryset = News.published.all().prefetch_related('tags').select_related('poll').annotate(
            is_good=Case(
                When(poll__likes__gt=F('poll__dislikes'), then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).annotate(
            tags_count=Count('tags')
        ).annotate(
            description_len=Length('description')
        )
        
        # Фильтрация
        filter_tags = self.request.GET.getlist('tags')
        filter_category = self.request.GET.get('category')
        
        if filter_tags and filter_category:
            queryset = queryset.filter(Q(category__slug=filter_category) & Q(tags__slug__in=filter_tags))
        elif filter_tags:
            queryset = queryset.filter(tags__slug__in=filter_tags)
        elif filter_category:
            queryset = queryset.filter(category__slug=filter_category)
        
        return queryset.annotate(total=Count('id')).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_tags = self.request.GET.getlist('tags')
        filter_category = self.request.GET.get('category')
        
        # Формируем query string для пагинации
        query_params = []
        if filter_category:
            query_params.append(f"&category={filter_category}")
        for tag in filter_tags:
            query_params.append(f"&tags={tag}")
        query_string = ''.join(query_params)
        
        return self.get_mixin_context(
            context,
            tags=Tags.objects.all(),
            categories=Category.objects.all(),
            filter_tags=filter_tags,
            filter_category=filter_category,
            query_string=query_string
        )


class NewsDetailView(DataMixin, DetailView):
    """Детальная страница новости"""
    model = News
    template_name = "news-detail.html"
    context_object_name = 'elem'
    slug_field = 'slug'
    slug_url_kwarg = 'news_slug'
    
    def get_queryset(self):
        # Показываем только опубликованные новости с оптимизацией запросов
        return News.published.all().select_related('poll', 'category').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем текущий голос пользователя из сессии
        news_slug = context['elem'].slug
        session_key = f'poll_vote_{news_slug}'
        current_vote = self.request.session.get(session_key, None)
        context['current_vote'] = current_vote
        return self.get_mixin_context(context, title=context['elem'])


class NotFoundView(DataMixin, TemplateView):
    """Страница 404"""
    template_name = "404.html"
    title_page = 'Страница не найдена'


class FeedbackAPIView(CreateView):
    """
    API endpoint для обработки формы обратной связи через AJAX.
    Принимает POST запросы и возвращает JSON с результатом валидации.
    Сохраняет валидные данные в базу данных.
    """
    model = Feedback
    form_class = FeedbackForm
    
    def form_valid(self, form):
        """Обработка валидной формы"""
        # Сохраняем в базу данных 
        feedback = form.save()
        
        # Логирование для отладки
        print(f"""
        === Новое сообщение обратной связи (AJAX) ===
        ID: {feedback.id}
        Имя: {feedback.name}
        Email: {feedback.email}
        Тема: {feedback.subject}
        Сообщение: {feedback.message}
        Скриншот: {'Да' if feedback.screenshot else 'Нет'}
        Дата: {feedback.created_at}
        =============================================
        """)
        
        # Возвращаем успешный ответ
        return JsonResponse({
            'success': True,
            'message': 'Спасибо за ваше обращение! Мы свяжемся с вами в ближайшее время.',
            'feedback_id': feedback.id
        })
    
    def form_invalid(self, form):
        """Обработка невалидной формы"""
        # Формируем детальные ошибки для фронтенда
        errors = {}
        
        # Ошибки для конкретных полей
        for field, error_list in form.errors.items():
            if field == '__all__':
                # Общие ошибки формы
                errors['general'] = [str(error) for error in error_list]
            else:
                # Ошибки конкретных полей
                errors[field] = [str(error) for error in error_list]
        
        # Возвращаем ошибки валидации
        return JsonResponse({
            'success': False,
            'errors': errors,
            'message': 'Пожалуйста, исправьте ошибки в форме.'
        }, status=400)


class CallbackAPIView(FormView):
    """
    API endpoint для обработки формы "Позвоните мне" через AJAX.
    Принимает POST запросы и возвращает JSON с результатом валидации.
    Не сохраняет данные в базу, только выводит в консоль.
    """
    form_class = CallbackForm
    
    def form_valid(self, form):
        """Обработка валидной формы"""
        name = form.cleaned_data['name']
        phone = form.cleaned_data['phone']
        
        # Выводим данные в консоль вместо сохранения в БД
        print(f"""
        === Запрос на обратный звонок ===
        Имя: {name}
        Телефон: {phone}
        Дата: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        ==================================
        """)
        
        # Возвращаем успешный ответ
        return JsonResponse({
            'success': True,
            'message': 'Спасибо! Мы свяжемся с вами в ближайшее время.'
        })
    
    def form_invalid(self, form):
        """Обработка невалидной формы"""
        # Формируем детальные ошибки для фронтенда
        errors = {}
        
        # Ошибки для конкретных полей
        for field, error_list in form.errors.items():
            if field == '__all__':
                # Общие ошибки формы
                errors['general'] = [str(error) for error in error_list]
            else:
                # Ошибки конкретных полей
                errors[field] = [str(error) for error in error_list]
        
        # Возвращаем ошибки валидации
        return JsonResponse({
            'success': False,
            'errors': errors,
            'message': 'Пожалуйста, исправьте ошибки в форме.'
        }, status=400)


class PollVoteView(View):
    """
    API endpoint для обработки голосования за новость (лайки/дизлайки).
    Принимает POST запросы и возвращает JSON с обновленными значениями.
    Поддерживает переключение голоса и отмену голосования.
    """
    def post(self, request, news_slug):
        # Получаем новость
        news = get_object_or_404(News.published.all(), slug=news_slug)
        
        # Получаем или создаем опрос
        poll, created = Poll.objects.get_or_create(news=news, defaults={'likes': 0, 'dislikes': 0})
        
        # Получаем текущий голос пользователя из сессии
        session_key = f'poll_vote_{news_slug}'
        current_vote = request.session.get(session_key, None)
        
        # Получаем тип голоса из запроса
        vote_type = request.POST.get('vote_type')
        
        if vote_type not in ['like', 'dislike']:
            return JsonResponse({
                'success': False,
                'message': 'Неверный тип голоса. Используйте "like" или "dislike".',
                'likes': poll.likes,
                'dislikes': poll.dislikes,
                'current_vote': current_vote
            }, status=400)
        
        # Логика переключения голоса
        if current_vote == vote_type:
            # Отменяем голос (пользователь нажал на уже выбранную кнопку)
            if vote_type == 'like':
                poll.likes = max(0, poll.likes - 1)
            else:  # dislike
                poll.dislikes = max(0, poll.dislikes - 1)
            poll.save()
            # Удаляем голос из сессии
            if session_key in request.session:
                del request.session[session_key]
            current_vote = None
            message = 'Ваш голос отменен.'
        elif current_vote is None:
            # Новый голос
            if vote_type == 'like':
                poll.likes += 1
            else:  # dislike
                poll.dislikes += 1
            poll.save()
            request.session[session_key] = vote_type
            current_vote = vote_type
            message = 'Спасибо за ваш голос!'
        else:
            # Переключение с одного типа на другой
            # Уменьшаем предыдущий голос
            if current_vote == 'like':
                poll.likes = max(0, poll.likes - 1)
            else:  # current_vote == 'dislike'
                poll.dislikes = max(0, poll.dislikes - 1)
            
            # Увеличиваем новый голос
            if vote_type == 'like':
                poll.likes += 1
            else:  # dislike
                poll.dislikes += 1
            
            poll.save()
            request.session[session_key] = vote_type
            current_vote = vote_type
            message = 'Ваш голос изменен.'
        
        # Возвращаем успешный ответ
        return JsonResponse({
            'success': True,
            'message': message,
            'likes': poll.likes,
            'dislikes': poll.dislikes,
            'current_vote': current_vote
        })
