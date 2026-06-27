/* AutoHR — Interview list page
 * Модалка переноса собеседования.
 */

(function() {
    'use strict';

    function initInterviewList() {
        const urls = (window.AutoHR && window.AutoHR.urls && window.AutoHR.urls.interviews) || {};
        if (!urls.reschedule) return;

        function replacePlaceholder(url, id) {
            return url.replace('0', id);
        }

        window.openRescheduleModal = function(interviewId) {
            const form = document.getElementById('rescheduleForm');
            form.setAttribute('hx-post', replacePlaceholder(urls.reschedule, interviewId));
            form.setAttribute('hx-target', '#interview-wrap-' + interviewId);
            htmx.process(form);

            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            form.querySelector('input[name="date"]').min = tomorrow.toISOString().split('T')[0];

            new bootstrap.Modal(document.getElementById('rescheduleModal')).show();
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initInterviewList);
    } else {
        initInterviewList();
    }
})();