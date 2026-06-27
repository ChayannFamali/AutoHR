/* AutoHR — Resume upload page
 * Drag & drop + submit loading state.
 * Использует класс .upload-area (отличный от .form-upload в custom.js).
 */

(function() {
    'use strict';

    function initResumeUpload() {
        const fileInput = document.querySelector('input[type="file"]');
        const uploadArea = document.querySelector('.upload-area');
        const fileInfo = document.getElementById('file-info');
        const fileName = document.getElementById('file-name');
        const fileSize = document.getElementById('file-size');
        const uploadBtn = document.getElementById('uploadBtn');
        const uploadForm = document.getElementById('uploadForm');

        if (!fileInput || !uploadArea) return;

        function handleFileSelect(file) {
            if (file && fileName && fileSize && fileInfo) {
                fileName.textContent = file.name;
                fileSize.textContent = AutoHR.formatFileSize(file.size);
                fileInfo.classList.remove('d-none');
            }
        }

        fileInput.addEventListener('change', function(e) {
            handleFileSelect(e.target.files[0]);
        });

        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');

            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFileSelect(files[0]);
            }
        });

        if (uploadForm) {
            uploadForm.addEventListener('submit', function() {
                if (uploadBtn) {
                    uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Загрузка...';
                    uploadBtn.disabled = true;
                }
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initResumeUpload);
    } else {
        initResumeUpload();
    }
})();