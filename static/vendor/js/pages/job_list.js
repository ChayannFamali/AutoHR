/* AutoHR — Job list page
 * Переключение вида (Список/Карточки) с сохранением в localStorage.
 */

(function() {
    'use strict';

    function initJobListView() {
        const listViewBtn = document.getElementById('listViewBtn');
        const cardViewBtn = document.getElementById('cardViewBtn');
        const listView = document.getElementById('listView');
        const cardView = document.getElementById('cardView');

        if (!listViewBtn || !cardViewBtn || !listView || !cardView) return;

        function switchToListView() {
            listViewBtn.classList.add('active');
            cardViewBtn.classList.remove('active');
            listView.classList.remove('d-none');
            cardView.classList.add('d-none');
        }

        function switchToCardView() {
            cardViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
            cardView.classList.remove('d-none');
            listView.classList.add('d-none');
        }

        const savedView = localStorage.getItem('jobsViewMode') || 'list';
        if (savedView === 'card') {
            switchToCardView();
        } else {
            switchToListView();
        }

        listViewBtn.addEventListener('click', function() {
            switchToListView();
            localStorage.setItem('jobsViewMode', 'list');
        });

        cardViewBtn.addEventListener('click', function() {
            switchToCardView();
            localStorage.setItem('jobsViewMode', 'card');
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initJobListView);
    } else {
        initJobListView();
    }
})();