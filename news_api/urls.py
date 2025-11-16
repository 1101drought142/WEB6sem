from django.urls import path
from news_api import views

urlpatterns = [
    path('api/news/', views.NewsListCreateView.as_view(), name='api_news_list_create'),
    path('api/news/<int:pk>/', views.NewsDetailUpdateDeleteView.as_view(), name='api_news_detail_update_delete'),
]