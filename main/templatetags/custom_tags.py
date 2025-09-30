from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def show_error_message(context):
    request = context.get('request')
    if request and request.GET.get('error'):
        return mark_safe('<p style="color: red;">Проверьте заполнение полей формы</p>')
    return ''