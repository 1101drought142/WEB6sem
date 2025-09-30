from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect

from personal.models import UserProfile
from personal.forms import UserRegistrationForm, UserLoginForm, UserProfileForm, UserDeleteForm


class UserRegistrationView(CreateView):
    """Регистрация нового пользователя"""
    form_class = UserRegistrationForm
    template_name = 'personal/register.html'
    success_url = reverse_lazy('personal:profile')
    
    def dispatch(self, request, *args, **kwargs):
        # Если пользователь уже авторизован, перенаправляем его в профиль
        if request.user.is_authenticated:
            return redirect('personal:profile')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # Сохраняем пользователя
        response = super().form_valid(form)
        # Автоматически авторизуем пользователя после регистрации
        login(self.request, self.object)
        messages.success(self.request, 'Регистрация прошла успешно! Добро пожаловать!')
        return response


class UserLoginView(LoginView):
    """Вход пользователя"""
    form_class = UserLoginForm
    template_name = 'personal/login.html'
    
    def get_success_url(self):
        # Проверяем, является ли пользователь доктором
        if hasattr(self.request.user, 'doctor'):
            return reverse_lazy('chat:doctor_requests')
        return reverse_lazy('personal:profile')
    
    def form_valid(self, form):
        messages.success(self.request, f'Добро пожаловать, {form.get_user().username}!')
        return super().form_valid(form)



class UserProfileView(LoginRequiredMixin, DetailView):
    """Просмотр профиля пользователя"""
    model = UserProfile
    template_name = 'personal/profile.html'
    context_object_name = 'profile'
    
    def get_object(self, queryset=None):
        # Получаем или создаём профиль для текущего пользователя
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля пользователя"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'personal/profile_edit.html'
    success_url = reverse_lazy('personal:profile')
    
    def get_object(self, queryset=None):
        # Получаем или создаём профиль для текущего пользователя
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлён!')
        return super().form_valid(form)


class UserDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление аккаунта пользователя"""
    model = UserProfile
    template_name = 'personal/account_delete.html'
    success_url = reverse_lazy('homepage')
    
    def get_object(self, queryset=None):
        return UserProfile.objects.get(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        # Удаляем пользователя (профиль удалится автоматически через CASCADE)
        user = self.request.user
        messages.success(request, 'Ваш аккаунт успешно удалён.')
        user.delete()
        return redirect(self.success_url)