from django.contrib import admin
from personal.models import UserProfile, Doctor


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'get_full_name', 'date_of_birth', 'height', 'weight', 'created_at')
    list_display_links = ('id', 'user', 'get_full_name')
    search_fields = ('user__username', 'first_name', 'last_name', 'middle_name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
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


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_full_name', 'specialization', 'is_active', 'created_at')
    list_display_links = ('id', 'get_full_name')
    list_filter = ('specialization', 'is_active', 'created_at')
    search_fields = ('first_name', 'last_name', 'middle_name', 'user__username')
    list_editable = ('is_active',)
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Пользователь', {
            'fields': ('user',)
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