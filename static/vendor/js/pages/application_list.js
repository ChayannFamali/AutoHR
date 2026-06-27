/* AutoHR — Application list page
 * Модалки: детали заявки, планирование собеседования, добавление заметки.
 * Использует URL templates через глобальную переменную window.AutoHR.urls.applications.
 */

(function() {
    'use strict';

    function initApplicationList() {
        const urls = (window.AutoHR && window.AutoHR.urls && window.AutoHR.urls.applications) || {};
        if (!urls.detail) return; // URLs не переданы — выходим

        function replacePlaceholder(url, id) {
            return url.replace('0', id);
        }

        window.openDetailModal = function(applicationId) {
            const content = document.getElementById('detailModalContent');
            content.innerHTML = '<div class="text-center py-5"><i class="fas fa-spinner fa-spin fa-2x text-muted"></i></div>';
            htmx.ajax('GET', replacePlaceholder(urls.detail, applicationId), {
                target: '#detailModalContent',
                swap: 'innerHTML',
            });
            new bootstrap.Modal(document.getElementById('detailModal')).show();
        };

        window.openScheduleModal = function(applicationId) {
            const modal = document.getElementById('scheduleModal');
            modal.dataset.applicationId = applicationId;
            const form = modal.querySelector('form');
            form.setAttribute('hx-post', replacePlaceholder(urls.schedule, applicationId));
            htmx.process(form);
            new bootstrap.Modal(modal).show();
        };

        window.openNoteModal = function(applicationId) {
            const modal = document.getElementById('addNoteModal');
            const form = modal.querySelector('form');
            form.setAttribute('hx-post', replacePlaceholder(urls.addNote, applicationId));
            form.setAttribute('hx-target', '#notes-section-' + applicationId);
            htmx.process(form);
            document.getElementById('noteText').value = '';
            new bootstrap.Modal(modal).show();
        };

        window.updateApplicationStatusFromModal = function(applicationId, status) {
            htmx.ajax('POST', replacePlaceholder(urls.updateStatus, applicationId), {
                target: '#application-row-' + applicationId,
                swap: 'outerHTML',
                values: { status: status },
            });
            bootstrap.Modal.getInstance(document.getElementById('detailModal')).hide();
        };

        window.scheduleFromModal = function(applicationId) {
            bootstrap.Modal.getInstance(document.getElementById('detailModal')).hide();
            setTimeout(function() { window.openScheduleModal(applicationId); }, 300);
        };

        window.openDetailModalForNote = function(applicationId) {
            window.openDetailModal(applicationId);
            setTimeout(function() { window.openNoteModal(applicationId); }, 500);
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initApplicationList);
    } else {
        initApplicationList();
    }
})();