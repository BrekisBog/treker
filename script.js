class BadHabitTracker {
    constructor() {
        this.apiBase = 'http://localhost:8000';
        this.currentTab = 'habits';
        this.chart = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.showTab('habits');
        this.loadHabits();
        this.setDefaultDate();
        this.setupRangeSliders();
    }

    setupEventListeners() {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.getAttribute('data-tab');
                this.showTab(tab);
            });
        });

        document.getElementById('habit-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addHabit();
        });

        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('completion-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveCompletion();
        });

        window.addEventListener('click', (e) => {
            const modal = document.getElementById('completion-modal');
            if (e.target === modal) {
                this.closeModal();
            }
        });

        // Закрытие модального окна по ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    setupRangeSliders() {
        const cravingSlider = document.getElementById('craving-level');
        const resistanceSlider = document.getElementById('resistance-level');
        const cravingValue = document.getElementById('craving-value');
        const resistanceValue = document.getElementById('resistance-value');

        cravingSlider.addEventListener('input', (e) => {
            cravingValue.textContent = e.target.value;
        });

        resistanceSlider.addEventListener('input', (e) => {
            resistanceValue.textContent = e.target.value;
        });
    }

    setDefaultDate() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('completion-date').value = today;
    }

    async showTab(tabName) {
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;

        if (tabName === 'habits') {
            await this.loadHabits();
        } else if (tabName === 'analytics') {
            await this.loadAnalytics();
        }
    }

    async loadHabits() {
        try {
            this.showLoading('habits-list', 'Загрузка привычек...');
            const response = await fetch(`${this.apiBase}/habits/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const habits = await response.json();
            this.renderHabits(habits);
        } catch (error) {
            console.error('Error loading habits:', error);
            this.showError('Ошибка загрузки привычек');
            this.renderHabits([]);
        }
    }

    showLoading(containerId, message = 'Загрузка...') {
        const container = document.getElementById(containerId);
        container.innerHTML = `
            <div class="loading" style="text-align: center; padding: 40px; color: #6c757d;">
                <div style="margin-bottom: 10px;">⏳</div>
                ${message}
            </div>
        `;
    }

    renderHabits(habits) {
        const container = document.getElementById('habits-list');

        if (habits.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #6c757d;">
                    <p>У вас пока нет отслеживаемых вредных привычек.</p>
                    <p>Добавьте первую привычку для отслеживания!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = habits.map(habit => `
            <div class="habit-card" data-habit-id="${habit.id}">
                <div class="habit-header">
                    <div>
                        <h3>${this.escapeHtml(habit.name)}</h3>
                        <span class="difficulty-badge difficulty-${habit.difficulty_level}">
                            ${this.getDifficultyText(habit.difficulty_level)}
                        </span>
                    </div>
                    <button class="btn-danger" onclick="tracker.deleteHabit(${habit.id})" title="Удалить привычку">
                        Удалить
                    </button>
                </div>

                <p>${habit.description ? this.escapeHtml(habit.description) : 'Без описания'}</p>

                ${habit.motivation_text ? `
                    <div class="motivation-text">${this.escapeHtml(habit.motivation_text)}</div>
                ` : ''}

                <div class="habit-meta">
                    <span>${this.getFrequencyText(habit.frequency)}</span>
                    <span>Цель: избегать</span>
                </div>

                <div class="habit-actions">
                    <button class="btn-success" onclick="tracker.openCompletionModal(${habit.id})">
                        Отметить день борьбы
                    </button>
                    <button class="btn-secondary" onclick="tracker.viewCompletions(${habit.id})">
                        Статистика
                    </button>
                </div>
            </div>
        `).join('');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    getDifficultyText(level) {
        const levels = {
            'easy': 'Легко отказаться',
            'medium': 'Средняя сложность',
            'hard': 'Очень сложно'
        };
        return levels[level] || level;
    }

    getFrequencyText(frequency) {
        const frequencies = {
            'daily': 'Ежедневно',
            'weekly': 'Несколько раз в неделю',
            'monthly': 'Несколько раз в месяц'
        };
        return frequencies[frequency] || frequency;
    }

    async addHabit() {
        const name = document.getElementById('habit-name').value.trim();
        if (!name) {
            this.showError('Введите название привычки');
            return;
        }

        const formData = {
            name: name,
            description: document.getElementById('habit-desc').value.trim(),
            habit_type: 'bad',
            frequency: document.getElementById('habit-frequency').value,
            target_count: 1,
            motivation_text: document.getElementById('motivation-text').value.trim(),
            difficulty_level: document.getElementById('difficulty-level').value
        };

        try {
            const response = await fetch(`${this.apiBase}/habits/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showSuccess('Вредная привычка добавлена для отслеживания!');
                document.getElementById('habit-form').reset();
                this.showTab('habits');
                await this.loadHabits();
            } else {
                const errorText = await response.text();
                throw new Error(errorText || 'Failed to add habit');
            }
        } catch (error) {
            console.error('Error adding habit:', error);
            this.showError('Ошибка при добавлении привычки: ' + error.message);
        }
    }

    async deleteHabit(habitId) {
        if (!confirm('Вы уверены, что хотите удалить эту привычку из отслеживания?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/habits/${habitId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showSuccess('Привычка удалена из отслеживания!');
                await this.loadHabits();
            } else {
                throw new Error('Failed to delete habit');
            }
        } catch (error) {
            console.error('Error deleting habit:', error);
            this.showError('Ошибка при удалении привычки');
        }
    }

    openCompletionModal(habitId) {
        document.getElementById('modal-habit-id').value = habitId;
        const modal = document.getElementById('completion-modal');
        modal.style.display = 'block';
        
        // Блокируем прокрутку основного контента
        document.body.style.overflow = 'hidden';
        document.documentElement.style.overflow = 'hidden';
        
        // Прокручиваем модальное окно вверх при открытии
        modal.scrollTop = 0;
        
        // Фокусируемся на первом поле формы
        setTimeout(() => {
            document.getElementById('completion-date').focus();
        }, 100);
    }

    closeModal() {
        const modal = document.getElementById('completion-modal');
        modal.style.display = 'none';
        
        // Восстанавливаем прокрутку основного контента
        document.body.style.overflow = 'auto';
        document.documentElement.style.overflow = 'auto';
        
        document.getElementById('completion-form').reset();
        this.setDefaultDate();

        // Сбрасываем слайдеры
        document.getElementById('craving-level').value = 0;
        document.getElementById('resistance-level').value = 0;
        document.getElementById('craving-value').textContent = '0';
        document.getElementById('resistance-value').textContent = '0';
    }

    async saveCompletion() {
        const habitId = parseInt(document.getElementById('modal-habit-id').value);
        if (!habitId) {
            this.showError('Ошибка: не выбрана привычка');
            return;
        }

        const formData = {
            habit_id: habitId,
            completion_date: document.getElementById('completion-date').value,
            completed: document.getElementById('completed-checkbox').checked,
            notes: document.getElementById('completion-notes').value.trim(),
            craving_level: parseInt(document.getElementById('craving-level').value),
            resistance_level: parseInt(document.getElementById('resistance-level').value)
        };

        // Валидация даты
        if (!formData.completion_date) {
            this.showError('Выберите дату');
            return;
        }

        try {
            const response = await fetch(`${this.apiBase}/habits/complete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                this.showSuccess('Данные о дне борьбы сохранены!');
                this.closeModal();
                await this.loadHabits();
                
                // Если открыта вкладка аналитики, обновляем её
                if (this.currentTab === 'analytics') {
                    await this.loadAnalytics();
                }
            } else {
                const errorText = await response.text();
                throw new Error(errorText || 'Failed to save completion');
            }
        } catch (error) {
            console.error('Error saving completion:', error);
            this.showError('Ошибка при сохранении данных: ' + error.message);
        }
    }

    async loadAnalytics() {
        try {
            this.showLoading('stats-grid', 'Загрузка аналитики...');
            const response = await fetch(`${this.apiBase}/analytics/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const analytics = await response.json();
            this.renderAnalytics(analytics);
        } catch (error) {
            console.error('Error loading analytics:', error);
            this.showError('Ошибка загрузки аналитики');
            this.renderAnalytics({ total_stats: {}, habit_stats: [] });
        }
    }

    renderAnalytics(analytics) {
        const statsGrid = document.getElementById('stats-grid');

        if (!analytics.total_stats || Object.keys(analytics.total_stats).length === 0) {
            statsGrid.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #6c757d; grid-column: 1 / -1;">
                    <p>Нет данных для отображения аналитики</p>
                    <p>Добавьте привычки и отмечайте дни борьбы</p>
                </div>
            `;
            return;
        }

        statsGrid.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${analytics.total_stats.total_habits || 0}</div>
                <div class="stat-label">Всего вредных привычек</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analytics.total_stats.daily_habits || 0}</div>
                <div class="stat-label">Ежедневные привычки</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analytics.total_stats.weekly_habits || 0}</div>
                <div class="stat-label">Еженедельные привычки</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${analytics.total_stats.monthly_habits || 0}</div>
                <div class="stat-label">Ежемесячные привычки</div>
            </div>
        `;

        if (analytics.habit_stats && analytics.habit_stats.length > 0) {
            analytics.habit_stats.forEach(stat => {
                const successRate = stat.completion_rate || 0;
                statsGrid.innerHTML += `
                    <div class="stat-card">
                        <div class="stat-value">${successRate}%</div>
                        <div class="stat-label">${this.escapeHtml(stat.habit_name)}</div>
                        <div class="stat-sub">${stat.completed_count || 0} из 30 дней без привычки</div>
                    </div>
                `;
            });
        }

        this.renderChart(analytics.habit_stats || []);
    }

    renderChart(habitStats) {
        const ctx = document.getElementById('progressChart');
        if (!ctx) return;

        if (this.chart) {
            this.chart.destroy();
        }

        // Если нет данных для графика
        if (!habitStats || habitStats.length === 0) {
            ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
            const noDataText = document.createElement('div');
            noDataText.style.textAlign = 'center';
            noDataText.style.padding = '40px';
            noDataText.style.color = '#6c757d';
            noDataText.textContent = 'Нет данных для построения графика';
            ctx.parentNode.appendChild(noDataText);
            return;
        }

        const labels = habitStats.map(stat => stat.habit_name);
        const data = habitStats.map(stat => stat.completion_rate || 0);

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Процент дней без вредной привычки (%)',
                    data: data,
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(155, 89, 182, 0.8)',
                        'rgba(46, 204, 113, 0.8)',
                        'rgba(241, 196, 15, 0.8)',
                        'rgba(230, 126, 34, 0.8)',
                        'rgba(231, 76, 60, 0.8)',
                        'rgba(149, 165, 166, 0.8)'
                    ],
                    borderColor: [
                        'rgb(52, 152, 219)',
                        'rgb(155, 89, 182)',
                        'rgb(46, 204, 113)',
                        'rgb(241, 196, 15)',
                        'rgb(230, 126, 34)',
                        'rgb(231, 76, 60)',
                        'rgb(149, 165, 166)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Дней без привычки (%)'
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.1)'
                        },
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + '% дней без привычки';
                            }
                        }
                    }
                }
            }
        });
    }

    async viewCompletions(habitId) {
        try {
            const response = await fetch(`${this.apiBase}/habits/${habitId}/completions/`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const completions = await response.json();
            this.showCompletions(completions);
        } catch (error) {
            console.error('Error loading completions:', error);
            this.showError('Ошибка загрузки статистики');
        }
    }

    showCompletions(completions) {
        if (completions.length === 0) {
            alert('Нет данных о борьбе с этой привычкой');
            return;
        }

        const completionsList = completions.map(comp => {
            const status = comp.completed ? '✅ Удалось избежать' : '❌ Не удалось избежать';
            const craving = comp.craving_level ? ` | Тяга: ${comp.craving_level}/10` : '';
            const resistance = comp.resistance_level ? ` | Сопротивление: ${comp.resistance_level}/10` : '';
            const notes = comp.notes ? `\n   Заметки: ${comp.notes}` : '';

            return `${comp.completion_date}: ${status}${craving}${resistance}${notes}`;
        }).join('\n\n');

        alert('История борьбы с привычкой:\n\n' + completionsList);
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Создаем уведомление вместо alert
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        `;
        
        notification.textContent = message;
        document.body.appendChild(notification);

        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);

        // Добавляем стили для анимации
        if (!document.getElementById('notification-styles')) {
            const style = document.createElement('style');
            style.id = 'notification-styles';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    window.tracker = new BadHabitTracker();
});

// Фолбэк на случай, если DOM уже загружен
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        window.tracker = new BadHabitTracker();
    });
} else {
    window.tracker = new BadHabitTracker();
}