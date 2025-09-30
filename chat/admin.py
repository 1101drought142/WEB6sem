from django.contrib import admin
from chat.models import Request, Chat, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('sender', 'created_at', 'is_read', 'read_at')
    fields = ('sender', 'text', 'file', 'is_read', 'created_at')
    can_delete = False


@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'patient', 'doctor', 'specialization', 'status', 'created_at')
    list_display_links = ('id', 'title')
    list_filter = ('status', 'specialization', 'created_at')
    search_fields = ('title', 'description', 'patient__username', 'doctor__first_name', 'doctor__last_name')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'specialization')
        }),
        ('Участники', {
            'fields': ('patient', 'doctor')
        }),
        ('Статус', {
            'fields': ('status',)
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['assign_status_waiting', 'assign_status_closed']
    
    @admin.action(description="Установить статус 'Ожидает доктора'")
    def assign_status_waiting(self, request, queryset):
        updated = queryset.update(status=Request.Status.WAITING)
        self.message_user(request, f"{updated} заявок переведено в статус 'Ожидает доктора'.")
    
    @admin.action(description="Закрыть заявки")
    def assign_status_closed(self, request, queryset):
        updated = queryset.update(status=Request.Status.CLOSED)
        self.message_user(request, f"{updated} заявок закрыто.")


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'get_patient', 'get_doctor', 'created_at', 'updated_at')
    list_display_links = ('id', 'request')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('request__title', 'request__patient__username')
    readonly_fields = ('created_at', 'updated_at', 'get_last_message', 'get_messages_count')
    inlines = [MessageInline]
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('request',)
        }),
        ('Статистика', {
            'fields': ('get_messages_count', 'get_last_message')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def get_patient(self, obj):
        return obj.request.patient.username
    get_patient.short_description = 'Пациент'
    
    def get_doctor(self, obj):
        return obj.request.doctor.get_full_name() if obj.request.doctor else '-'
    get_doctor.short_description = 'Доктор'
    
    def get_messages_count(self, obj):
        return obj.messages.count()
    get_messages_count.short_description = 'Количество сообщений'
    
    def get_last_message(self, obj):
        last_message = obj.get_last_message()
        if last_message:
            return f"{last_message.sender.username}: {last_message.text[:50]}..."
        return "Нет сообщений"
    get_last_message.short_description = 'Последнее сообщение'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'text_preview', 'is_read', 'created_at')
    list_display_links = ('id', 'chat')
    list_filter = ('is_read', 'created_at')
    search_fields = ('text', 'sender__username', 'chat__request__title')
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('chat', 'sender')
        }),
        ('Содержимое', {
            'fields': ('text', 'file')
        }),
        ('Статус', {
            'fields': ('is_read', 'read_at')
        }),
        ('Метаданные', {
            'fields': ('created_at',),
        }),
    )
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'