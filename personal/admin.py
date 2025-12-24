from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from personal.models import UserProfile, Doctor


class UserProfileAdminForm(forms.ModelForm):
    """Форма для админки UserProfile с дополнительной валидацией"""
    
    class Meta:
        model = UserProfile
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        
        if user:
            # Проверяем, не является ли пользователь уже доктором
            if hasattr(user, 'doctor'):
                # Если это новый объект или user изменился
                if not self.instance.pk or (self.instance.pk and self.instance.user_id != user.id):
                    raise ValidationError({
                        'user': 'Этот пользователь уже является доктором. Пользователь не может быть одновременно пациентом и доктором.'
                    })
        
        return cleaned_data


class DoctorAdminForm(forms.ModelForm):
    """Форма для админки Doctor с дополнительной валидацией"""
    
    class Meta:
        model = Doctor
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        
        if user:
            # Проверяем, не является ли пользователь уже пациентом
            if hasattr(user, 'profile'):
                # Если это новый объект или user изменился
                if not self.instance.pk or (self.instance.pk and self.instance.user_id != user.id):
                    raise ValidationError({
                        'user': 'Этот пользователь уже является пациентом. Пользователь не может быть одновременно пациентом и доктором.'
                    })
        
        return cleaned_data


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm
    list_display = ('id', 'user', 'get_full_name', 'date_of_birth', 'height', 'weight', 'created_at', 'user_status')
    list_display_links = ('id', 'user', 'get_full_name')
    search_fields = ('user__username', 'first_name', 'last_name', 'middle_name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at', 'user_status')
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user', 'user_status')
        }),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'middle_name', 'photo', 'date_of_birth')
        }),
        ('Медицинские данные', {
            'fields': ('height', 'weight')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_status(self, obj):
        """Показывает статус пользователя (пациент/доктор)"""
        if obj and obj.user_id:
            if hasattr(obj.user, 'doctor'):
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠ ВНИМАНИЕ: Этот пользователь также является доктором!</span>'
                )
            return format_html('<span style="color: green;">✓ Пациент</span>')
        return '-'
    user_status.short_description = 'Статус пользователя'
    
    def save_model(self, request, obj, form, change):
        """Дополнительная проверка перед сохранением"""
        # Вызываем clean модели (форма уже проверила, но для надежности)
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    form = DoctorAdminForm
    list_display = ('id', 'get_full_name', 'specialization', 'is_active', 'created_at', 'user_status')
    list_display_links = ('id', 'get_full_name')
    list_filter = ('specialization', 'is_active', 'created_at')
    search_fields = ('first_name', 'last_name', 'middle_name', 'user__username')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'user_status')
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user', 'user_status')
        }),
        ('Личные данные', {
            'fields': ('first_name', 'last_name', 'middle_name', 'photo')
        }),
        ('Профессиональные данные', {
            'fields': ('specialization', 'description')
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
        ('Метаданные', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def user_status(self, obj):
        """Показывает статус пользователя (пациент/доктор)"""
        if obj and obj.user_id:
            if hasattr(obj.user, 'profile'):
                return format_html(
                    '<span style="color: red; font-weight: bold;">⚠ ВНИМАНИЕ: Этот пользователь также является пациентом!</span>'
                )
            return format_html('<span style="color: green;">✓ Доктор</span>')
        return '-'
    user_status.short_description = 'Статус пользователя'
    
    def save_model(self, request, obj, form, change):
        """Дополнительная проверка перед сохранением"""
        # Вызываем clean модели (форма уже проверила, но для надежности)
        obj.full_clean()
        super().save_model(request, obj, form, change)
    
    def delete_model(self, request, obj):
        """Защита от удаления доктора, если есть активные заявки"""
        from chat.models import Request
        active_requests = Request.objects.filter(doctor=obj, status__in=[
            Request.Status.ASSIGNED,
            Request.Status.WAITING_DOCTOR,
            Request.Status.DOCTOR_REPLIED
        ]).count()
        
        if active_requests > 0:
            raise ValidationError(
                f'Невозможно удалить доктора: у него есть {active_requests} активных заявок. '
                'Сначала закройте или переназначьте все активные заявки.'
            )
        
        super().delete_model(request, obj)