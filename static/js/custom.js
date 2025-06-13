// AutoHR Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всех компонентов
    initFileUpload();
    initTooltips();
    initConfirmDialogs();
    initAjaxForms();
    initNotifications();
});

// Файловая загрузка с drag & drop
function initFileUpload() {
    const uploadAreas = document.querySelectorAll('.form-upload');
    
    uploadAreas.forEach(area => {
        const fileInput = area.querySelector('input[type="file"]');
        
        if (!fileInput) return;
        
        // Drag & Drop события
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });
        
        area.addEventListener('dragleave', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
        });
        
        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                updateFileUploadDisplay(area, files[0]);
            }
        });
        
        // Клик по области для выбора файла
        area.addEventListener('click', function() {
            fileInput.click();
        });
        
        // Изменение файла через input
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                updateFileUploadDisplay(area, this.files[0]);
            }
        });
    });
}

function updateFileUploadDisplay(area, file) {
    const fileName = file.name;
    const fileSize = formatFileSize(file.size);
    
    area.innerHTML = `
        <div class="text-success">
            <i class="fas fa-file-check fa-2x mb-2"></i>
            <p class="mb-1"><strong>${fileName}</strong></p>
            <p class="text-muted">${fileSize}</p>
        </div>
    `;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Инициализация tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Диалоги подтверждения
function initConfirmDialogs() {
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-confirm]')) {
            e.preventDefault();
            const message = e.target.getAttribute('data-confirm') || 'Вы уверены?';
            
            if (confirm(message)) {
                if (e.target.tagName === 'A') {
                    window.location.href = e.target.href;
                } else if (e.target.tagName === 'BUTTON') {
                    e.target.closest('form').submit();
                }
            }
        }
    });
}

// AJAX формы
function initAjaxForms() {
    document.addEventListener('submit', function(e) {
        if (e.target.matches('.ajax-form')) {
            e.preventDefault();
            submitAjaxForm(e.target);
        }
    });
}

function submitAjaxForm(form) {
    const formData = new FormData(form);
    const submitBtn = form.querySelector('[type="submit"]');
    
    // Показать загрузку
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add('loading');
    }
    
    fetch(form.action || window.location.href, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Успешно!', 'success');
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        } else {
            showNotification(data.message || 'Произошла ошибка', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Произошла ошибка при отправке формы', 'error');
    })
    .finally(() => {
        // Убрать загрузку
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove('loading');
        }
    });
}

// Уведомления
function initNotifications() {
    // Автоскрытие alert-ов через 5 секунд
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

function showNotification(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : `alert-${type}`;
    const alertHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Найти контейнер для уведомлений или создать
    let container = document.querySelector('.notifications-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'notifications-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    
    container.insertAdjacentHTML('beforeend', alertHTML);
    
    // Автоскрытие через 5 секунд
    setTimeout(() => {
        const alert = container.lastElementChild;
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

// Утилиты
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// AI Score цветовая индикация
function updateAIScores() {
    document.querySelectorAll('.ai-score').forEach(element => {
        const score = parseFloat(element.textContent);
        element.classList.remove('high', 'medium', 'low');
        
        if (score >= 0.7) {
            element.classList.add('high');
        } else if (score >= 0.4) {
            element.classList.add('medium');
        } else {
            element.classList.add('low');
        }
    });
}

// Запуск обновления AI scores при загрузке
document.addEventListener('DOMContentLoaded', updateAIScores);
