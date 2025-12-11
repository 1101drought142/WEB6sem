from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView, PasswordChangeView,
    PasswordChangeDoneView
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth import login
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme

from personal.models import UserProfile
from personal.forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm, UserDeleteForm,
    CustomPasswordResetForm, CustomSetPasswordForm, CustomPasswordChangeForm
)
from shared.utils import DataMixin


class UserRegistrationView(DataMixin, CreateView): 
    """Регистрация нового пользователя"""
    form_class = UserRegistrationForm
    template_name = 'personal/register.html'
    success_url = reverse_lazy('personal:profile')
    title_page = 'Регистрация'
    
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


class UserLoginView(DataMixin, LoginView):
    """Вход пользователя"""
    form_class = UserLoginForm
    template_name = 'personal/login.html'
    title_page = 'Вход'
    
    def get_success_url(self):
        # Проверяем параметр next из GET или POST запроса
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        
        # Проверяем безопасность URL (защита от открытых редиректов)
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure()
        ):
            return next_url
        
        # Если параметра next нет или он небезопасен, используем стандартную логику
        # Проверяем, является ли пользователь доктором
        if hasattr(self.request.user, 'doctor'):
            return reverse_lazy('chat:doctor_requests')
        return reverse_lazy('personal:profile')
    
    def form_valid(self, form):
        messages.success(self.request, f'Добро пожаловать, {form.get_user().username}!')
        return super().form_valid(form)


class UserLogoutView(LogoutView):
    """Выход пользователя из системы"""
    
    def dispatch(self, request, *args, **kwargs):
        # Сохраняем имя пользователя перед выходом для сообщения
        username = request.user.username if request.user.is_authenticated else None
        response = super().dispatch(request, *args, **kwargs)
        # Добавляем сообщение об успешном выходе
        if username:
            messages.success(request, f'Вы успешно вышли из системы. До свидания, {username}!')
        return response


class UserProfileView(DataMixin, LoginRequiredMixin, DetailView):
    """Просмотр профиля пользователя"""
    model = UserProfile
    template_name = 'personal/profile.html'
    context_object_name = 'profile'
    title_page = 'Профиль'
    
    def get_object(self, queryset=None):
        # Получаем профиль для текущего пользователя
        return UserProfile.objects.get(user=self.request.user)


class UserProfileUpdateView(DataMixin, PermissionRequiredMixin, LoginRequiredMixin, UpdateView):
    """Редактирование профиля пользователя"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'personal/profile_edit.html'
    success_url = reverse_lazy('personal:profile')
    title_page = 'Редактирование профиля'
    permission_required = 'personal.change_userprofile'
    
    def get_object(self, queryset=None):
        # Получаем профиль для текущего пользователя
        return UserProfile.objects.get(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлён!')
        return super().form_valid(form)


class UserDeleteView(DataMixin, LoginRequiredMixin, DeleteView):
    """Удаление аккаунта пользователя"""
    model = UserProfile
    template_name = 'personal/account_delete.html'
    success_url = reverse_lazy('homepage')
    title_page = 'Удаление аккаунта'
    
    def get_object(self, queryset=None): 
        return UserProfile.objects.get(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        """Обработка DELETE запроса"""
        user = self.request.user
        messages.success(request, 'Ваш аккаунт успешно удалён.')
        user.delete()
        
        if request.headers.get('Content-Type') == 'application/json':
            from django.http import JsonResponse
            return JsonResponse({'success': True, 'redirect': str(self.success_url)})
        
        return redirect(self.success_url)


class UserPasswordResetView(DataMixin, PasswordResetView):
    """Представление для запроса восстановления пароля"""
    form_class = CustomPasswordResetForm
    template_name = 'personal/password_reset_form.html'
    email_template_name = 'personal/password_reset_email.html'
    success_url = reverse_lazy('personal:password_reset_done')
    title_page = 'Восстановление пароля'
    
    def form_valid(self, form):
        messages.info(
            self.request,
            'Инструкции по восстановлению пароля отправлены на указанный email адрес.'
        )
        return super().form_valid(form)


class UserPasswordResetDoneView(DataMixin, PasswordResetDoneView):
    """Страница подтверждения отправки письма для восстановления пароля"""
    template_name = 'personal/password_reset_done.html'
    title_page = 'Письмо отправлено'


class UserPasswordResetConfirmView(DataMixin, PasswordResetConfirmView):
    """Представление для изменения пароля по ссылке из письма"""
    form_class = CustomSetPasswordForm
    template_name = 'personal/password_reset_confirm.html'
    success_url = reverse_lazy('personal:password_reset_complete')
    title_page = 'Новый пароль'
    
    def form_valid(self, form):
        messages.success(self.request, 'Пароль успешно изменён!')
        return super().form_valid(form)


class UserPasswordResetCompleteView(DataMixin, PasswordResetCompleteView):
    """Страница успешного изменения пароля"""
    template_name = 'personal/password_reset_complete.html'
    title_page = 'Пароль изменён'


class UserPasswordChangeView(DataMixin, LoginRequiredMixin, PasswordChangeView):
    """Представление для смены пароля авторизованным пользователем"""
    form_class = CustomPasswordChangeForm
    template_name = 'personal/password_change_form.html'
    success_url = reverse_lazy('personal:password_change_done')
    title_page = 'Смена пароля'
    
    def form_valid(self, form):
        messages.success(self.request, 'Пароль успешно изменён!')
        return super().form_valid(form)


class UserPasswordChangeDoneView(DataMixin, LoginRequiredMixin, PasswordChangeDoneView):
    """Страница успешной смены пароля"""
    template_name = 'personal/password_change_done.html'
    title_page = 'Пароль изменён'