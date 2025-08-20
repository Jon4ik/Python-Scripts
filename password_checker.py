import sys
import re
import hashlib
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QWidget, QScrollArea, 
                               QHBoxLayout, QToolButton)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap, QFont, QPainter, QImage

class PasswordCheckThread(QThread):
    finished = Signal(dict)

    def __init__(self, password):
        super().__init__()
        self.password = password

    def run(self):
        result = {}
        try:
            sha1_password = hashlib.sha1(self.password.encode('utf-8')).hexdigest().upper()
            prefix, suffix = sha1_password[:5], sha1_password[5:]
            
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                for line in response.text.splitlines():
                    if suffix in line:
                        count = int(line.split(":")[1])
                        result["pwned"] = True
                        result["count"] = count
                        break
                else:
                    result["pwned"] = False
            else:
                result["error"] = "Ошибка при запросе к API"
        except Exception as e:
            result["error"] = f"Ошибка: {str(e)}"
        
        self.finished.emit(result)

class PasswordCheckerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Проверка сложности пароля")
        self.setFixedSize(550, 500)
        
        self.scroll = QScrollArea()
        self.setCentralWidget(self.scroll)
        
        self.central_widget = QWidget()
        self.scroll.setWidget(self.central_widget)
        self.scroll.setWidgetResizable(True)
        
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        self.create_ui()
    
    def create_ui(self):
        self.label = QLabel("Введите пароль для проверки:")
        self.label.setAlignment(Qt.AlignCenter)
        
        # Контейнер для поля ввода и кнопки
        self.password_container = QWidget()
        self.password_layout = QHBoxLayout(self.password_container)
        self.password_layout.setContentsMargins(0, 0, 0, 0)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        
        # Кнопка показа/скрытия пароля
        self.toggle_password_btn = QToolButton()
        self.toggle_password_btn.setIcon(self.create_eye_icon())
        self.toggle_password_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_password_btn.setStyleSheet("""
            QToolButton {
                border: none;
                padding: 0px 5px;
                background: transparent;
            }
        """)
        self.toggle_password_btn.setCheckable(True)
        self.toggle_password_btn.toggled.connect(self.toggle_password_visibility)
        
        self.password_layout.addWidget(self.password_input)
        self.password_layout.addWidget(self.toggle_password_btn)
        
        self.check_button = QPushButton("Проверить пароль")
        self.check_button.clicked.connect(self.check_password)
        
        self.requirements_label = QLabel("Требования к паролю:")
        self.requirements_label.setStyleSheet("font-weight: bold;")
        
        self.requirements_list = QLabel("""
        - Не менее 12 символов<br>
        - Минимум 1 специальный символ (!@#$ и т.д.)<br>
        - Минимум 1 заглавная буква<br>
        - Минимум 1 строчная буква<br>
        - Минимум 1 цифра<br>
        - Не найден в утечках паролей
        """)
        self.requirements_list.setTextFormat(Qt.RichText)
        
        self.result_title = QLabel("Результат проверки:")
        self.result_title.setStyleSheet("font-weight: bold;")
        
        self.result_text = QLabel()
        self.result_text.setAlignment(Qt.AlignLeft)
        self.result_text.setWordWrap(True)
        self.result_text.setTextFormat(Qt.RichText)
        self.result_text.setStyleSheet("""
            padding: 10px;
            margin: 5px;
            border: 1px solid #ccc;
            border-radius: 5px;
        """)
        
        widgets = [
            self.label, self.password_container, self.check_button,
            self.requirements_label, self.requirements_list,
            self.result_title, self.result_text
        ]
        
        for widget in widgets:
            self.layout.addWidget(widget)
        
        self.layout.addStretch()
    
    def create_eye_icon(self):
        """Создает иконку глаза из символа"""
        image = QImage(24, 24, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        painter = QPainter(image)
        painter.setFont(QFont("Arial", 14))
        painter.drawText(image.rect(), Qt.AlignCenter, "👁")
        painter.end()
        
        return QIcon(QPixmap.fromImage(image))
    
    def toggle_password_visibility(self, checked):
        """Переключает видимость пароля"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
            self.toggle_password_btn.setIcon(self.create_eye_slash_icon())
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
            self.toggle_password_btn.setIcon(self.create_eye_icon())
    
    def create_eye_slash_icon(self):
        """Создает иконку перечеркнутого глаза"""
        image = QImage(24, 24, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        
        painter = QPainter(image)
        painter.setFont(QFont("Arial", 14))
        painter.drawText(image.rect(), Qt.AlignCenter, "🔒")
        painter.end()
        
        return QIcon(QPixmap.fromImage(image))
    
    def check_password(self):
        password = self.password_input.text()
        errors = []
        successes = []
        
        self.check_length(password, successes, errors)
        self.check_special_chars(password, successes, errors)
        self.check_uppercase(password, successes, errors)
        self.check_lowercase(password, successes, errors)
        self.check_digits(password, successes, errors)
        
        self.check_button.setEnabled(False)
        self.result_text.setText("Проверка пароля через базу утечек...")
        
        self.thread = PasswordCheckThread(password)
        self.thread.finished.connect(lambda res: self.on_api_check_done(res, successes, errors))
        self.thread.start()
    
    def on_api_check_done(self, api_result, successes, errors):
        self.check_button.setEnabled(True)
        
        if "error" in api_result:
            errors.append(f"× Ошибка проверки в базе утечек: {api_result['error']}")
        elif api_result.get("pwned", False):
            errors.append(f"× Пароль найден в {api_result['count']} утечках (небезопасен!)")
        else:
            successes.append("✓ Пароль не найден в известных утечках")
        
        self.display_results(successes, errors)
    
    def check_length(self, password, successes, errors):
        if len(password) >= 12:
            successes.append("✓ Длина пароля: 12+ символов")
        else:
            errors.append("× Длина пароля менее 12 символов")
    
    def check_special_chars(self, password, successes, errors):
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            successes.append("✓ Содержит специальные символы")
        else:
            errors.append("× Отсутствуют специальные символы")
    
    def check_uppercase(self, password, successes, errors):
        if re.search(r'[A-ZА-Я]', password):
            successes.append("✓ Содержит заглавные буквы")
        else:
            errors.append("× Отсутствуют заглавные буквы")
    
    def check_lowercase(self, password, successes, errors):
        if re.search(r'[a-zа-я]', password):
            successes.append("✓ Содержит строчные буквы")
        else:
            errors.append("× Отсутствуют строчные буквы")
    
    def check_digits(self, password, successes, errors):
        if re.search(r'\d', password):
            successes.append("✓ Содержит цифры")
        else:
            errors.append("× Отсутствуют цифры")
    
    def display_results(self, successes, errors):
        result_html = []
        
        if successes:
            result_html.append("<div style='color: green; margin-bottom: 10px;'>")
            result_html.append("<b>Соответствует требованиям:</b>")
            result_html.append("<ul style='margin-top: 5px; margin-bottom: 10px;'>")
            for success in successes:
                result_html.append(f"<li style='margin-bottom: 3px;'>{success}</li>")
            result_html.append("</ul>")
            result_html.append("</div>")
        
        if errors:
            result_html.append("<div style='color: red;'>")
            result_html.append("<b>Не соответствует требованиям:</b>")
            result_html.append("<ul style='margin-top: 5px;'>")
            for error in errors:
                result_html.append(f"<li style='margin-bottom: 3px;'>{error}</li>")
            result_html.append("</ul>")
            result_html.append("</div>")
        
        if not errors:
            result_html.insert(0, "<div style='color: green; font-weight: bold; font-size: 14pt; "
                                "text-align: center; margin: 15px 0;'>"
                                "Пароль соответствует всем требованиям!</div>")
        else:
            result_html.insert(0, "<div style='color: red; font-weight: bold; font-size: 14pt; "
                                "text-align: center; margin: 15px 0;'>"
                                "Пароль не соответствует требованиям!</div>")
        
        self.result_text.setText("".join(result_html))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PasswordCheckerApp()
    window.show()
    sys.exit(app.exec())
