"""
Утилиты для приложения shared.
Содержит общие миксины для классов представлений.
"""


class DataMixin:
    """
    Миксин для добавления общего контекста в классы представлений.
    Устраняет дублирование кода и добавляет стандартные данные в шаблоны.
    """
    title_page = None
    extra_context = {}
    paginate_by = 2 

    def __init__(self, *args, **kwargs):
        """
        Инициализатор для формирования словаря extra_context.
        Вызывается при создании экземпляра класса представления.
        """
        # Вызываем __init__ родительского класса, если он есть
        super().__init__(*args, **kwargs)
        
        # Инициализируем extra_context как новый словарь для экземпляра
        # (чтобы избежать проблем с общим словарем класса)
        if not hasattr(self, '_extra_context_initialized'):
            self.extra_context = self.extra_context.copy() if isinstance(self.extra_context, dict) else {}
            self._extra_context_initialized = True
        
        # Базовое меню для всех пользователей
        menu = [
            {'title': 'Главная', 'url_name': 'homepage'},
            {'title': 'Новости', 'url_name': 'news'},
        ]
        
        # Обновляем extra_context с меню
        self.extra_context.update({
            'menu': menu
        })
        
        # Добавляем title в extra_context, если он задан
        if self.title_page:
            self.extra_context['title'] = self.title_page
    
    def get_mixin_context(self, context, **kwargs):
        """
        Метод для формирования контекста шаблона по умолчанию.
        
        Args:
            context: Базовый контекст от родительского класса
            **kwargs: Дополнительные именованные аргументы для контекста
        
        Returns:
            dict: Обновленный контекст с стандартными данными
        """
        # Базовое меню для всех пользователей (если не задано в extra_context)
        if 'menu' not in context and 'menu' not in self.extra_context:
            menu = [
                {'title': 'Главная', 'url_name': 'homepage'},
                {'title': 'Новости', 'url_name': 'news'},
            ]
            context['menu'] = menu
        
        if self.title_page:
            context['title'] = self.title_page
        
        # Добавляем данные из extra_context
        context.update(self.extra_context)
        context.update(kwargs)
        return context

