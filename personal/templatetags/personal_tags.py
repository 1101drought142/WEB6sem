from django import template

register = template.Library()


@register.filter
def is_admin_only(user):
    """Проверяет, является ли пользователь администратором без профиля/доктора"""
    from personal.models import is_admin_only as check_admin
    return check_admin(user)
