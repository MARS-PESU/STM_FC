import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QGroupBox, QFrame
)
from .attitude_widget import AttitudeIndicator
from .compass_widget import CompassWidget
import math


class FlightDataTab(QWidget):
    def __init__(self, serial_reader=None):
        super().__init__()
        self.reader = serial_reader

        # Store sensor values
        self.current_acc = [0, 0, 0]
        self.current_gyro = [0, 0, 0]
        self.current_temp = 25.0
        self.current_pressure = 1013.25
        
        # 🎯 Store ACTUAL RC channel values (from receiver)
        self.rc_channels = [1500, 1500, 1500, 1500, 1500, 1500]  # Real RC values
        self.rc_connected = False

        # Sensor calibration ranges (keep for other calculations)
        self.sensor_ranges = {
            'acc_x': {'min': -2000, 'max': 2000},
            'acc_y': {'min': -2000, 'max': 2000},
            'acc_z': {'min': -2000, 'max': 2000},
            'gyro_x': {'min': -1000, 'max': 1000},
            'gyro_y': {'min': -1000, 'max': 1000},
            'gyro_z': {'min': -1000, 'max': 1000},
            'temp': {'min': -10, 'max': 60},
            'pressure': {'min': 950, 'max': 1050}
        }

        self.setStyleSheet("""
            QLabel {
                font-size: 16px;
                padding: 4px 8px;
                color: #EAEAEA;
            }
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                border: 2px solid #007ACC;
                border-radius: 10px;
                margin-top: 10px;
                background-color: #1e1e1e;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 8px;
                background-color: #121212;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 1px;
                color: #ffffff;
            }
        """)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        grid = QGridLayout()
        grid.setSpacing(20)

        # Sensor Panel
        sensor_panel = QVBoxLayout()
        sensor_panel.addWidget(self.create_gps_group())
        sensor_panel.addWidget(self.create_baro_group())
        sensor_panel.addWidget(self.create_imu_group())
        sensor_panel.addWidget(self.create_rc_group())  # 🎯 Changed from PPM to RC
        sensor_frame = QFrame()
        sensor_frame.setLayout(sensor_panel)

        # Visual Panel
        visual_panel = QVBoxLayout()
        visual_panel.addWidget(self.create_attitude_group())
        visual_panel.addWidget(self.create_compass_group())
        visual_frame = QFrame()
        visual_frame.setLayout(visual_panel)

        grid.addWidget(sensor_frame, 0, 0)
        grid.addWidget(visual_frame, 0, 1)
        main_layout.addLayout(grid)

        # Connect serial signal
        if self.reader:
            self.reader.data_received.connect(self.handle_serial_data)

    def create_gps_group(self):
        group = QGroupBox("GPS")
        layout = QVBoxLayout()
        
        self.gps_status = QLabel("Status: Searching...")
        self.gps_status.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #FFA726;
            background-color: rgba(255, 167, 38, 0.1);
            border-radius: 5px; padding: 6px;
        """)
        
        self.latitude = QLabel("Latitude: 12.9351° N")
        self.latitude.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #42A5F5;
            background-color: rgba(66, 165, 245, 0.1);
            border-radius: 5px; padding: 6px;
        """)
        
        self.longitude = QLabel("Longitude: 77.5360° E")
        self.longitude.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #AB47BC;
            background-color: rgba(171, 71, 188, 0.1);
            border-radius: 5px; padding: 6px;
        """)
        
        layout.addWidget(self.gps_status)
        layout.addWidget(self.latitude)
        layout.addWidget(self.longitude)
        group.setLayout(layout)
        return group

    def create_baro_group(self):
        group = QGroupBox("Barometer")
        layout = QVBoxLayout()
        
        self.altitude = QLabel("Relative Altitude: -- m")
        self.altitude.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #66BB6A;
            background-color: rgba(102, 187, 106, 0.1);
            border-radius: 5px; padding: 6px;
        """)
        
        self.temp = QLabel("TEMP: -- °C")
        self.temp.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #FF7043;
            background-color: rgba(255, 112, 67, 0.1);
            border-radius: 5px; padding: 6px;
        """)
        
        self.press = QLabel("PRESS: -- hPa")
        self.press.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #26C6DA;
            background-color: rgba(38, 198, 218, 0.1);
            border-radius: 5px; padding: 6px;
        """)
        
        layout.addWidget(self.altitude)
        layout.addWidget(self.temp)
        layout.addWidget(self.press)
        group.setLayout(layout)
        return group

    def create_imu_group(self):
        group = QGroupBox("IMU / Sensor Data")
        layout = QVBoxLayout()

        self.roll = QLabel("Roll: --°")
        self.roll.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #EF5350;
            background-color: rgba(239, 83, 80, 0.1);
            border-left: 4px solid #EF5350; border-radius: 5px; padding: 6px;
        """)
        
        self.pitch = QLabel("Pitch: --°")
        self.pitch.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #5C6BC0;
            background-color: rgba(92, 107, 192, 0.1);
            border-left: 4px solid #5C6BC0; border-radius: 5px; padding: 6px;
        """)
        
        self.yaw = QLabel("Yaw: --°")
        self.yaw.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #FFCA28;
            background-color: rgba(255, 202, 40, 0.1);
            border-left: 4px solid #FFCA28; border-radius: 5px; padding: 6px;
        """)

        self.accel = QLabel("ACC: ---, ---, ---")
        self.accel.setStyleSheet("""
            font-size: 13px; font-weight: bold; color: #8BC34A;
            background-color: rgba(139, 195, 74, 0.1);
            border: 1px solid #8BC34A; border-radius: 5px; padding: 5px;
        """)
        
        self.gyro = QLabel("GYRO: ---, ---, ---")
        self.gyro.setStyleSheet("""
            font-size: 13px; font-weight: bold; color: #FF9800;
            background-color: rgba(255, 152, 0, 0.1);
            border: 1px solid #FF9800; border-radius: 5px; padding: 5px;
        """)
        
        self.mag = QLabel("MAG: ---, ---, ---")
        self.mag.setStyleSheet("""
            font-size: 13px; font-weight: bold; color: #E91E63;
            background-color: rgba(233, 30, 99, 0.1);
            border: 1px solid #E91E63; border-radius: 5px; padding: 5px;
        """)

        layout.addWidget(self.roll)
        layout.addWidget(self.pitch)
        layout.addWidget(self.yaw)
        layout.addWidget(self.accel)
        layout.addWidget(self.gyro)
        layout.addWidget(self.mag)

        group.setLayout(layout)
        return group

    def create_rc_group(self):
        """🎯 NEW: Display ACTUAL RC receiver channel values"""
        group = QGroupBox("RC Receiver Channels (μs)")
        layout = QVBoxLayout()
        
        # RC connection status
        self.rc_status = QLabel("RC Status: DISCONNECTED")
        self.rc_status.setStyleSheet("""
            font-size: 14px; font-weight: bold; color: #ff5722;
            background-color: rgba(255, 87, 34, 0.2);
            border: 2px solid #ff5722; border-radius: 5px; padding: 8px;
            text-align: center;
        """)
        
        # Create 6 RC channel labels
        self.rc_ch1 = QLabel("CH1 (Aileron): 1500 μs")
        self.rc_ch2 = QLabel("CH2 (Elevator): 1500 μs")
        self.rc_ch3 = QLabel("CH3 (Throttle): 1500 μs")
        self.rc_ch4 = QLabel("CH4 (Rudder): 1500 μs")
        self.rc_ch5 = QLabel("CH5 (Aux1): 1500 μs")
        self.rc_ch6 = QLabel("CH6 (Aux2): 1500 μs")
        
        # Enhanced styling with gradients and borders
        rc_styles = [
            """font-size: 14px; font-weight: bold; color: #ff5722; 
               background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255,87,34,0.2), stop:1 rgba(255,87,34,0.05));
               border-left: 3px solid #ff5722; border-radius: 5px; padding: 6px;""",
            """font-size: 14px; font-weight: bold; color: #2196f3;
               background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(33,150,243,0.2), stop:1 rgba(33,150,243,0.05));
               border-left: 3px solid #2196f3; border-radius: 5px; padding: 6px;""",
            """font-size: 14px; font-weight: bold; color: #4caf50;
               background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(76,175,80,0.2), stop:1 rgba(76,175,80,0.05));
               border-left: 3px solid #4caf50; border-radius: 5px; padding: 6px;""",
            """font-size: 14px; font-weight: bold; color: #ff9800;
               background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(255,152,0,0.2), stop:1 rgba(255,152,0,0.05));
               border-left: 3px solid #ff9800; border-radius: 5px; padding: 6px;""",
            """font-size: 14px; font-weight: bold; color: #9c27b0;
               background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(156,39,176,0.2), stop:1 rgba(156,39,176,0.05));
               border-left: 3px solid #9c27b0; border-radius: 5px; padding: 6px;""",
            """font-size: 14px; font-weight: bold; color: #00bcd4;
               background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0,188,212,0.2), stop:1 rgba(0,188,212,0.05));
               border-left: 3px solid #00bcd4; border-radius: 5px; padding: 6px;"""
        ]
        
        layout.addWidget(self.rc_status)
        
        rc_labels = [self.rc_ch1, self.rc_ch2, self.rc_ch3, self.rc_ch4, self.rc_ch5, self.rc_ch6]
        for i, label in enumerate(rc_labels):
            label.setStyleSheet(rc_styles[i])
            layout.addWidget(label)
        
        group.setLayout(layout)
        return group

    def create_attitude_group(self):
        group = QGroupBox("Artificial Horizon")
        layout = QVBoxLayout()
        self.attitude_widget = AttitudeIndicator()
        layout.addWidget(self.attitude_widget)
        group.setLayout(layout)
        return group

    def create_compass_group(self):
        group = QGroupBox("Compass")
        layout = QVBoxLayout()
        self.compass_widget = CompassWidget()
        layout.addWidget(self.compass_widget)
        group.setLayout(layout)
        return group

    def get_channel_status_color(self, ppm_value):
        """Get color for channel based on value range"""
        if ppm_value < 1200 or ppm_value > 1800:
            return "#ff5722"  # Red for extreme values
        elif ppm_value < 1400 or ppm_value > 1600:
            return "#ff9800"  # Orange for high values
        else:
            return "#4caf50"  # Green for normal range

    def handle_serial_data(self, raw_line: str):
        """Parse and handle incoming serial data from STM32."""
        try:
            # Normalize line for parsing
            line_normalized = (
                raw_line.replace('°', '')
                        .replace('hPa', '')
                        .replace('HPA', '')
                        .replace('C', '')
                        .replace('m', '')
                        .replace('M', '')
                        .strip()
            )
            upper_line = line_normalized.upper()
            print(f"[STM32 → GUI]: {raw_line}")

            # -------------------------------
            # 1️⃣ Handle PPM / RC Channels
            # -------------------------------
            if 'PPM' in upper_line:
                values = line_normalized.split(':', 1)[1].strip().split()
                if len(values) >= 6:
                    raw_channels = [int(v) for v in values[:6]]

                    # Auto-scale to ~1000–2000 μs if raw
                    min_val, max_val = min(raw_channels), max(raw_channels)
                    if min_val < 800 or max_val > 2200:
                        scaled_channels = [
                            int(1000 + (v - min_val) * 1000 / max(1, max_val - min_val))
                            for v in raw_channels
                        ]
                        self.rc_channels = scaled_channels
                        print(f"[DEBUG] Raw PPM: {raw_channels} -> Scaled: {scaled_channels}")
                    else:
                        self.rc_channels = raw_channels

                    # Update RC status
                    self.rc_connected = True
                    self.rc_status.setText("RC Status: CONNECTED")
                    self.rc_status.setStyleSheet("""
                        font-size: 14px; font-weight: bold; color: #4caf50;
                        background-color: rgba(76, 175, 80, 0.2);
                        border: 2px solid #4caf50; border-radius: 5px; padding: 8px;
                    """)

                    # Update RC channel labels
                    labels = [
                        self.rc_ch1, self.rc_ch2, self.rc_ch3,
                        self.rc_ch4, self.rc_ch5, self.rc_ch6
                    ]
                    names = ["Aileron", "Elevator", "Throttle", "Rudder", "Aux1", "Aux2"]
                    for i, ch_val in enumerate(self.rc_channels):
                        labels[i].setText(f"CH{i+1} ({names[i]}): {ch_val} μs")

                return  # ✅ Exit after handling PPM

            # -------------------------------
            # 2️⃣ Handle ROLL/PITCH/YAW
            # -------------------------------
            if all(x in upper_line for x in ["ROLL", "PITCH", "YAW"]):
                parts = [p.strip() for p in line_normalized.split('|')]
                for part in parts:
                    if part.upper().startswith("ROLL"):
                        self.roll.setText("Roll: " + part.split(':')[1].strip())
                    elif part.upper().startswith("PITCH"):
                        self.pitch.setText("Pitch: " + part.split(':')[1].strip())
                    elif part.upper().startswith("YAW"):
                        self.yaw.setText("Yaw: " + part.split(':')[1].strip())
                return  # ✅ Exit after handling RPY

            # -------------------------------
            # 3️⃣ Handle IMU (ACC, GYRO, MAG)
            # -------------------------------
            if all(x in upper_line for x in ["ACC", "GYRO", "MAG"]):
                parts = [p.strip() for p in line_normalized.split('|')]
                for part in parts:
                    if part.upper().startswith("ACC"):
                        acc_data = part.split(':')[1].strip()
                        self.accel.setText("ACC: " + acc_data)
                        self.current_acc = [int(x.strip()) for x in acc_data.split(',')]
                    elif part.upper().startswith("GYRO"):
                        gyro_data = part.split(':')[1].strip()
                        self.gyro.setText("GYRO: " + gyro_data)
                        self.current_gyro = [int(x.strip()) for x in gyro_data.split(',')]
                    elif part.upper().startswith("MAG"):
                        self.mag.setText("MAG: " + part.split(':')[1].strip())
                return  # ✅ Exit after handling IMU

            # -------------------------------
            # 4️⃣ Handle Barometer (TEMP, PRESS, ALT)
            # -------------------------------
            if all(x in upper_line for x in ["TEMP", "PRESS", "ALT"]):
                parts = [p.strip() for p in line_normalized.split('|')]
                for part in parts:
                    if part.upper().startswith("TEMP"):
                        temp_val = float(part.split(':')[1].strip())
                        self.current_temp = temp_val
                        self.temp.setText(f"TEMP: {temp_val:.2f} °C")
                    elif part.upper().startswith("PRESS"):
                        press_val = float(part.split(':')[1].strip())
                        self.current_pressure = press_val
                        self.press.setText(f"PRESS: {press_val:.2f} hPa")
                    elif part.upper().startswith("ALT"):
                        alt_val = float(part.split(':')[1].strip())
                        self.altitude.setText(f"Relative Altitude: {alt_val:.2f} m")
                return  # ✅ Exit after handling barometer

            # -------------------------------
            # 5️⃣ Handle GPS Data (LAT, LON, GPS)
            # -------------------------------
            if "LAT" in upper_line and "LON" in upper_line:
                parts = [p.strip() for p in line_normalized.split('|')]
                for part in parts:
                    if part.upper().startswith("LAT"):
                        self.latitude.setText(f"Latitude: {part.split(':')[1].strip()}")
                    elif part.upper().startswith("LON"):
                        self.longitude.setText(f"Longitude: {part.split(':')[1].strip()}")
                    elif part.upper().startswith("GPS"):
                        self.gps_status.setText(f"Status: {part.split(':')[1].strip()}")
                return  # ✅ Exit after handling GPS

            # -------------------------------
            # 6️⃣ Unknown line (optional debug)
            # -------------------------------
            print(f"[DEBUG] ❓ Unknown data type: {raw_line}")

        except Exception as e:
            print(f"[ERROR parsing line]: {raw_line} — {e}")

    def get_rc_statistics(self):
        """Get current RC channel statistics"""
        if self.rc_connected and self.rc_channels:
            return {
                'channels': self.rc_channels,
                'connected': self.rc_connected,
                'min': min(self.rc_channels),
                'max': max(self.rc_channels),
                'avg': sum(self.rc_channels) / len(self.rc_channels),
                'range': max(self.rc_channels) - min(self.rc_channels)
            }
        return None

