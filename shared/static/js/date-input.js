/**
 * Маска ввода для поля даты в формате dd.mm.yyyy
 */
document.addEventListener('DOMContentLoaded', function() {
    const dateInputs = document.querySelectorAll('.date-input');
    
    dateInputs.forEach(function(input) {
        // Обработка ввода
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, ''); // Убираем все нецифровые символы
            
            // Ограничиваем длину до 8 цифр (ddmmyyyy)
            if (value.length > 8) {
                value = value.substring(0, 8);
            }
            
            // Форматируем: dd.mm.yyyy
            let formatted = '';
            if (value.length > 0) {
                formatted = value.substring(0, 2);
                if (value.length > 2) {
                    formatted += '.' + value.substring(2, 4);
                }
                if (value.length > 4) {
                    formatted += '.' + value.substring(4, 8);
                }
            }
            
            e.target.value = formatted;
        });
        
        // Обработка вставки (paste)
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            let pasted = (e.clipboardData || window.clipboardData).getData('text');
            let value = pasted.replace(/\D/g, '');
            
            if (value.length > 8) {
                value = value.substring(0, 8);
            }
            
            let formatted = '';
            if (value.length > 0) {
                formatted = value.substring(0, 2);
                if (value.length > 2) {
                    formatted += '.' + value.substring(2, 4);
                }
                if (value.length > 4) {
                    formatted += '.' + value.substring(4, 8);
                }
            }
            
            input.value = formatted;
        });
        
        // Валидация при потере фокуса
        input.addEventListener('blur', function(e) {
            let value = e.target.value.trim();
            if (value && value.length === 10) {
                // Проверяем формат dd.mm.yyyy
                let parts = value.split('.');
                if (parts.length === 3) {
                    let day = parseInt(parts[0], 10);
                    let month = parseInt(parts[1], 10);
                    let year = parseInt(parts[2], 10);
                    
                    // Проверяем валидность даты
                    if (day < 1 || day > 31 || month < 1 || month > 12 || year < 1900 || year > 2100) {
                        e.target.classList.add('error');
                        return;
                    }
                    
                    // Проверяем, существует ли такая дата
                    let date = new Date(year, month - 1, day);
                    if (date.getDate() !== day || date.getMonth() !== month - 1 || date.getFullYear() !== year) {
                        e.target.classList.add('error');
                        return;
                    }
                    
                    e.target.classList.remove('error');
                } else {
                    e.target.classList.add('error');
                }
            } else if (value && value.length > 0) {
                e.target.classList.add('error');
            } else {
                e.target.classList.remove('error');
            }
        });
        
        // Убираем класс error при начале ввода
        input.addEventListener('focus', function(e) {
            e.target.classList.remove('error');
        });
    });
});

