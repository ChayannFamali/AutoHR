/* AutoHR — Dashboard analytics
 * Chart.js initialization + HTMX metric loaders.
 * Читает URL endpoints из window.AutoHR.urls.dashboard.
 */

(function() {
    'use strict';

    function initDashboard() {
        if (!window.Chart) return;

        Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
        Chart.defaults.color = '#64748B';

        const urls = (window.AutoHR && window.AutoHR.urls && window.AutoHR.urls.dashboard) || {};

        // HTMX-load метрик
        document.body.addEventListener('htmx:afterRequest', function(evt) {
            if (!evt.detail.successful) return;
            const trigger = evt.detail.xhr.getResponseHeader('HX-Trigger');
            if (!trigger) return;

            try {
                const data = JSON.parse(evt.detail.xhr.response);
                const elt = evt.detail.target;
                if (!elt) return;

                if (elt.querySelector('#timeToHireValue')) {
                    const v = elt.querySelector('#timeToHireValue');
                    const l = elt.querySelector('#timeToHireLabel');
                    if (data.avg_days === null) {
                        v.textContent = '—';
                        l.textContent = 'Нет данных';
                    } else {
                        v.textContent = data.avg_days;
                        l.textContent = 'Дней до найма (n=' + data.sample_size + ')';
                    }
                } else if (elt.querySelector('#conversionRateValue')) {
                    const v = elt.querySelector('#conversionRateValue');
                    if (data.data && data.data.length > 0) {
                        v.textContent = data.data[0] + '%';
                    }
                }
            } catch (e) {
                // Ignore parse errors
            }
        });

        // Утилита: загрузить данные и отрендерить chart
        function loadChart(canvasId, url, options) {
            if (!url) return;
            const canvas = document.getElementById(canvasId);
            if (!canvas) return;

            fetch(url)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    const ctx = canvas.getContext('2d');
                    new Chart(ctx, Object.assign({
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: 'Количество',
                                data: data.data,
                                backgroundColor: options.colors || '#3b82f6',
                                borderRadius: 5,
                            }],
                        },
                    }, options.config));
                });
        }

        // Динамика заявок (line)
        loadChart('applicationsChart', urls.applicationsChart, {
            config: {
                type: 'line',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
                },
            },
            colors: 'rgba(79, 70, 229, 0.1)',
        });

        // Распределение AI оценок (bar)
        loadChart('aiScoresChart', urls.aiScores, {
            config: {
                type: 'bar',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } },
                },
            },
            colors: ['#ef4444', '#f97316', '#eab308', '#22c55e', '#10b981'],
        });

        // Топ навыков (horizontal bar)
        loadChart('skillsChart', urls.popularSkills, {
            config: {
                type: 'bar',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: { legend: { display: false } },
                    scales: { x: { beginAtZero: true } },
                },
            },
            colors: '#8b5cf6',
        });

        // Статусы заявок (doughnut)
        loadChart('statusChart', urls.applicationStatus, {
            config: {
                type: 'doughnut',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } },
                },
            },
            colors: ['#fbbf24', '#3b82f6', '#10b981', '#ef4444', '#8b5cf6'],
        });

        // Топ вакансий (bar)
        loadChart('topJobsChart', urls.topJobs, {
            config: {
                type: 'bar',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true }, x: { ticks: { maxRotation: 45 } } },
                },
            },
            colors: '#06b6d4',
        });

        // Обработка резюме (pie)
        loadChart('resumeProcessingChart', urls.resumeProcessing, {
            config: {
                type: 'pie',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } },
                },
            },
            colors: ['#64748b', '#f59e0b', '#10b981', '#ef4444'],
        });

        // Воронка рекрутинга (horizontal bar, multi-color)
        loadChart('funnelChart', urls.recruitmentFunnel, {
            config: {
                type: 'bar',
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { x: { beginAtZero: true } },
                },
            },
            colors: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'],
        });

        // Конверсия по этапам (bar)
        loadChart('conversionChart', urls.conversionRates, {
            config: {
                type: 'bar',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { callbacks: { label: function(ctx) { return ctx.parsed.y + '%'; } } },
                    },
                    scales: { y: { beginAtZero: true, ticks: { callback: function(v) { return v + '%'; } } } },
                },
            },
            colors: '#10b981',
        });

        // Топ работодателей (bar с двумя datasets)
        const topEmployersCanvas = document.getElementById('topEmployersChart');
        if (topEmployersCanvas && urls.topEmployers) {
            fetch(urls.topEmployers)
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    const ctx = topEmployersCanvas.getContext('2d');
                    new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: data.labels,
                            datasets: [
                                { label: 'Вакансий', data: data.jobs_data, backgroundColor: '#3b82f6', borderRadius: 5 },
                                { label: 'Откликов', data: data.apps_data, backgroundColor: '#8b5cf6', borderRadius: 5 },
                            ],
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: { y: { beginAtZero: true }, x: { ticks: { maxRotation: 45 } } },
                        },
                    });
                });
        }
    }

    // Запуск после загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDashboard);
    } else {
        initDashboard();
    }
})();