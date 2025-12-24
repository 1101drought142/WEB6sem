import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from chat.models import Chat, Message, Request
from django.utils import timezone


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer для обработки сообщений в чате"""
    
    async def connect(self):
        """Обработка подключения к WebSocket"""
        self.chat_id = self.scope['url_route']['kwargs']['chat_id']
        self.chat_group_name = f'chat_{self.chat_id}'
        self.user = self.scope['user']
        
        # Проверяем доступ к чату
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Проверяем, что пользователь имеет доступ к этому чату
        has_access = await self.check_chat_access()
        if not has_access:
            await self.close()
            return
        
        # Присоединяемся к группе чата
        await self.channel_layer.group_add(
            self.chat_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Отправляем информацию о подключении
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Вы подключены к чату'
        }))
    
    async def disconnect(self, close_code):
        """Обработка отключения от WebSocket"""
        # Покидаем группу чата
        await self.channel_layer.group_discard(
            self.chat_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Обработка получения сообщения от клиента"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                # Отправка нового сообщения
                text = data.get('text', '').strip()
                file_url = data.get('file_url', None)
                
                if not text and not file_url:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Сообщение не может быть пустым'
                    }))
                    return
                
                # Сохраняем сообщение в БД
                message = await self.save_message(text, file_url)
                
                if message:
                    # Получаем информацию о чате и участниках
                    chat_info = await self.get_chat_info()
                    
                    # Отправляем сообщение всем участникам чата
                    await self.channel_layer.group_send(
                        self.chat_group_name,
                        {
                            'type': 'chat_message',
                            'message_id': message.id,
                            'sender_id': message.sender.id,
                            'sender_username': message.sender.username,
                            'sender_is_doctor': await self.is_doctor(message.sender),
                            'sender_full_name': await self.get_user_full_name(message.sender),
                            'text': message.text,
                            'file_url': message.file.url if message.file else None,
                            'file_name': message.file.name.split('/')[-1] if message.file else None,
                            'created_at': message.created_at.isoformat(),
                            'is_read': message.is_read,
                        }
                    )
                    
                    # Отправляем уведомления в группы пользователей для обновления списка чатов
                    if chat_info:
                        chat_updated_at = await self.get_chat_updated_at()
                        
                        # Уведомление для пациента
                        patient_group = f'user_{chat_info["patient_id"]}_chats'
                        patient_unread = await self.get_unread_count(chat_info["patient_id"])
                        await self.channel_layer.group_send(
                            patient_group,
                            {
                                'type': 'new_chat_message',
                                'chat_id': self.chat_id,
                                'message_id': message.id,
                                'sender_id': message.sender.id,
                                'sender_username': message.sender.username,
                                'text': message.text[:100] if message.text else '',  # Первые 100 символов
                                'created_at': message.created_at.isoformat(),
                                'updated_at': chat_updated_at.isoformat() if chat_updated_at else message.created_at.isoformat(),
                                'unread_count': patient_unread,
                            }
                        )
                        
                        # Уведомление для доктора
                        if chat_info["doctor_id"]:
                            doctor_group = f'user_{chat_info["doctor_id"]}_chats'
                            doctor_unread = await self.get_unread_count(chat_info["doctor_id"])
                            await self.channel_layer.group_send(
                                doctor_group,
                                {
                                    'type': 'new_chat_message',
                                    'chat_id': self.chat_id,
                                    'message_id': message.id,
                                    'sender_id': message.sender.id,
                                    'sender_username': message.sender.username,
                                    'text': message.text[:100] if message.text else '',
                                    'created_at': message.created_at.isoformat(),
                                    'updated_at': chat_updated_at.isoformat() if chat_updated_at else message.created_at.isoformat(),
                                    'unread_count': doctor_unread,
                                }
                            )
                    
                    # Обновляем статус заявки
                    await self.update_request_status()
            
            elif message_type == 'typing':
                # Уведомление о наборе текста
                await self.channel_layer.group_send(
                    self.chat_group_name,
                    {
                        'type': 'typing_indicator',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'is_typing': data.get('is_typing', False)
                    }
                )
            
            elif message_type == 'read_messages':
                # Отметка сообщений как прочитанных
                message_ids = data.get('message_ids', [])
                await self.mark_messages_as_read(message_ids)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Неверный формат данных'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Ошибка: {str(e)}'
            }))
    
    async def chat_message(self, event):
        """Отправка сообщения клиенту"""
        # Отправляем сообщение только если это не отправитель
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'new_message',
                'message_id': event['message_id'],
                'sender_id': event['sender_id'],
                'sender_username': event['sender_username'],
                'sender_is_doctor': event['sender_is_doctor'],
                'sender_full_name': event['sender_full_name'],
                'text': event['text'],
                'file_url': event['file_url'],
                'file_name': event['file_name'],
                'created_at': event['created_at'],
                'is_read': event['is_read'],
            }))
        else:
            # Отправителю отправляем подтверждение
            await self.send(text_data=json.dumps({
                'type': 'message_sent',
                'message_id': event['message_id'],
                'created_at': event['created_at'],
            }))
    
    async def typing_indicator(self, event):
        """Отправка индикатора набора текста"""
        # Не отправляем себе
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    @database_sync_to_async
    def check_chat_access(self):
        """Проверка доступа пользователя к чату"""
        try:
            chat = Chat.objects.select_related('request__patient', 'request__doctor__user').get(pk=self.chat_id)
            user = self.user
            
            # Проверяем, является ли пользователь участником чата
            if hasattr(user, 'doctor'):
                # Пользователь - доктор
                return chat.request.doctor and chat.request.doctor.user == user
            else:
                # Пользователь - пациент
                return chat.request.patient == user
        except Chat.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, text, file_url):
        """Сохранение сообщения в БД"""
        try:
            chat = Chat.objects.get(pk=self.chat_id)
            message = Message.objects.create(
                chat=chat,
                sender=self.user,
                text=text,
            )
            # Обновляем время последнего обновления чата
            chat.updated_at = timezone.now()
            chat.save(update_fields=['updated_at'])
            # Если есть file_url, можно обработать загрузку файла
            # Пока оставляем только текст
            return message
        except Chat.DoesNotExist:
            return None
        except Exception as e:
            print(f"Ошибка сохранения сообщения: {e}")
            return None
    
    @database_sync_to_async
    def update_request_status(self):
        """Обновление статуса заявки при отправке сообщения"""
        try:
            chat = Chat.objects.select_related('request').get(pk=self.chat_id)
            request_obj = chat.request
            
            if hasattr(self.user, 'doctor'):
                request_obj.status = Request.Status.DOCTOR_REPLIED
            else:
                request_obj.status = Request.Status.WAITING_DOCTOR
            
            request_obj.save()
        except Exception as e:
            print(f"Ошибка обновления статуса: {e}")
    
    @database_sync_to_async
    def mark_messages_as_read(self, message_ids):
        """Отметка сообщений как прочитанных"""
        try:
            messages = Message.objects.filter(
                id__in=message_ids,
                chat_id=self.chat_id,
                is_read=False
            ).exclude(sender=self.user)
            
            for message in messages:
                message.mark_as_read()
        except Exception as e:
            print(f"Ошибка отметки сообщений: {e}")
    
    @database_sync_to_async
    def is_doctor(self, user):
        """Проверка, является ли пользователь доктором"""
        return hasattr(user, 'doctor')
    
    @database_sync_to_async
    def get_user_full_name(self, user):
        """Получение полного имени пользователя"""
        if hasattr(user, 'doctor'):
            return user.doctor.get_full_name()
        elif hasattr(user, 'profile'):
            return user.profile.get_full_name() or user.username
        return user.get_full_name() or user.username
    
    @database_sync_to_async
    def get_chat_info(self):
        """Получение информации о чате и участниках"""
        try:
            chat = Chat.objects.select_related('request__patient', 'request__doctor__user').get(pk=self.chat_id)
            return {
                'patient_id': chat.request.patient.id,
                'doctor_id': chat.request.doctor.user.id if chat.request.doctor else None,
            }
        except Chat.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_unread_count(self, user_id):
        """Получение количества непрочитанных сообщений для пользователя"""
        try:
            from django.contrib.auth.models import User
            user = User.objects.get(pk=user_id)
            chat = Chat.objects.get(pk=self.chat_id)
            return chat.messages.filter(is_read=False).exclude(sender=user).count()
        except Exception:
            return 0
    
    @database_sync_to_async
    def get_chat_updated_at(self):
        """Получение времени последнего обновления чата"""
        try:
            chat = Chat.objects.get(pk=self.chat_id)
            return chat.updated_at
        except Chat.DoesNotExist:
            return None


class ChatListConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer для обновления списка чатов в реальном времени"""
    
    async def connect(self):
        """Обработка подключения к WebSocket"""
        self.user = self.scope['user']
        
        # Проверяем доступ
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Группа для всех уведомлений пользователя
        self.user_group_name = f'user_{self.user.id}_chats'
        
        # Присоединяемся к группе пользователя
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Отправляем информацию о подключении
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Подключено к обновлениям чатов'
        }))
    
    async def disconnect(self, close_code):
        """Обработка отключения от WebSocket"""
        # Покидаем группу пользователя
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Обработка получения сообщения от клиента"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'mark_chat_read':
                # Отметка чата как прочитанного
                chat_id = data.get('chat_id')
                await self.mark_chat_as_read(chat_id)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Неверный формат данных'
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Ошибка: {str(e)}'
            }))
    
    async def new_chat_message(self, event):
        """Обработка нового сообщения в чате"""
        await self.send(text_data=json.dumps({
            'type': 'new_chat_message',
            'chat_id': event['chat_id'],
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_username': event['sender_username'],
            'text': event.get('text', ''),
            'created_at': event['created_at'],
            'unread_count': event.get('unread_count', 0),
        }))
    
    async def chat_updated(self, event):
        """Обработка обновления чата"""
        await self.send(text_data=json.dumps({
            'type': 'chat_updated',
            'chat_id': event['chat_id'],
            'updated_at': event['updated_at'],
            'unread_count': event.get('unread_count', 0),
        }))
    
    @database_sync_to_async
    def mark_chat_as_read(self, chat_id):
        """Отметка всех сообщений в чате как прочитанных"""
        try:
            from chat.models import Message
            messages = Message.objects.filter(
                chat_id=chat_id,
                is_read=False
            ).exclude(sender=self.user)
            
            for message in messages:
                message.mark_as_read()
        except Exception as e:
            print(f"Ошибка отметки чата как прочитанного: {e}")
