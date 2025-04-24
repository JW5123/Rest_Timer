import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QHBoxLayout,
    QVBoxLayout, QMessageBox, QDialog, QTimeEdit
)
from PyQt5.QtCore import Qt, QTimer, QTime
from screeninfo import get_monitors

class TimeEditWidget(QTimeEdit):
    def __init__(self):
        super().__init__()
        self.setDisplayFormat("HH : mm : ss")
        self.setTime(QTime(0, 0, 0))
        self.setButtonSymbols(QTimeEdit.UpDownArrows)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedWidth(180)
        self.setStyleSheet("font-size: 20px;")

    def get_total_seconds(self):
        t = self.time()
        return t.hour() * 3600 + t.minute() * 60 + t.second()

    def set_time(self, h=0, m=0, s=0):
        self.setTime(QTime(h, m, s))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            return
        super().keyPressEvent(event)

class RestScreen(QDialog):
    def __init__(self, duration, on_done):
        super().__init__()
        self.duration = duration
        self.remaining = duration
        self.on_done = on_done
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 40px; color: white;")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.showFullScreen()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

    def update_timer(self):
        if self.remaining <= 0:
            self.timer.stop()
            self.close()
            self.on_done()
            return

        hrs, rem = divmod(self.remaining, 3600)
        mins, secs = divmod(rem, 60)
        self.label.setText(f"休息剩餘時間: {hrs:02d}:{mins:02d}:{secs:02d}")
        self.remaining -= 1

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.timer.stop()
            self.close()
            self.on_done()

class TimerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.work_timer = QTimer(self)
        self.work_timer.timeout.connect(self.update_work_timer)
        self.elapsed = 0
        self.total_work = 0
        self.is_paused = False

    def init_ui(self):
        self.setWindowTitle('工作-休息計時器')
        self.setFixedSize(400, 300)

        self.work_time_edit = TimeEditWidget()
        self.rest_time_edit = TimeEditWidget()

        work_layout = QHBoxLayout()
        work_layout.setAlignment(Qt.AlignCenter)
        work_label = QLabel("工作時間：")
        work_label.setStyleSheet("font-size: 18px;")
        work_layout.addWidget(work_label)
        work_layout.addWidget(self.work_time_edit)

        rest_layout = QHBoxLayout()
        rest_layout.setAlignment(Qt.AlignCenter)
        rest_label = QLabel("休息時間：")
        rest_label.setStyleSheet("font-size: 18px;")
        rest_layout.addWidget(rest_label)
        rest_layout.addWidget(self.rest_time_edit)

        self.status_label = QLabel("尚未開始")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 20px;")

        self.start_btn = QPushButton("開始計時")
        self.pause_btn = QPushButton("暫停")
        self.stop_btn = QPushButton("停止")

        for btn in (self.start_btn, self.pause_btn, self.stop_btn):
            btn.setStyleSheet("font-size: 18px; padding: 10px 20px;")

        self.start_btn.clicked.connect(self.start_timer)
        self.pause_btn.clicked.connect(self.pause_timer)
        self.stop_btn.clicked.connect(self.stop_timer)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setSpacing(20)
        button_layout.addWidget(self.pause_btn)
        button_layout.addWidget(self.stop_btn)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addLayout(work_layout)
        layout.addSpacing(10)
        layout.addLayout(rest_layout)
        layout.addSpacing(20)
        layout.addWidget(self.status_label)
        layout.addSpacing(20)
        layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def start_timer(self):
        self.elapsed = 0
        self.is_paused = False
        try:
            self.total_work = self.work_time_edit.get_total_seconds()
            self.rest_time = self.rest_time_edit.get_total_seconds()
            if self.total_work <= 0 or self.rest_time <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.critical(self, "輸入錯誤", "請輸入有效的整數時間（不得為零）")
            return

        self.status_label.setText("已工作時間: 00:00:00")
        self.work_timer.start(1000)

    def update_work_timer(self):
        if self.is_paused:
            return

        self.elapsed += 1
        hrs, rem = divmod(self.elapsed, 3600)
        mins, secs = divmod(rem, 60)
        self.status_label.setText(f"已工作時間: {hrs:02d}:{mins:02d}:{secs:02d}")

        if self.elapsed >= self.total_work:
            self.work_timer.stop()
            self.status_label.setText(f"已工作時間: {hrs:02d}:{mins:02d}:{secs:02d}")
            self.show_rest_screen()

    def pause_timer(self):
        self.is_paused = not self.is_paused
        self.pause_btn.setText("繼續" if self.is_paused else "暫停")

    def stop_timer(self):
        self.work_timer.stop()
        self.elapsed = 0
        self.status_label.setText("已工作時間: 00:00:00")
        self.is_paused = False
        self.pause_btn.setText("暫停")

    def show_rest_screen(self):
        self.rest_dialogs = []
        monitors = get_monitors()

        def on_rest_done():
            for dlg in self.rest_dialogs:
                dlg.close()
            self.status_label.setText("已工作時間: 00:00:00")

        for monitor in monitors:
            dlg = RestScreen(self.rest_time, on_rest_done)
            dlg.move(monitor.x, monitor.y)
            dlg.showFullScreen()
            self.rest_dialogs.append(dlg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimerApp()
    window.show()
    sys.exit(app.exec_())