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

from personal.models import UserProfile, Doctor
from personal.forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm, DoctorProfileForm, UserDeleteForm,
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
        from personal.models import is_admin_only
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
        # Администраторы перенаправляются в админ-панель
        if is_admin_only(self.request.user):
            return reverse_lazy('admin:index')
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
    
    def dispatch(self, request, *args, **kwargs):
        from personal.models import is_admin_only, is_doctor
        # Администраторы без профиля не могут просматривать профиль
        if is_admin_only(request.user):
            messages.info(request, 'У администраторов нет профиля. Используйте админ-панель для управления.')
            return redirect('admin:index')
        # Докторы перенаправляются на страницу просмотра профиля доктора
        if is_doctor(request.user):
            return redirect('personal:doctor_profile')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        # Получаем профиль для текущего пользователя
        return UserProfile.objects.get(user=self.request.user)


class UserProfileUpdateView(DataMixin, LoginRequiredMixin, UpdateView):
    """Редактирование профиля пользователя"""
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'personal/profile_edit.html'
    success_url = reverse_lazy('personal:profile')
    title_page = 'Редактирование профиля'
    
    def dispatch(self, request, *args, **kwargs):
        from personal.models import is_admin_only, is_doctor
        # Администраторы без профиля не могут редактировать профиль
        if is_admin_only(request.user):
            messages.info(request, 'У администраторов нет профиля. Используйте админ-панель для управления.')
            return redirect('admin:index')
        # Докторы перенаправляются на страницу редактирования профиля доктора
        if is_doctor(request.user):
            messages.info(request, 'Для редактирования профиля доктора используйте специальную страницу.')
            return redirect('personal:doctor_profile_edit')
        return super().dispatch(request, *args, **kwargs)
    
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
    
    def dispatch(self, request, *args, **kwargs):
        from personal.models import is_admin_only, is_doctor
        # Администраторы без профиля не могут удалять профиль
        if is_admin_only(request.user):
            messages.info(request, 'У администраторов нет профиля. Используйте админ-панель для управления.')
            return redirect('admin:index')
        # Докторы перенаправляются на страницу удаления профиля доктора
        if is_doctor(request.user):
            messages.info(request, 'Для удаления аккаунта доктора используйте специальную страницу.')
            return redirect('personal:doctor_account_delete')
        return super().dispatch(request, *args, **kwargs)
    
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


class DoctorDeleteView(DataMixin, LoginRequiredMixin, DeleteView):
    """Удаление аккаунта доктора"""
    model = Doctor
    template_name = 'personal/doctor_account_delete.html'
    success_url = reverse_lazy('homepage')
    title_page = 'Удаление аккаунта доктора'
    
    def dispatch(self, request, *args, **kwargs):
        from personal.models import is_doctor, is_admin_only
        # Администраторы без профиля не могут удалять профиль доктора
        if is_admin_only(request.user):
            messages.info(request, 'У администраторов нет профиля. Используйте админ-панель для управления.')
            return redirect('admin:index')
        # Только докторы могут удалять профиль доктора
        if not is_doctor(request.user):
            messages.error(request, 'У вас нет доступа к этой странице.')
            return redirect('homepage')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        # Получаем профиль доктора для текущего пользователя
        return Doctor.objects.get(user=self.request.user)

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
    
    def get_success_url(self):
        """Определяет URL для редиректа после успешной смены пароля"""
        from personal.models import is_doctor
        # Если пользователь - доктор, перенаправляем на страницу просмотра профиля доктора
        if is_doctor(self.request.user):
            return reverse_lazy('personal:doctor_profile')
        # Иначе на страницу профиля
        return reverse_lazy('personal:profile')
    
    def form_valid(self, form):
        messages.success(self.request, 'Пароль успешно изменён!')
        return super().form_valid(form)


class UserPasswordChangeDoneView(DataMixin, LoginRequiredMixin, PasswordChangeDoneView):
    """Страница успешной смены пароля"""
    template_name = 'personal/password_change_done.html'
    title_page = 'Пароль изменён'


class DoctorProfileView(DataMixin, LoginRequiredMixin, DetailView):
    """Просмотр профиля доктора"""
    model = Doctor
    template_name = 'personal/doctor_profile.html'
    context_object_name = 'doctor'
    title_page = 'Профиль доктора'
    
    def dispatch(self, request, *args, **kwargs):
        from personal.models import is_doctor, is_admin_only
        # Администраторы без профиля не могут просматривать профиль доктора
        if is_admin_only(request.user):
            messages.info(request, 'У администраторов нет профиля. Используйте админ-панель для управления.')
            return redirect('admin:index')
        # Только докторы могут просматривать профиль доктора
        if not is_doctor(request.user):
            messages.error(request, 'У вас нет доступа к этой странице.')
            return redirect('homepage')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        # Получаем профиль доктора для текущего пользователя
        return Doctor.objects.get(user=self.request.user)


class DoctorProfileUpdateView(DataMixin, LoginRequiredMixin, UpdateView):
    """Редактирование профиля доктора"""
    model = Doctor
    form_class = DoctorProfileForm
    template_name = 'personal/doctor_profile_edit.html'
    success_url = reverse_lazy('personal:doctor_profile')
    title_page = 'Редактирование профиля доктора'
    
    def dispatch(self, request, *args, **kwargs):
        from personal.models import is_doctor, is_admin_only
        # Администраторы без профиля не могут редактировать профиль доктора
        if is_admin_only(request.user):
            messages.info(request, 'У администраторов нет профиля. Используйте админ-панель для управления.')
            return redirect('admin:index')
        # Только докторы могут редактировать профиль доктора
        if not is_doctor(request.user):
            messages.error(request, 'У вас нет доступа к этой странице.')
            return redirect('homepage')
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self, queryset=None):
        # Получаем профиль доктора для текущего пользователя
        return Doctor.objects.get(user=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Профиль успешно обновлён!')
        return super().form_valid(form)