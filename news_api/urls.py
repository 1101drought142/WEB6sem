from django.urls import path
from news_api import views

urlpatterns = [
    path('api/news/', views.api_news_list_create, name='api_news_list_create'),
    path('api/news/<int:pk>/', views.api_news_detail_update_delete, name='api_news_detail_update_delete'),
]