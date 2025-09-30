from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import CreateView, ListView, DetailView, View
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.db.models import Q, Count, Max
from django.http import JsonResponse

from chat.models import Request, Chat, Message
from chat.forms import RequestCreateForm, MessageCreateForm
from personal.models import Doctor


class DoctorRequiredMixin(UserPassesTestMixin):
    """Миксин для проверки, что пользователь является доктором"""
    
    def test_func(self):
        return hasattr(self.request.user, 'doctor')
    
    def handle_no_permission(self):
        messages.error(self.request, 'Доступ запрещён. Эта страница доступна только докторам.')
        return redirect('homepage')


class RequestCreateView(LoginRequiredMixin, CreateView):
    """Создание заявки пациентом"""
    model = Request
    form_class = RequestCreateForm
    template_name = 'chat/request_create.html'
    success_url = reverse_lazy('chat:patient_chats')
    
    def form_valid(self, form):
        # Устанавливаем пациента
        form.instance.patient = self.request.user
        messages.success(self.request, 'Заявка успешно создана!')
        return super().form_valid(form)

class DoctorRequestsListView(LoginRequiredMixin, DoctorRequiredMixin, ListView):
    """Список доступных заявок для доктора"""
    model = Request
    template_name = 'chat/doctor_requests.html'
    context_object_name = 'requests'
    paginate_by = 20
    
    def get_queryset(self):
        doctor = self.request.user.doctor
        
        # Получаем параметр фильтрации
        filter_type = self.request.GET.get('filter', 'available')
        
        if filter_type == 'my':
            # Заявки, принятые этим доктором
            return Request.objects.filter(doctor=doctor).select_related('patient')
        else:
            # Доступные заявки для специализации доктора
            return Request.objects.filter(
                specialization=doctor.specialization,
                status=Request.Status.WAITING
            ).select_related('patient')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_type'] = self.request.GET.get('filter', 'available')
        return context


class RequestAcceptView(LoginRequiredMixin, DoctorRequiredMixin, View):
    """Принятие заявки доктором"""
    
    def post(self, request, pk):
        request_obj = get_object_or_404(Request, pk=pk, status=Request.Status.WAITING)
        doctor = request.user.doctor
        
        # Проверяем специализацию
        if request_obj.specialization != doctor.specialization:
            messages.error(request, 'Эта заявка не соответствует вашей специализации.')
            return redirect('chat:doctor_requests')
        
        # Принимаем заявку
        request_obj.doctor = doctor
        request_obj.status = Request.Status.ASSIGNED
        request_obj.save()
        
        # Создаём чат
        Chat.objects.create(request=request_obj)
        
        messages.success(request, f'Вы приняли заявку "{request_obj.title}".')
        return redirect('chat:chat_detail', pk=request_obj.chat.pk)


class ChatDetailView(LoginRequiredMixin, DetailView):
    """Детальная страница чата"""
    model = Chat
    template_name = 'chat/chat_detail.html'
    context_object_name = 'chat'
    
    def get_queryset(self):
        # Проверяем доступ
        user = self.request.user
        if hasattr(user, 'doctor'):
            # Доктор видит свои чаты
            return Chat.objects.filter(request__doctor=user.doctor)
        else:
            # Пациент видит свои чаты
            return Chat.objects.filter(request__patient=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['messages'] = self.object.messages.select_related('sender').order_by('created_at')
        context['form'] = MessageCreateForm()
        
        # Отмечаем сообщения как прочитанные
        unread_messages = self.object.messages.filter(is_read=False).exclude(sender=self.request.user)
        for message in unread_messages:
            message.mark_as_read()
        
        return context


class MessageSendView(LoginRequiredMixin, View):
    """Отправка сообщения в чат"""
    
    def post(self, request, chat_pk):
        chat = get_object_or_404(Chat, pk=chat_pk)
        
        # Проверяем доступ
        user = request.user
        if hasattr(user, 'doctor'):
            if chat.request.doctor != user.doctor:
                messages.error(request, 'Доступ запрещён.')
                return redirect('chat:doctor_requests')
        else:
            if chat.request.patient != user:
                messages.error(request, 'Доступ запрещён.')
                return redirect('chat:patient_chats')
        
        form = MessageCreateForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = user
            message.save()
            
            # Обновляем статус заявки
            if hasattr(user, 'doctor'):
                chat.request.status = Request.Status.DOCTOR_REPLIED
            else:
                chat.request.status = Request.Status.WAITING_DOCTOR
            chat.request.save()
            
            messages.success(request, 'Сообщение отправлено!')
        else:
            messages.error(request, 'Ошибка при отправке сообщения.')
        
        return redirect('chat:chat_detail', pk=chat_pk)


class PatientChatsListView(LoginRequiredMixin, ListView):
    """Список всех заявок пациента с таблицей"""
    model = Request
    template_name = 'chat/patient_chats.html'
    context_object_name = 'requests'
    paginate_by = 10
    
    def get_queryset(self):
        # Показываем ВСЕ заявки пациента (включая ожидающие доктора)
        return Request.objects.filter(
            patient=self.request.user
        ).select_related('doctor__user', 'chat').order_by('-created_at')


class DoctorChatsListView(LoginRequiredMixin, DoctorRequiredMixin, ListView):
    """Список чатов доктора"""
    model = Chat
    template_name = 'chat/doctor_chats.html'
    context_object_name = 'chats'
    
    def get_queryset(self):
        doctor = self.request.user.doctor
        
        # Получаем чаты с аннотациями
        chats = Chat.objects.filter(
            request__doctor=doctor
        ).select_related(
            'request__patient'
        ).annotate(
            unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=self.request.user))
        ).order_by('-updated_at')
        
        return chats