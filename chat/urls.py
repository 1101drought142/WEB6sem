from django.urls import path
from chat.views import (
    RequestCreateView,
    DoctorRequestsListView,
    RequestAcceptView,
    ChatDetailView,
    MessageSendView,
    PatientChatsListView,
    DoctorChatsListView,
)

app_name = 'chat'

urlpatterns = [
    # Заявки - Пациент
    path('request/create/', RequestCreateView.as_view(), name='request_create'),
    path('chats/my/', PatientChatsListView.as_view(), name='patient_chats'),
    
    # Заявки - Доктор
    path('requests/doctor/', DoctorRequestsListView.as_view(), name='doctor_requests'),
    path('request/<int:pk>/accept/', RequestAcceptView.as_view(), name='request_accept'),
    path('chats/doctor/', DoctorChatsListView.as_view(), name='doctor_chats'),
    
    # Чат
    path('chat/<int:pk>/', ChatDetailView.as_view(), name='chat_detail'),
    path('chat/<int:chat_pk>/send/', MessageSendView.as_view(), name='message_send'),
]
