from django.contrib import admin
from django.utils.html import format_html
from main.models import Tags, News, Category, Poll, Feedback
# Register your models here



class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'news_count')    
    ordering = ('id',)                     

    def news_count(self, obj):
        return obj.news_set.count()
    news_count.short_description = 'Количество новостей'    

class PollInline(admin.StackedInline):
    model = Poll
    can_delete = False
    verbose_name = "Опрос"
    verbose_name_plural = 'Опрос'
    fk_name = 'news'

class NewsTagInline(admin.TabularInline):
    model = News.tags.through  # через промежуточную модель
    extra = 1
    verbose_name = "Тэг"
    verbose_name_plural = "Тэги"

class NewsAdmin(admin.ModelAdmin):

    class HasImageFilter(admin.SimpleListFilter):
        title = 'Наличие фотографии'
        parameter_name = 'has_image'

        def lookups(self, request, model_admin):
            return [
                ('yes', 'С фотографией'),
                ('no', 'Без фотографии'),
            ]

        def queryset(self, request, queryset):
            value = self.value()
            if value == 'yes':
                return queryset.exclude(image='').exclude(image__isnull=True)
            if value == 'no':
                return queryset.filter(image__isnull=True) | queryset.filter(image='')
            return queryset

    list_display = ('id', 'name', 'slug', 'category', 'status', 'tags_count')  
    list_editable = ('status', ) 
    list_display_links = ('category', 'name')      
    ordering = ('id',)                     

    def tags_count(self, obj):
        return obj.tags.count()
    tags_count.short_description = 'Количество тэгов'

    actions = ['set_status_draft', 'set_status_published']

    @admin.action(description="Пометить как черновик")
    def set_status_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f"{updated} записей переведено в статус 'Черновик'.")

    @admin.action(description="Опубликовать")
    def set_status_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f"{updated} записей опубликовано.")

    search_fields = ['name', 'category__name']
    list_filter = ('category__name', "status", HasImageFilter)

    readonly_fields = ('updated_at', 'image_preview')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'image', 'image_preview')
        }),
        ('Категоризация', {
            'fields': ('category',),
            'classes': ('collapse',),
        }),
        ('Метаданные', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )
    inlines = [PollInline, NewsTagInline]
    prepopulated_fields = {'slug': ('name',)}
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 200px;" />', obj.image.url)
        return "Нет изображения"
    image_preview.short_description = "Превью изображения"



@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """Админка для обратной связи"""
    
    list_display = ('id', 'name', 'email', 'subject', 'created_at', 'is_processed', 'screenshot_preview_small')
    list_display_links = ('id', 'subject')
    list_editable = ('is_processed',)
    list_filter = ('is_processed', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'screenshot_preview')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('name', 'email')
        }),
        ('Обращение', {
            'fields': ('subject', 'message', 'screenshot', 'screenshot_preview')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'is_processed'),
            'classes': ('collapse',)
        }),
    )
    
    def screenshot_preview(self, obj):
        """Превью скриншота"""
        if obj.screenshot:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 400px; border: 1px solid #ddd; border-radius: 4px;" />',
                obj.screenshot.url
            )
        return "Нет скриншота"
    screenshot_preview.short_description = "Превью скриншота"

    def screenshot_preview_small(self, obj):
        """Превью скриншота"""
        if obj.screenshot:
            return format_html(
                '<img src="{}" style="max-width: 70px; max-height: 70px; border: 1px solid #ddd; border-radius: 4px;" />',
                obj.screenshot.url
            )
        return "Нет скриншота"
    screenshot_preview_small.short_description = "Превью скриншота"
    
    actions = ['mark_as_processed', 'mark_as_unprocessed']
    
    @admin.action(description="Отметить как обработанное")
    def mark_as_processed(self, request, queryset):
        updated = queryset.update(is_processed=True)
        self.message_user(request, f"{updated} обращений отмечено как обработанные.")
    
    @admin.action(description="Отметить как необработанное")
    def mark_as_unprocessed(self, request, queryset):
        updated = queryset.update(is_processed=False)
        self.message_user(request, f"{updated} обращений отмечено как необработанные.")


admin.site.register(News, NewsAdmin)
admin.site.register(Category, CategoryAdmin)