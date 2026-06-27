/* AutoHR — Resume detail page
 * Toggle "Показать/скрыть полный текст" для extracted text.
 */

(function() {
    'use strict';

    function initResumeDetail() {
        const showFullTextBtn = document.getElementById('showFullText');
        if (!showFullTextBtn) return;

        showFullTextBtn.addEventListener('click', function() {
            const fullText = document.querySelector('.full-text');
            const extractedText = document.querySelector('.extracted-text');

            if (!fullText || !extractedText) return;

            if (fullText.classList.contains('d-none')) {
                fullText.classList.remove('d-none');
                extractedText.style.maxHeight = 'none';
                this.innerHTML = '<i class="fas fa-compress me-1"></i>Скрыть полный текст';
            } else {
                fullText.classList.add('d-none');
                extractedText.style.maxHeight = '300px';
                this.innerHTML = '<i class="fas fa-expand me-1"></i>Показать полный текст';
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initResumeDetail);
    } else {
        initResumeDetail();
    }
})();