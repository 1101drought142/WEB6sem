/**
 * Обработчик формы обратной связи с использованием Fetch API
 * Отправляет данные асинхронно без перезагрузки страницы
 */

document.addEventListener('DOMContentLoaded', function() {
    const feedbackForm = document.querySelector('.feedback-form');
    
    if (!feedbackForm) {
        console.warn('Форма обратной связи не найдена на странице');
        return;
    }
    
    feedbackForm.addEventListener('submit', async function(e) {
        e.preventDefault(); // Предотвращаем стандартную отправку формы
        
        // Получаем кнопку отправки
        const submitButton = feedbackForm.querySelector('.feedback-submit-btn');
        const originalButtonText = submitButton.textContent;
        
        // Очищаем предыдущие ошибки
        clearErrors();
        
        // Показываем состояние загрузки
        submitButton.disabled = true;
        submitButton.textContent = 'Отправка...';
        submitButton.classList.add('loading');
        
        // Собираем данные формы
        const formData = new FormData(feedbackForm);
        
        try {
            // Отправляем запрос
            const response = await fetch('/api/feedback/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    // CSRF токен уже в FormData из {% csrf_token %}
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Успешная отправка
                showSuccessMessage(data.message);
                feedbackForm.reset(); // Очищаем форму
                
                // Прокручиваем к сообщению успеха
                scrollToNotifications();
                
            } else {
                // Ошибки валидации
                showErrors(data.errors, data.message);
                scrollToNotifications();
            }
            
        } catch (error) {
            // Ошибка сети или сервера
            console.error('Ошибка отправки формы:', error);
            showErrorMessage('Произошла ошибка при отправке формы. Пожалуйста, попробуйте позже.');
            
        } finally {
            // Восстанавливаем кнопку
            submitButton.disabled = false;
            submitButton.textContent = originalButtonText;
            submitButton.classList.remove('loading');
        }
    });
});


/**
 * Отображает сообщение об успешной отправке
 */
function showSuccessMessage(message) {
    const container = getNotificationsContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = message;
    
    container.appendChild(alertDiv);
    
    // Автоматически скрываем через 5 секунд
    setTimeout(() => {
        alertDiv.style.opacity = '0';
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}


/**
 * Отображает сообщение об ошибке
 */
function showErrorMessage(message) {
    const container = getNotificationsContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-error';
    alertDiv.textContent = message;
    
    container.appendChild(alertDiv);
}


/**
 * Отображает ошибки валидации полей формы
 */
function showErrors(errors, generalMessage) {
    // Показываем общее сообщение
    if (generalMessage) {
        showErrorMessage(generalMessage);
    }
    
    // Показываем ошибки для каждого поля
    for (const [fieldName, errorList] of Object.entries(errors)) {
        if (fieldName === 'general') {
            // Общие ошибки формы
            errorList.forEach(error => showErrorMessage(error));
        } else {
            // Ошибки конкретных полей
            const fieldWrapper = document.querySelector(`[name="${fieldName}"]`)?.closest('.form-group');
            
            if (fieldWrapper) {
                // Удаляем старый список ошибок, если есть
                const oldErrorList = fieldWrapper.querySelector('.error-list');
                if (oldErrorList) {
                    oldErrorList.remove();
                }
                
                // Создаем новый список ошибок
                const errorListEl = document.createElement('ul');
                errorListEl.className = 'error-list';
                
                errorList.forEach(error => {
                    const li = document.createElement('li');
                    li.textContent = error;
                    errorListEl.appendChild(li);
                });
                
                // Добавляем после поля ввода
                const inputField = fieldWrapper.querySelector('input, textarea');
                if (inputField) {
                    inputField.classList.add('error');
                    inputField.insertAdjacentElement('afterend', errorListEl);
                }
                
                // Показываем ошибку и в уведомлениях
                const fieldLabel = fieldWrapper.querySelector('label')?.textContent || fieldName;
                console.log(fieldLabel);
                errorList.forEach(error => {
                    showErrorMessage(`${fieldLabel} ${error}`);
                });
            }
        }
    }
}


/**
 * Очищает все ошибки формы
 */
function clearErrors() {
    // Удаляем все уведомления
    const container = getNotificationsContainer();
    container.innerHTML = '';
    
    // Удаляем ошибки под полями
    document.querySelectorAll('.error-list').forEach(el => el.remove());
    
    // Убираем класс ошибки с полей
    document.querySelectorAll('.form-control.error').forEach(el => {
        el.classList.remove('error');
    });
}


/**
 * Получает или создает контейнер для уведомлений
 */
function getNotificationsContainer() {
    let container = document.querySelector('.notifications-container');
    
    if (!container) {
        container = document.createElement('div');
        container.className = 'notifications-container';
        
        // Вставляем после header
        const header = document.querySelector('header');
        if (header) {
            header.insertAdjacentElement('afterend', container);
        } else {
            document.body.insertAdjacentElement('afterbegin', container);
        }
    }
    
    return container;
}


/**
 * Прокручивает страницу к уведомлениям
 */
function scrollToNotifications() {
    const container = getNotificationsContainer();
    if (container.children.length > 0) {
        container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}
