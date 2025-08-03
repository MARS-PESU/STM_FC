from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QTextEdit, QGridLayout
)
from PyQt5.QtCore import Qt, QTimer
from datetime import datetime

class TelemetryTab(QWidget):
    def __init__(self, serial_reader=None):
        super().__init__()
        self.reader = serial_reader

        # Main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # ───────────── Telemetry Overview ─────────────
        overview_group = QGroupBox("Telemetry Overview")
        overview_layout = QGridLayout()
        overview_group.setLayout(overview_layout)

        # Labels for telemetry data
        self.roll_label = self._create_label("Roll: --°", "#EF5350")     # Red
        self.pitch_label = self._create_label("Pitch: --°", "#5C6BC0")   # Blue
        self.yaw_label = self._create_label("Yaw: --°", "#FFCA28")       # Yellow
        self.mode_label = self._create_label("Mode: Unknown", "#00E676") # Green

        self.alt_label = self._create_label("Altitude: -- m", "#66BB6A") # Green
        self.temp_label = self._create_label("Temp: -- °C", "#FF7043")   # Orange
        self.press_label = self._create_label("Pressure: -- hPa", "#26C6DA") # Cyan

        # Place labels in a 2x3 grid
        overview_layout.addWidget(self.roll_label, 0, 0)
        overview_layout.addWidget(self.pitch_label, 0, 1)
        overview_layout.addWidget(self.yaw_label, 0, 2)
        overview_layout.addWidget(self.alt_label, 1, 0)
        overview_layout.addWidget(self.temp_label, 1, 1)
        overview_layout.addWidget(self.press_label, 1, 2)
        overview_layout.addWidget(self.mode_label, 2, 0, 1, 3)

        main_layout.addWidget(overview_group)

        # ───────────── Connection Status ─────────────
        status_group = QGroupBox("Telemetry Status")
        status_layout = QHBoxLayout()
        status_group.setLayout(status_layout)

        self.status_label = QLabel("Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F44336;")
        status_layout.addWidget(self.status_label)

        main_layout.addWidget(status_group)

        # ───────────── Live Log Console ─────────────
        log_group = QGroupBox("Live Telemetry Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet(
            "background-color: #121212; color: #E0E0E0; font-family: Consolas; font-size: 12px;"
        )
        log_layout.addWidget(self.log_console)

        main_layout.addWidget(log_group)

        # ───────────── Connect to Serial Reader ─────────────
        self.last_update_time = None
        if self.reader:
            self.reader.data_received.connect(self.handle_serial_data)

        # Check connection health every 1 second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_connection_status)
        self.timer.start(1000)

    # ───────────── Helper to Create Styled Labels ─────────────
    def _create_label(self, text, color):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        return label

    # ───────────── Handle Serial Data ─────────────
    def handle_serial_data(self, line):
        line = line.strip()
        if not line:
            return

        # Log the line to the console with timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_console.append(f"[{timestamp}] {line}")

        # Update status timestamp
        self.last_update_time = datetime.now()

        # Parse telemetry data
        try:
            parts = [p.strip() for p in line.split("|")]
            for part in parts:
                if part.upper().startswith("ROLL"):
                    self.roll_label.setText(f"Roll: {part.split(':')[1].strip()}°")
                elif part.upper().startswith("PITCH"):
                    self.pitch_label.setText(f"Pitch: {part.split(':')[1].strip()}°")
                elif part.upper().startswith("YAW"):
                    self.yaw_label.setText(f"Yaw: {part.split(':')[1].strip()}°")
                elif part.upper().startswith("ALT"):
                    self.alt_label.setText(f"Altitude: {part.split(':')[1].strip()}")
                elif part.upper().startswith("TEMP"):
                    self.temp_label.setText(f"Temp: {part.split(':')[1].strip()}")
                elif part.upper().startswith("PRESS"):
                    self.press_label.setText(f"Pressure: {part.split(':')[1].strip()}")
                elif part.upper().startswith("MODE"):
                    self.mode_label.setText(f"Mode: {part.split(':')[1].strip()}")
        except Exception as e:
            print(f"[TelemetryTab] Parse error: {line} — {e}")

    # ───────────── Connection Status ─────────────
    def update_connection_status(self):
        if self.last_update_time:
            delta = (datetime.now() - self.last_update_time).total_seconds()
            if delta < 2:  # received data in last 2 seconds
                self.status_label.setText("Connected")
                self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00E676;")
            else:
                self.status_label.setText("No Data")
                self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFCA28;")
        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #F44336;")
