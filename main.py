import sys
import requests
from datetime import datetime, date
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
                               QLabel, QLineEdit, QTextEdit, QComboBox, QDateEdit,
                               QMessageBox, QTabWidget, QProgressBar, QSlider,
                               QGroupBox, QFormLayout, QScrollArea)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QFont
import time


class ApiWorker(QThread):
    habits_loaded = Signal(list)
    analytics_loaded = Signal(dict)
    completion_saved = Signal(bool, str)
    habit_deleted = Signal(bool, str)
    error_occurred = Signal(str)

    def __init__(self, api_base):
        super().__init__()
        self.api_base = api_base
        self.action = None
        self.data = None

    def load_habits(self):
        self.action = "load_habits"
        self.start()

    def load_analytics(self):
        self.action = "load_analytics"
        self.start()

    def save_completion(self, tracking_data):
        self.action = "save_completion"
        self.data = tracking_data
        self.start()

    def delete_habit(self, habit_id):
        self.action = "delete_habit"
        self.data = habit_id
        self.start()

    def run(self):
        try:
            if self.action == "load_habits":
                r = requests.get(f"{self.api_base}/habits/", timeout=5)
                if r.status_code == 200:
                    self.habits_loaded.emit(r.json())
                else:
                    self.error_occurred.emit("Ошибка загрузки привычек")

            elif self.action == "load_analytics":
                r = requests.get(f"{self.api_base}/analytics/", timeout=5)
                if r.status_code == 200:
                    self.analytics_loaded.emit(r.json())
                else:
                    self.error_occurred.emit("Ошибка загрузки аналитики")

            elif self.action == "save_completion":
                r = requests.post(f"{self.api_base}/habits/complete/", json=self.data, timeout=5)
                if r.status_code == 200:
                    self.completion_saved.emit(True, "Отметка сохранена")
                else:
                    self.completion_saved.emit(False, "Ошибка сохранения")

            elif self.action == "delete_habit":
                r = requests.delete(f"{self.api_base}/habits/{self.data}", timeout=5)
                if r.status_code == 200:
                    self.habit_deleted.emit(True, "Привычка удалена")
                else:
                    self.habit_deleted.emit(False, "Ошибка удаления")

        except requests.exceptions.ConnectionError:
            self.error_occurred.emit("Сервер не доступен")
        except requests.exceptions.Timeout:
            self.error_occurred.emit("Таймаут соединения")
        except Exception as e:
            self.error_occurred.emit(f"Ошибка: {str(e)}")


class HabitTrackerDesktop(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_base = 'http://localhost:8000'
        self.habits = []
        self.data_cache = {}
        self.last_update = 0
        self.cache_timeout = 30

        self.api_worker = ApiWorker(self.api_base)
        self.api_worker.habits_loaded.connect(self.on_habits_loaded)
        self.api_worker.analytics_loaded.connect(self.on_analytics_loaded)
        self.api_worker.completion_saved.connect(self.on_completion_saved)
        self.api_worker.habit_deleted.connect(self.on_habit_deleted)
        self.api_worker.error_occurred.connect(self.on_api_error)

        self.init_ui()
        self.load_habits()

    def init_ui(self):
        self.setWindowTitle("Трекер Вредных Привычек")
        self.setGeometry(100, 100, 1000, 700)

        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f8f9fa, stop:1 #e9ecef);
            }
            QWidget {
                background: white;
                border-radius: 10px;
                color: #495057;
            }
            QPushButton {
                background: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover { 
                background: #2980b9; 
            }
            QPushButton:pressed { 
                background: #21618c; 
            }
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background: white;
                color: #495057;
                alternate-background-color: #f8f9fa;
            }
            QListWidget::item { 
                padding: 8px; 
                border-bottom: 1px solid #e9ecef; 
            }
            QListWidget::item:selected { 
                background: #3498db; 
                color: white; 
            }
            QLineEdit, QTextEdit, QComboBox {
                padding: 6px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background: white;
                color: #495057;
                min-height: 20px;
            }
            QLabel { 
                color: #2c3e50; 
                font-weight: bold; 
            }
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                text-align: center;
                background: #f8f9fa;
                color: #495057;
                min-height: 15px;
            }
            QProgressBar::chunk { 
                background: #27ae60; 
                border-radius: 3px; 
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                color: #495057;
                padding: 8px 16px;
                margin-right: 2px;
                min-width: 80px;
                border-radius: 4px;
            }
            QTabBar::tab:selected { 
                background-color: white; 
                color: #3498db;
                border-bottom: 2px solid #3498db;
            }
            QGroupBox {
                color: #2c3e50;
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 10px;
                background: #f8f9fa;
            }
            QSlider::groove:horizontal {
                border: 1px solid #dee2e6;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #2980b9;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QTextEdit {
                background: white;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("АНТИ-ПРИВЫЧКИ")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #2c3e50; padding: 12px; background: #e3f2fd; border-radius: 8px;")
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.create_habits_tab()
        self.create_add_tab()
        self.create_tracking_tab()
        self.create_analytics_tab()

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Готов к работе")


        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(60000)

    def auto_refresh(self):
        current_time = time.time()
        if current_time - self.last_update > self.cache_timeout:
            self.load_habits()

    def load_habits(self):
        if self.api_worker.isRunning():
            return

        self.status_bar.showMessage("Загрузка...")
        self.api_worker.load_habits()

    def on_habits_loaded(self, habits):
        self.habits = habits
        self.data_cache['habits'] = habits
        self.last_update = time.time()
        self.update_habits_list()
        self.update_tracking_combo()
        self.status_bar.showMessage(f"Загружено {len(self.habits)} привычек")

    def on_analytics_loaded(self, analytics):
        self.display_analytics(analytics)
        self.status_bar.showMessage("Аналитика загружена")

    def on_completion_saved(self, success, message):
        if success:
            self.last_update = 0
            self.load_habits()
        else:
            QMessageBox.critical(self, "Ошибка", message)

    def on_habit_deleted(self, success, message):
        if success:
            self.last_update = 0
            self.load_habits()
        else:
            QMessageBox.critical(self, "Ошибка", message)

    def on_api_error(self, error_message):
        self.status_bar.showMessage(error_message)
        # Показываем ошибку только если она критическая
        if "Сервер не доступен" in error_message or "Таймаут" in error_message:
            QMessageBox.warning(self, "Ошибка", error_message)

    def update_habits_list(self):
        self.habits_list.clear()
        for habit in self.habits:
            item = QListWidgetItem(habit['name'])
            item.setData(Qt.UserRole, habit)
            self.habits_list.addItem(item)

    def update_tracking_combo(self):
        self.track_habit_combo.clear()
        for habit in self.habits:
            self.track_habit_combo.addItem(habit['name'], habit['id'])

    def on_habit_selected(self, item):
        habit = item.data(Qt.UserRole)
        info_text = f"""
        <b>{habit['name']}</b><br><br>
        {habit['description'] or 'Без описания'}<br><br>
        Мотивация: {habit['motivation_text'] or 'Не указана'}<br>
        Сложность: {self.get_difficulty_text(habit['difficulty_level'])}<br>
        Частота: {self.get_frequency_text(habit['frequency'])}<br>
        ID: {habit['id']}
        """
        self.habit_info.setHtml(info_text)

    def get_difficulty_text(self, level):
        levels = {'easy': 'Легко', 'medium': 'Средне', 'hard': 'Сложно'}
        return levels.get(level, level)

    def get_frequency_text(self, frequency):
        frequencies = {'daily': 'Ежедневно', 'weekly': 'Еженедельно', 'monthly': 'Ежемесячно'}
        return frequencies.get(frequency, frequency)

    def add_habit(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название привычки")
            return

        difficulty_map = {"Легко": "easy", "Средне": "medium", "Сложно": "hard"}

        habit_data = {
            "name": name,
            "description": self.desc_input.toPlainText().strip(),
            "habit_type": "bad",
            "frequency": "daily",
            "target_count": 1,
            "motivation_text": self.motivation_input.toPlainText().strip(),
            "difficulty_level": difficulty_map[self.difficulty_combo.currentText()]
        }

        self.status_bar.showMessage("Добавление привычки...")

        worker = ApiWorker(self.api_base)
        worker.completion_saved.connect(self.on_habit_added)
        worker.error_occurred.connect(self.on_api_error)
        worker.action = "save_completion"
        worker.data = habit_data
        worker.start()

    def on_habit_added(self, success, message):
        if success:
            self.name_input.clear()
            self.desc_input.clear()
            self.motivation_input.clear()
            self.last_update = 0
            self.load_habits()
            self.tabs.setCurrentIndex(0)
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось добавить привычку")

    def delete_habit(self):
        current_item = self.habits_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите привычку для удаления")
            return
        habit = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить привычку '{habit['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.api_worker.delete_habit(habit['id'])

    def show_tracking_dialog(self):
        current_item = self.habits_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Ошибка", "Выберите привычку")
            return
        self.tabs.setCurrentIndex(2)

    def save_tracking(self):
        if self.track_habit_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Ошибка", "Выберите привычку")
            return
        habit_id = self.track_habit_combo.currentData()
        completed = self.completed_check.currentIndex() == 0
        tracking_data = {
            "habit_id": habit_id,
            "completion_date": self.track_date.date().toString("yyyy-MM-dd"),
            "completed": completed,
            "notes": self.notes_input.toPlainText().strip(),
            "craving_level": self.craving_slider.value(),
            "resistance_level": self.resistance_slider.value()
        }
        self.api_worker.save_completion(tracking_data)

    def load_analytics(self):
        if self.api_worker.isRunning():
            return

        self.status_bar.showMessage("Загрузка аналитики...")
        self.api_worker.load_analytics()

    def display_analytics(self, analytics):
        total_habits = analytics['total_stats']['total_habits']
        stats_text = f"<b>Общая статистика</b><br>Всего привычек: {total_habits}"
        self.stats_label.setText(stats_text)

        for i in reversed(range(self.progress_layout.count())):
            widget = self.progress_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        for stat in analytics['habit_stats']:
            group = QGroupBox(stat['habit_name'])
            layout = QVBoxLayout()
            progress = QProgressBar()
            progress.setValue(int(stat['completion_rate']))
            progress.setFormat(f"{stat['completion_rate']}% ({stat['completed_count']}/30 дней)")
            layout.addWidget(progress)
            group.setLayout(layout)
            self.progress_layout.addWidget(group)

    def create_habits_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Мои вредные привычки"))
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_habits)
        header_layout.addWidget(refresh_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.habits_list = QListWidget()
        self.habits_list.itemClicked.connect(self.on_habit_selected)
        layout.addWidget(self.habits_list)

        self.habit_info = QTextEdit()
        self.habit_info.setReadOnly(True)
        self.habit_info.setMaximumHeight(120)
        layout.addWidget(self.habit_info)

        actions_layout = QHBoxLayout()
        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_habit)
        track_btn = QPushButton("Отметить")
        track_btn.clicked.connect(self.show_tracking_dialog)
        actions_layout.addWidget(delete_btn)
        actions_layout.addWidget(track_btn)
        layout.addLayout(actions_layout)

        self.tabs.addTab(tab, "Привычки")

    def create_add_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Добавить новую вредную привычку"))

        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Например: Курение")
        form_layout.addRow("Название:", self.name_input)

        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setPlaceholderText("Описание привычки...")
        form_layout.addRow("Описание:", self.desc_input)

        self.motivation_input = QTextEdit()
        self.motivation_input.setMaximumHeight(50)
        self.motivation_input.setPlaceholderText("Мотивация...")
        form_layout.addRow("Мотивация:", self.motivation_input)

        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Легко", "Средне", "Сложно"])
        form_layout.addRow("Сложность:", self.difficulty_combo)

        layout.addLayout(form_layout)

        add_btn = QPushButton("Добавить привычку")
        add_btn.clicked.connect(self.add_habit)
        layout.addWidget(add_btn)

        layout.addStretch()
        self.tabs.addTab(tab, "Добавить")

    def create_tracking_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Отслеживание борьбы с привычками"))

        track_layout = QFormLayout()
        track_layout.setSpacing(8)

        self.track_habit_combo = QComboBox()
        track_layout.addRow("Привычка:", self.track_habit_combo)

        self.track_date = QDateEdit()
        self.track_date.setDate(date.today())
        self.track_date.setCalendarPopup(True)
        track_layout.addRow("Дата:", self.track_date)

        self.completed_check = QComboBox()
        self.completed_check.addItems(["Удалось избежать", "Не удалось избежать"])
        track_layout.addRow("Результат:", self.completed_check)

        self.craving_slider = QSlider(Qt.Horizontal)
        self.craving_slider.setRange(0, 10)
        self.craving_slider.setValue(0)
        self.craving_label = QLabel("Уровень тяги: 0")
        self.craving_slider.valueChanged.connect(
            lambda v: self.craving_label.setText(f"Уровень тяги: {v}")
        )
        track_layout.addRow(self.craving_label, self.craving_slider)

        self.resistance_slider = QSlider(Qt.Horizontal)
        self.resistance_slider.setRange(0, 10)
        self.resistance_slider.setValue(0)
        self.resistance_label = QLabel("Уровень сопротивления: 0")
        self.resistance_slider.valueChanged.connect(
            lambda v: self.resistance_label.setText(f"Уровень сопротивления: {v}")
        )
        track_layout.addRow(self.resistance_label, self.resistance_slider)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(80)
        self.notes_input.setPlaceholderText("Заметки...")
        track_layout.addRow("Заметки:", self.notes_input)

        layout.addLayout(track_layout)

        save_btn = QPushButton("Сохранить отметку")
        save_btn.clicked.connect(self.save_tracking)
        layout.addWidget(save_btn)

        layout.addStretch()
        self.tabs.addTab(tab, "Отслеживание")

    def create_analytics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Аналитика"))
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet(
            "font-size: 14px; padding: 10px; color: #2c3e50; background: #e3f2fd; border-radius: 6px;")
        layout.addWidget(self.stats_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(400)

        scroll_content = QWidget()
        self.progress_layout = QVBoxLayout(scroll_content)
        self.progress_layout.setSpacing(10)
        self.progress_layout.setContentsMargins(10, 10, 10, 10)

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        refresh_btn = QPushButton("Обновить аналитику")
        refresh_btn.clicked.connect(self.load_analytics)
        layout.addWidget(refresh_btn)

        layout.addStretch()
        self.tabs.addTab(tab, "Аналитика")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = HabitTrackerDesktop()
    window.show()
    sys.exit(app.exec())