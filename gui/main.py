import sys
import os
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disk-cache-dir=C:/Temp/QtCache"

from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtCore import QThread
from tabs.flight_data_tab import FlightDataTab
from tabs.flight_modes_tab import FlightModesTab
from tabs.orientation_3d_tab import Orientation3DTab
from tabs.radio_calibration_tab import RadioCalibrationTab
from tabs.gps_map_tab import GPSMapTab
from tabs.telemetry_tab import TelemetryTab
from serial_reader import SerialReader

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Ground Control Station")
        self.setGeometry(100, 100, 1200, 800)

        # QTabWidget for all tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Custom tab style
        self.tabs.setStyleSheet("""
            QTabBar::tab {
                background: #2c2c2c;
                color: #dddddd;
                padding: 14px 30px;
                font-size: 16px;
                border: 1px solid #444;
                border-bottom: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                min-width: 140px;
            }
            QTabBar::tab:selected {
                background: #4caf50;
                color: white;
                font-weight: bold;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                top: -1px;
                background-color: #1e1e1e;
            }
        """)

        # ───────────── Serial Reader Setup ─────────────
        self.serial_thread = QThread()
        self.serial_reader = SerialReader()
        self.serial_reader.moveToThread(self.serial_thread)
        self.serial_thread.started.connect(self.serial_reader.start_reading)
        self.serial_thread.start()

        # ───────────── Create Tabs ─────────────
        self.flight_data_tab = FlightDataTab(serial_reader=self.serial_reader)
        self.flight_modes_tab = FlightModesTab(serial_reader=self.serial_reader)
        self.radio_tab = RadioCalibrationTab(serial_reader=self.serial_reader)
        self.gps_map_tab = GPSMapTab()

        # 3D Model Assets
        base_dir = os.path.dirname(os.path.abspath(__file__))
        obj_path = os.path.join(base_dir, "assets", "F450 Quadcopter Frame with Pixhawk 2.4.8 Flight Controller.obj")
        mtl_path = os.path.join(base_dir, "assets", "F450 Quadcopter Frame with Pixhawk 2.4.8 Flight Controller.mtl")

        if os.path.exists(obj_path):
            print(f"✅ OBJ file found: {obj_path}")
        else:
            print(f"❌ OBJ file NOT found: {obj_path}")

        if os.path.exists(mtl_path):
            print(f"✅ MTL file found: {mtl_path}")
        else:
            print(f"❌ MTL file NOT found: {mtl_path}")

        self.orientation_3d_tab = Orientation3DTab(obj_path, mtl_path, serial_reader=self.serial_reader)
        self.telemetry_tab = TelemetryTab(serial_reader=self.serial_reader)

        # ───────────── Add Tabs to QTabWidget ─────────────
        self.tabs.addTab(self.flight_data_tab, "Flight Data")
        self.tabs.addTab(self.flight_modes_tab, "Flight Modes")
        self.tabs.addTab(self.radio_tab, "Radio Calibration")
        self.tabs.addTab(self.gps_map_tab, "GPS Map")
        self.tabs.addTab(self.orientation_3d_tab, "3D Orientation")
        self.tabs.addTab(self.telemetry_tab, "Telemetry")

        # Debugging: print relevant incoming lines
        self.serial_reader.data_received.connect(self.debug_serial_data)

    def debug_serial_data(self, line):
        """Quick filter for debugging data flow to GUI."""
        if any(keyword in line for keyword in ["ROLL:", "PITCH:", "YAW:", "CH1:"]):
            print(f"🎯 [MainWindow] Serial Data: {line}")

    def closeEvent(self, event):
        print("[MainWindow] Stopping SerialReader...")
        if hasattr(self.serial_reader, 'stop'):
            self.serial_reader.stop()
        if hasattr(self.serial_thread, 'quit'):
            self.serial_thread.quit()
            self.serial_thread.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            font-size: 14px;
            background-color: #121212;
            color: #e0e0e0;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #555;
            border-radius: 5px;
            margin-top: 20px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 3px;
            background-color: #121212;
        }
        QProgressBar {
            border: 1px solid #333;
            border-radius: 5px;
            background: #1e1e1e;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #00c853;
        }
        QPushButton {
            background-color: #263238;
            color: #ffffff;
            border: 1px solid #37474f;
            padding: 5px 10px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #37474f;
        }
        QComboBox {
            background-color: #263238;
            color: #ffffff;
            border: 1px solid #37474f;
        }
        QLabel {
            font-size: 14px;
        }
        QLCDNumber {
            color: #00e676;
            background-color: #1e1e1e;
            border: 1px solid #333;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
