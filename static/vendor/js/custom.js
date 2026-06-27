/* AutoHR — единый JS-файл
 * Глобальные функции доступны как window.AutoHR.*
 * Никаких inline <script> в шаблонах — глобальные обработчики регистрируются здесь.
 */

(function() {
    'use strict';

    const AutoHR = {
        // ===================== Утилиты =====================

        getCookie(name) {
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
        },

        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        // ===================== Toast-уведомления =====================

        showToast(message, type = 'info', duration = 4000) {
            type = type === 'error' ? 'error' : type;
            const iconMap = {
                success: 'check-circle',
                error: 'exclamation-circle',
                warning: 'exclamation-triangle',
                info: 'info-circle',
            };

            let container = document.querySelector('.toast-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'toast-container';
                document.body.appendChild(container);
            }

            const toast = document.createElement('div');
            toast.className = `autohr-toast toast-${type}`;
            toast.innerHTML = `
                <i class="fas fa-${iconMap[type] || 'info-circle'} toast-icon"></i>
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close" aria-label="Close"></button>
            `;

            container.appendChild(toast);

            const close = () => {
                toast.classList.add('fade-out');
                setTimeout(() => toast.remove(), 300);
            };

            toast.querySelector('.btn-close').addEventListener('click', close);
            setTimeout(close, duration);
        },

        // Backward-compat алиас для старого `showNotification`
        showNotification(message, type) {
            return this.showToast(message, type);
        },

        // ===================== Подтверждения =====================

        confirm(message) {
            return window.confirm(message);
        },

        // ===================== File upload (drag & drop) =====================

        initFileUpload() {
            document.querySelectorAll('.form-upload').forEach((area) => {
                const fileInput = area.querySelector('input[type="file"]');
                if (!fileInput) return;

                area.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    area.classList.add('dragover');
                });

                area.addEventListener('dragleave', (e) => {
                    e.preventDefault();
                    area.classList.remove('dragover');
                });

                area.addEventListener('drop', (e) => {
                    e.preventDefault();
                    area.classList.remove('dragover');
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        fileInput.files = files;
                        this._renderFileUpload(area, files[0]);
                    }
                });

                area.addEventListener('click', () => fileInput.click());

                fileInput.addEventListener('change', function() {
                    if (this.files.length > 0) {
                        AutoHR._renderFileUpload(area, this.files[0]);
                    }
                });
            });
        },

        _renderFileUpload(area, file) {
            area.innerHTML = `
                <div class="text-success">
                    <i class="fas fa-file-check fa-2x mb-2"></i>
                    <p class="mb-1"><strong>${file.name}</strong></p>
                    <p class="text-muted">${this.formatFileSize(file.size)}</p>
                </div>
            `;
        },

        // ===================== Tooltips =====================

        initTooltips() {
            document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
                new bootstrap.Tooltip(el);
            });
        },

        // ===================== Подтверждение через data-confirm =====================

        initConfirmDialogs() {
            document.addEventListener('click', (e) => {
                const target = e.target.closest('[data-confirm]');
                if (!target) return;

                e.preventDefault();
                const message = target.getAttribute('data-confirm') || 'Вы уверены?';

                if (window.confirm(message)) {
                    if (target.tagName === 'A') {
                        window.location.href = target.href;
                    } else if (target.tagName === 'BUTTON') {
                        const form = target.closest('form');
                        if (form) form.submit();
                    }
                }
            });
        },

        // ===================== Автоскрытие alert-ов =====================

        initAlerts() {
            document.querySelectorAll('.alert:not(.alert-permanent)').forEach((alert) => {
                setTimeout(() => {
                    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                    bsAlert.close();
                }, 5000);
            });
        },

        // ===================== AI Score цвета =====================

        updateAIScores() {
            document.querySelectorAll('.ai-score').forEach((element) => {
                const score = parseFloat(element.textContent);
                element.classList.remove('high', 'medium', 'low');
                if (isNaN(score)) return;
                if (score >= 0.7) {
                    element.classList.add('high');
                } else if (score >= 0.4) {
                    element.classList.add('medium');
                } else {
                    element.classList.add('low');
                }
            });
        },

        // ===================== HTMX-события =====================

        initHtmxEvents() {
            // Показываем toast после HTMX-запроса, если сервер вернул HX-Trigger
            document.body.addEventListener('htmx:afterRequest', (evt) => {
                const trigger = evt.detail.xhr.getResponseHeader('HX-Trigger');
                if (!trigger) return;

                try {
                    const payload = JSON.parse(trigger);
                    if (payload.showToast) {
                        this.showToast(payload.showToast.message, payload.showToast.type || 'info');
                    }
                } catch (e) {
                    // Просто строка — показать как info
                    this.showToast(trigger, 'info');
                }
            });

            // Показываем глобальный индикатор на время запроса
            document.body.addEventListener('htmx:beforeSend', () => {
                document.body.classList.add('htmx-loading');
            });
            document.body.addEventListener('htmx:afterRequest', () => {
                document.body.classList.remove('htmx-loading');
            });
        },

        // ===================== Theme (dark/light) =====================

        theme: {
            STORAGE_KEY: 'autohr-theme',

            get() {
                try {
                    return localStorage.getItem(this.STORAGE_KEY) || '';
                } catch (e) {
                    return '';
                }
            },

            set(theme) {
                try {
                    localStorage.setItem(this.STORAGE_KEY, theme);
                } catch (e) {}
                document.documentElement.setAttribute('data-theme', theme);
                window.dispatchEvent(new CustomEvent('theme-changed', { detail: { theme } }));
            },

            toggle() {
                const current = this.get() ||
                    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
                this.set(current === 'light' ? 'dark' : 'light');
            },

            init() {
                // Следим за сменой системной темы (если пользователь не выбрал явно)
                window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                    if (!this.get()) {
                        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
                        window.dispatchEvent(new CustomEvent('theme-changed', {
                            detail: { theme: e.matches ? 'dark' : 'light' }
                        }));
                    }
                });
            },
        },

        // ===================== Глобальный обработчик ошибок HTMX =====================

        init() {
            document.addEventListener('DOMContentLoaded', () => {
                this.initFileUpload();
                this.initTooltips();
                this.initConfirmDialogs();
                this.initAlerts();
                this.updateAIScores();
                this.initHtmxEvents();
            });
            this.theme.init();
        },
    };

    // Экспорт
    window.AutoHR = AutoHR;
    AutoHR.init();
})();