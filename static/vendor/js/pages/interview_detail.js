/* AutoHR — Interview detail page
 * AI score init + addToCalendar (Google Calendar) + copyToClipboard.
 */

(function() {
    'use strict';

    function initInterviewDetail() {
        // AI score — устанавливает CSS-переменную --score для conic-gradient
        const scoreCircle = document.querySelector('.ai-score-circle');
        if (scoreCircle) {
            const rawScore = parseFloat(scoreCircle.dataset.score);
            const scoreText = document.getElementById('score-text');
            if (scoreText && !isNaN(rawScore)) {
                scoreText.textContent = (rawScore * 100).toFixed(1) + '%';
            }
            if (!isNaN(rawScore)) {
                scoreCircle.style.setProperty('--score', rawScore);
            }
        }

        // Глобальные функции, вызываемые из onclick в шаблоне
        window.addToCalendar = function() {
            // Использует данные, переданные через data-* атрибуты на trigger-кнопке
            const btn = document.querySelector('[data-calendar-trigger]');
            if (!btn) return;

            const startDate = new Date(btn.dataset.start);
            const duration = parseInt(btn.dataset.duration || '60', 10);
            const endDate = new Date(startDate.getTime() + duration * 60000);
            const title = btn.dataset.title || 'Собеседование';
            const details = btn.dataset.details || '';

            const toGoogleFormat = function(d) {
                return d.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
            };

            const calendarUrl =
                'https://calendar.google.com/calendar/render?action=TEMPLATE' +
                '&text=' + encodeURIComponent(title) +
                '&dates=' + toGoogleFormat(startDate) + '/' + toGoogleFormat(endDate) +
                '&details=' + encodeURIComponent(details);

            window.open(calendarUrl, '_blank');
        };

        function fallbackCopyTextToClipboard(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.opacity = '0';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            try {
                document.execCommand('copy');
                AutoHR.showToast('Ссылка скопирована в буфер обмена', 'success');
            } catch (err) {
                console.error('Fallback copy failed: ', err);
            }
            document.body.removeChild(textArea);
        }

        window.copyToClipboard = function(text) {
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(function() {
                    AutoHR.showToast('Ссылка скопирована в буфер обмена', 'success');
                }).catch(function(err) {
                    console.error('Clipboard API failed: ', err);
                    fallbackCopyTextToClipboard(text);
                });
            } else {
                fallbackCopyTextToClipboard(text);
            }
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initInterviewDetail);
    } else {
        initInterviewDetail();
    }
})();