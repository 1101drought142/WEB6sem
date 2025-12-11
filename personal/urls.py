from django.urls import path
from personal.views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    UserProfileView,
    UserProfileUpdateView,
    UserDeleteView,
    UserPasswordResetView,
    UserPasswordResetDoneView,
    UserPasswordResetConfirmView,
    UserPasswordResetCompleteView,
    UserPasswordChangeView,
    UserPasswordChangeDoneView,
)

app_name = 'personal'

urlpatterns = [
    # Авторизация
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    # Восстановление пароля
    path('password-reset/', UserPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', UserPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', UserPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # Смена пароля (для авторизованных пользователей)
    path('password-change/', UserPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', UserPasswordChangeDoneView.as_view(), name='password_change_done'),
    
    # Профиль
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('profile/edit/', UserProfileUpdateView.as_view(), name='profile_edit'),
    path('profile/delete/', UserDeleteView.as_view(), name='account_delete'),
]
