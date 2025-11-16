from django.urls import path, register_converter
from main.views import (
    HomePageView,
    NewsListView,
    NewsDetailView,
    NotFoundView,
    FeedbackAPIView,
    CallbackAPIView
)
from main.converters import OneDigitYearConverter

handler404 = 'main.views.NotFoundView.as_view()'

register_converter(OneDigitYearConverter, "onedigit")

urlpatterns = [
    path('', HomePageView.as_view(), name='homepage'),
    path('api/feedback/', FeedbackAPIView.as_view(), name='feedback_api'),
    path('api/callback/', CallbackAPIView.as_view(), name='callback_api'),
    path('news/', NewsListView.as_view(), name='news'),
    path('news_elem/<slug:news_slug>/', NewsDetailView.as_view(), name='news_detail'),
]