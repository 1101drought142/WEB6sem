from django.urls import path, register_converter
from main.views import (
    HomePageView,
    SendFormView,
    NewsListView,
    NewsDetailView,
    NotFoundView,
    FeedbackAPIView
)
from main.converters import OneDigitYearConverter

handler404 = 'main.views.NotFoundView.as_view()'

register_converter(OneDigitYearConverter, "onedigit")

urlpatterns = [
    path('', HomePageView.as_view(), name='homepage'),
    path('send_form', SendFormView.as_view(), name='send_form'),  # Старый endpoint (можно удалить)
    path('api/feedback/', FeedbackAPIView.as_view(), name='feedback_api'),  # Новый API endpoint
    path('news/', NewsListView.as_view(), name='news'),
    path('news_elem/<slug:news_slug>/', NewsDetailView.as_view(), name='news_detail'),
]