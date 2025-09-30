from django.urls import path
from django.contrib.auth.views import LogoutView
from personal.views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileView,
    UserProfileUpdateView,
    UserDeleteView,
)

app_name = 'personal'

urlpatterns = [
    # Авторизация
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Профиль
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/edit/', UserProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/delete/', UserDeleteView.as_view(), name='account_delete'),
]
