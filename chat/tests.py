"""
Автотесты для приложения chat (заявки, чаты, сообщения)
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

from personal.models import UserProfile, Doctor
from chat.models import Request, Chat, Message


class RequestModelTest(TestCase):
    """Тесты для модели Request"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.patient)
        
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
    
    def test_create_request(self):
        """Тест создания заявки"""
        request = Request.objects.create(
            patient=self.patient,
            title='Консультация по питанию',
            description='Нужна консультация',
            specialization=Request.Specialization.NUTRITIONIST
        )
        
        self.assertEqual(request.patient, self.patient)
        self.assertEqual(request.title, 'Консультация по питанию')
        self.assertEqual(request.status, Request.Status.WAITING)
        self.assertIsNone(request.doctor)
    
    def test_request_status_choices(self):
        """Тест статусов заявки"""
        request = Request.objects.create(
            patient=self.patient,
            title='Тест',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST
        )
        
        # Проверяем все возможные статусы
        statuses = [choice[0] for choice in Request.Status.choices]
        self.assertIn('waiting', statuses)
        self.assertIn('assigned', statuses)
        self.assertIn('closed', statuses)
    
    def test_request_with_doctor(self):
        """Тест заявки с назначенным доктором"""
        request = Request.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            title='Тест',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST,
            status=Request.Status.ASSIGNED
        )
        
        self.assertEqual(request.doctor, self.doctor)
        self.assertEqual(request.status, Request.Status.ASSIGNED)
    
    def test_request_ordering(self):
        """Тест сортировки заявок"""
        request1 = Request.objects.create(
            patient=self.patient,
            title='Первая',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST
        )
        request2 = Request.objects.create(
            patient=self.patient,
            title='Вторая',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST
        )
        
        requests = Request.objects.all()
        # Новые заявки должны быть первыми
        self.assertEqual(requests[0], request2)
        self.assertEqual(requests[1], request1)


class ChatModelTest(TestCase):
    """Тесты для модели Chat"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.patient)
        
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        
        self.request = Request.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            title='Тест',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST,
            status=Request.Status.ASSIGNED
        )
    
    def test_create_chat(self):
        """Тест создания чата"""
        chat = Chat.objects.create(request=self.request)
        
        self.assertEqual(chat.request, self.request)
        self.assertIsNotNone(chat.created_at)
        self.assertIsNotNone(chat.updated_at)
    
    def test_chat_one_to_one_with_request(self):
        """Тест связи один-к-одному с заявкой"""
        chat1 = Chat.objects.create(request=self.request)
        
        # Нельзя создать второй чат для той же заявки
        with self.assertRaises(Exception):  # IntegrityError или ValidationError
            chat2 = Chat.objects.create(request=self.request)
    
    def test_get_last_message(self):
        """Тест получения последнего сообщения"""
        chat = Chat.objects.create(request=self.request)
        
        # Нет сообщений
        self.assertIsNone(chat.get_last_message())
        
        # Создаем сообщения
        message1 = Message.objects.create(
            chat=chat,
            sender=self.patient,
            text='Первое сообщение'
        )
        message2 = Message.objects.create(
            chat=chat,
            sender=self.doctor_user,
            text='Второе сообщение'
        )
        
        # Последнее сообщение должно быть message2
        self.assertEqual(chat.get_last_message(), message2)
    
    def test_get_unread_count(self):
        """Тест подсчета непрочитанных сообщений"""
        chat = Chat.objects.create(request=self.request)
        
        # Создаем сообщения
        Message.objects.create(
            chat=chat,
            sender=self.patient,
            text='Сообщение 1',
            is_read=False
        )
        Message.objects.create(
            chat=chat,
            sender=self.patient,
            text='Сообщение 2',
            is_read=True
        )
        Message.objects.create(
            chat=chat,
            sender=self.patient,
            text='Сообщение 3',
            is_read=False
        )
        
        # Для доктора должно быть 2 непрочитанных (исключая его собственные)
        unread = chat.get_unread_count_for_user(self.doctor_user)
        self.assertEqual(unread, 2)
        
        # Для пациента должно быть 0 (все сообщения от него)
        unread_patient = chat.get_unread_count_for_user(self.patient)
        self.assertEqual(unread_patient, 0)


class MessageModelTest(TestCase):
    """Тесты для модели Message"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.patient)
        
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        
        self.request = Request.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            title='Тест',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST,
            status=Request.Status.ASSIGNED
        )
        self.chat = Chat.objects.create(request=self.request)
    
    def test_create_message(self):
        """Тест создания сообщения"""
        message = Message.objects.create(
            chat=self.chat,
            sender=self.patient,
            text='Тестовое сообщение'
        )
        
        self.assertEqual(message.chat, self.chat)
        self.assertEqual(message.sender, self.patient)
        self.assertEqual(message.text, 'Тестовое сообщение')
        self.assertFalse(message.is_read)
        self.assertIsNone(message.read_at)
    
    def test_message_with_file(self):
        """Тест сообщения с файлом"""
        file = SimpleUploadedFile(
            "test_file.txt",
            b"file content",
            content_type="text/plain"
        )
        message = Message.objects.create(
            chat=self.chat,
            sender=self.patient,
            text='Сообщение с файлом',
            file=file
        )
        
        self.assertTrue(message.file)
        self.assertIn('uploads/chat/', message.file.name)
    
    def test_message_mark_as_read(self):
        """Тест отметки сообщения как прочитанного"""
        from django.utils import timezone
        
        message = Message.objects.create(
            chat=self.chat,
            sender=self.patient,
            text='Тестовое сообщение'
        )
        
        self.assertFalse(message.is_read)
        self.assertIsNone(message.read_at)
        
        message.mark_as_read()
        
        message.refresh_from_db()
        self.assertTrue(message.is_read)
        self.assertIsNotNone(message.read_at)
        self.assertAlmostEqual(
            message.read_at,
            timezone.now(),
            delta=timezone.timedelta(seconds=1)
        )
    
    def test_message_ordering(self):
        """Тест сортировки сообщений"""
        message1 = Message.objects.create(
            chat=self.chat,
            sender=self.patient,
            text='Первое'
        )
        message2 = Message.objects.create(
            chat=self.chat,
            sender=self.doctor_user,
            text='Второе'
        )
        
        messages = Message.objects.all()
        # Сообщения должны быть отсортированы по created_at
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)
    
    def test_message_can_be_empty_text_with_file(self):
        """Тест сообщения только с файлом (без текста)"""
        file = SimpleUploadedFile(
            "test_file.txt",
            b"file content",
            content_type="text/plain"
        )
        message = Message.objects.create(
            chat=self.chat,
            sender=self.patient,
            text='',  # Пустой текст
            file=file
        )
        
        self.assertEqual(message.text, '')
        self.assertTrue(message.file)


class RequestViewsTest(TestCase):
    """Тесты для views заявок"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()
        
        # Пациент
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.patient)
        
        # Доктор
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
    
    def test_create_request_requires_login(self):
        """Тест: создание заявки требует авторизации"""
        response = self.client.get(reverse('chat:request_create'))
        self.assertEqual(response.status_code, 302)  # Редирект на логин
    
    def test_create_request_as_patient(self):
        """Тест создания заявки пациентом"""
        self.client.login(username='patient', password='testpass123')
        
        response = self.client.get(reverse('chat:request_create'))
        self.assertEqual(response.status_code, 200)
        
        # Создаем заявку
        response = self.client.post(reverse('chat:request_create'), {
            'title': 'Тестовая заявка',
            'description': 'Описание проблемы',
            'specialization': Request.Specialization.NUTRITIONIST
        })
        
        self.assertEqual(response.status_code, 302)  # Редирект после создания
        self.assertTrue(Request.objects.filter(title='Тестовая заявка').exists())
        
        request = Request.objects.get(title='Тестовая заявка')
        self.assertEqual(request.patient, self.patient)
        self.assertEqual(request.status, Request.Status.WAITING)
    
    def test_create_request_as_doctor_forbidden(self):
        """Тест: доктор не может создавать заявки"""
        self.client.login(username='doctor', password='testpass123')
        
        response = self.client.get(reverse('chat:request_create'))
        # Должен быть редирект или 403
        self.assertIn(response.status_code, [302, 403])
    
    def test_doctor_requests_list(self):
        """Тест списка заявок для доктора"""
        self.client.login(username='doctor', password='testpass123')
        
        # Создаем заявку от пациента
        request = Request.objects.create(
            patient=self.patient,
            title='Тест',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST
        )
        
        response = self.client.get(reverse('chat:doctor_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(request, response.context['requests'])
    
    def test_accept_request(self):
        """Тест принятия заявки доктором"""
        self.client.login(username='doctor', password='testpass123')
        
        request = Request.objects.create(
            patient=self.patient,
            title='Тест',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST
        )
        
        response = self.client.post(reverse('chat:request_accept', args=[request.pk]))
        self.assertEqual(response.status_code, 302)  # Редирект
        
        request.refresh_from_db()
        self.assertEqual(request.doctor, self.doctor)
        self.assertEqual(request.status, Request.Status.ASSIGNED)
        self.assertTrue(Chat.objects.filter(request=request).exists())


class ChatViewsTest(TestCase):
    """Тесты для views чатов"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.client = Client()
        
        # Пациент
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.patient)
        
        # Доктор
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        
        # Заявка и чат
        self.request = Request.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            title='Тест',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST,
            status=Request.Status.ASSIGNED
        )
        self.chat = Chat.objects.create(request=self.request)
    
    def test_chat_detail_access_patient(self):
        """Тест доступа пациента к своему чату"""
        self.client.login(username='patient', password='testpass123')
        
        response = self.client.get(reverse('chat:chat_detail', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chat'], self.chat)
    
    def test_chat_detail_access_doctor(self):
        """Тест доступа доктора к своему чату"""
        self.client.login(username='doctor', password='testpass123')
        
        response = self.client.get(reverse('chat:chat_detail', args=[self.chat.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chat'], self.chat)
    
    def test_chat_detail_deny_access(self):
        """Тест запрета доступа к чужому чату"""
        # Создаем другого пользователя
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=other_user)
        
        self.client.login(username='other', password='testpass123')
        
        response = self.client.get(reverse('chat:chat_detail', args=[self.chat.pk]))
        # Должен быть 404 или редирект
        self.assertIn(response.status_code, [404, 302])
    
    def test_send_message(self):
        """Тест отправки сообщения"""
        self.client.login(username='patient', password='testpass123')
        
        response = self.client.post(
            reverse('chat:message_send', args=[self.chat.pk]),
            {'text': 'Тестовое сообщение'}
        )
        
        self.assertEqual(response.status_code, 302)  # Редирект
        self.assertTrue(Message.objects.filter(text='Тестовое сообщение').exists())
        
        message = Message.objects.get(text='Тестовое сообщение')
        self.assertEqual(message.sender, self.patient)
        self.assertEqual(message.chat, self.chat)
    
    def test_send_message_with_file(self):
        """Тест отправки сообщения с файлом"""
        self.client.login(username='patient', password='testpass123')
        
        file = SimpleUploadedFile(
            "test_file.txt",
            b"file content",
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('chat:message_send', args=[self.chat.pk]),
            {'text': 'Сообщение с файлом', 'file': file}
        )
        
        self.assertEqual(response.status_code, 302)
        message = Message.objects.filter(text='Сообщение с файлом').first()
        self.assertIsNotNone(message)
        self.assertTrue(message.file)
    
    def test_mark_messages_as_read_on_view(self):
        """Тест автоматической отметки сообщений как прочитанных при открытии чата"""
        # Создаем непрочитанное сообщение от доктора
        message = Message.objects.create(
            chat=self.chat,
            sender=self.doctor_user,
            text='Непрочитанное сообщение',
            is_read=False
        )
        
        self.client.login(username='patient', password='testpass123')
        response = self.client.get(reverse('chat:chat_detail', args=[self.chat.pk]))
        
        message.refresh_from_db()
        self.assertTrue(message.is_read)


class ChatFormsTest(TestCase):
    """Тесты для форм чата"""
    
    def setUp(self):
        """Подготовка тестовых данных"""
        from chat.forms import RequestCreateForm, MessageCreateForm
        
        self.patient = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.patient)
        
        self.request = Request.objects.create(
            patient=self.patient,
            title='Тест',
            description='Описание',
            specialization=Request.Specialization.NUTRITIONIST
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor',
            email='doctor@test.com',
            password='testpass123'
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            first_name='Доктор',
            last_name='Тестов',
            specialization=Doctor.Specialization.NUTRITIONIST
        )
        
        self.request.doctor = self.doctor
        self.request.status = Request.Status.ASSIGNED
        self.request.save()
        
        self.chat = Chat.objects.create(request=self.request)
    
    def test_request_create_form_valid(self):
        """Тест валидной формы создания заявки"""
        from chat.forms import RequestCreateForm
        
        form = RequestCreateForm(data={
            'title': 'Тестовая заявка',
            'description': 'Описание проблемы',
            'specialization': Request.Specialization.NUTRITIONIST
        })
        self.assertTrue(form.is_valid())
    
    def test_request_create_form_invalid(self):
        """Тест невалидной формы создания заявки"""
        from chat.forms import RequestCreateForm
        
        # Пустая форма
        form = RequestCreateForm(data={})
        self.assertFalse(form.is_valid())
    
    def test_message_create_form_with_text(self):
        """Тест формы сообщения с текстом"""
        from chat.forms import MessageCreateForm
        
        form = MessageCreateForm(data={'text': 'Тестовое сообщение'})
        self.assertTrue(form.is_valid())
    
    def test_message_create_form_with_file(self):
        """Тест формы сообщения с файлом"""
        from chat.forms import MessageCreateForm
        
        file = SimpleUploadedFile(
            "test_file.txt",
            b"file content",
            content_type="text/plain"
        )
        form = MessageCreateForm(data={}, files={'file': file})
        self.assertTrue(form.is_valid())
    
    def test_message_create_form_empty(self):
        """Тест формы сообщения без текста и файла"""
        from chat.forms import MessageCreateForm
        
        form = MessageCreateForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('Необходимо ввести текст сообщения или прикрепить файл.', str(form.errors))
