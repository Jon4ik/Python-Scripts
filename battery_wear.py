import subprocess
import re
from PySide6.QtWidgets import (QApplication, QMainWindow, QLabel, 
                              QPushButton, QVBoxLayout, QWidget, 
                              QMessageBox)
from PySide6.QtCore import Qt
import sys

class BatteryChecker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Проверка износа батареи")
        self.setFixedSize(400, 200)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)
        
        self.label = QLabel("Нажмите кнопку, чтобы проверить износ батареи:")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        
        self.button = QPushButton("Проверить состояние батареи")
        self.button.clicked.connect(self.show_battery_wear)
        self.layout.addWidget(self.button)
        
        # Центрирование окна
        self.center()
    
    def center(self):
        frame = self.frameGeometry()
        screen = QApplication.primaryScreen().geometry()
        frame.moveCenter(screen.center())
        self.move(frame.topLeft())
    
    def get_battery_info(self):
        try:
            subprocess.run(
                ["powercfg", "/batteryreport", "/output", "battery_report.html"],
                capture_output=True,
                text=True,
                check=True,
            )

            with open("battery_report.html", "r", encoding="utf-8") as file:
                content = file.read()

            design_capacity_match = re.search(r"DESIGN CAPACITY.*?(\d[\d\s]*)", content)
            full_charge_capacity_match = re.search(r"FULL CHARGE CAPACITY.*?(\d[\d\s]*)", content)

            if design_capacity_match and full_charge_capacity_match:
                design_capacity_str = ''.join(c for c in design_capacity_match.group(1) if c.isdigit())
                full_charge_capacity_str = ''.join(c for c in full_charge_capacity_match.group(1) if c.isdigit())
                
                design_capacity = int(design_capacity_str)
                full_charge_capacity = int(full_charge_capacity_str)
                
                wear = ((design_capacity - full_charge_capacity) / design_capacity) * 100
                return design_capacity, full_charge_capacity, wear
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось найти информацию о емкости батареи в отчете.")
                return None, None, None
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить информацию о батарее: {str(e)}")
            return None, None, None
    
    def get_battery_status(self, wear):
        if wear <= 10:
            return "Отличное", "#4CAF50"  # Зеленый
        elif 10 < wear <= 20:
            return "Нормальное", "#8BC34A"  # Светло-зеленый
        elif 20 < wear <= 30:
            return "Умеренный износ", "#FFC107"  # Желтый
        elif 30 < wear <= 50:
            return "Сильный износ", "#FF9800"  # Оранжевый
        else:
            return "Критический износ", "#F44336"  # Красный
    
    def show_battery_wear(self):
        design_capacity, full_charge_capacity, wear = self.get_battery_info()

        if wear is not None:
            status, color = self.get_battery_status(wear)
            
            message = (
                f"<b>Информация о батарее:</b><br><br>"
                f"Расчетная емкость: {design_capacity:,} мВт·ч<br>"
                f"Текущая емкость: {full_charge_capacity:,} мВт·ч<br><br>"
                f"<b>Износ батареи:</b> <span style='color:{color};'>{wear:.2f}%</span><br>"
                f"<b>Состояние:</b> {status}"
            )
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Информация о батарее")
            msg_box.setTextFormat(Qt.TextFormat.RichText)
            msg_box.setText(message)
            msg_box.setIcon(QMessageBox.Icon.Information)
            
            # Центрирование окна сообщения
            msg_box.show()
            msg_box.move(self.geometry().center() - msg_box.rect().center())
            
            msg_box.exec()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось рассчитать износ батареи.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BatteryChecker()
    window.show()
    sys.exit(app.exec())