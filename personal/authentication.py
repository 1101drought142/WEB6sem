from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailAuthBackend(ModelBackend):
    """
    Бэкенд аутентификации, позволяющий входить по email вместо username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Аутентификация пользователя по email или username.
        
        Args:
            request: HTTP запрос
            username: Имя пользователя или email
            password: Пароль
            **kwargs: Дополнительные аргументы
            
        Returns:
            User объект, если аутентификация успешна, иначе None
        """
        if username is None:
            username = kwargs.get('email')
        
        if username is None or password is None:
            return None
        
        try:
            # Пытаемся найти пользователя по email или username
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
        except User.DoesNotExist:
            # Возвращаем None, если пользователь не найден
            return None
        except User.MultipleObjectsReturned:
            # Если найдено несколько пользователей, берем первого
            user = User.objects.filter(
                Q(username=username) | Q(email=username)
            ).first()
        
        # Проверяем пароль и активность пользователя
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Получение пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            User объект, если найден и активен, иначе None
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        return user if self.user_can_authenticate(user) else None

