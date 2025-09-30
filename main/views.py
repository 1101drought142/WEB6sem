from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView, FormView
from django.views import View
from django.urls import reverse_lazy, reverse
from django.http import Http404, JsonResponse
from django.db.models import Q, F, BooleanField, Case, When, Value, Count
from django.db.models.functions import Length
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from main.models import News, Tags, Category, Feedback
from main.forms import FeedbackForm
from django.shortcuts import get_object_or_404


class HomePageView(TemplateView):
    """Главная страница"""
    template_name = "main.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feedback_form'] = FeedbackForm()
        return context


class SendFormView(FormView):
    """Обработка формы обратной связи с главной страницы"""
    template_name = "main.html"
    form_class = FeedbackForm
    success_url = reverse_lazy('homepage')
    
    def form_valid(self, form):
        # Получаем данные из формы
        name = form.cleaned_data['name']
        email = form.cleaned_data.get('email', 'Не указан')
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['message']
        
        # Здесь можно обработать данные: отправить email, сохранить в файл, etc.
        # Например, вывести в консоль:
        print(f"""
        === Новое сообщение обратной связи ===
        Имя: {name}
        Email: {email}
        Тема: {subject}
        Сообщение: {message}
        =====================================
        """)
        
        # Добавляем сообщение об успехе
        messages.success(self.request, 'Спасибо за ваше обращение! Мы свяжемся с вами в ближайшее время.')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Обработка невалидной формы.
        Добавляем детальные сообщения об ошибках и возвращаем форму с ошибками.
        """
        # Добавляем общее сообщение
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        
        # Добавляем конкретные ошибки для каждого поля
        for field, errors in form.errors.items():
            for error in errors:
                if field == '__all__':
                    # Общие ошибки формы (из метода clean())
                    messages.error(self.request, f'Ошибка: {error}')
                else:
                    # Ошибки конкретных полей
                    field_label = form.fields[field].label or field
                    messages.error(self.request, f'{field_label}: {error}')
        
        # Возвращаем рендер шаблона с формой, содержащей ошибки
        # Не используем redirect, чтобы сохранить объект формы с ошибками
        context = self.get_context_data(form=form)
        context['feedback_form'] = form  # Передаем форму с ошибками
        return self.render_to_response(context)


class NewsListView(ListView):
    """Список новостей с пагинацией и фильтрацией"""
    model = News
    template_name = "news.html"
    context_object_name = 'news'
    paginate_by = 6  # Пагинация - 6 новостей на страницу
    
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
        context['tags'] = Tags.objects.all()
        context['categories'] = Category.objects.all()
        context['filter_tags'] = self.request.GET.getlist('tags')
        context['filter_category'] = self.request.GET.get('category')
        
        # Формируем query string для пагинации
        query_params = []
        if context['filter_category']:
            query_params.append(f"&category={context['filter_category']}")
        for tag in context['filter_tags']:
            query_params.append(f"&tags={tag}")
        context['query_string'] = ''.join(query_params)
        
        return context


class NewsDetailView(DetailView):
    """Детальная страница новости"""
    model = News
    template_name = "news-detail.html"
    context_object_name = 'elem'
    slug_field = 'slug'
    slug_url_kwarg = 'news_slug'
    
    def get_queryset(self):
        # Показываем только опубликованные новости
        return News.published.all()


class NotFoundView(TemplateView):
    """Страница 404"""
    template_name = "404.html"


class FeedbackAPIView(View):
    """
    API endpoint для обработки формы обратной связи через AJAX.
    Принимает POST запросы и возвращает JSON с результатом валидации.
    Сохраняет валидные данные в базу данных.
    """
    
    def post(self, request, *args, **kwargs):
        """Обработка POST запроса с данными формы"""
        form = FeedbackForm(request.POST, request.FILES)
        
        if form.is_valid():
            # Сохраняем в базу данных (ModelForm автоматически создает объект)
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
        
        else:
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
