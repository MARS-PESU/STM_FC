import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QGroupBox, QFrame
)
from PyQt5.QtPositioning import QGeoPositionInfoSource
from .attitude_widget import AttitudeIndicator
from .compass_widget import CompassWidget
import math


class FlightDataTab(QWidget):
    def __init__(self, serial_reader=None):
        super().__init__()
        self.reader = serial_reader

        # Initialize GPS position source
        self.pos_source = QGeoPositionInfoSource.createDefaultSource(self)
        if self.pos_source:
            self.pos_source.positionUpdated.connect(self.position_updated)
            self.pos_source.startUpdates()

        # Store sensor values for PPM calculation
        self.current_acc = [0, 0, 0]
        self.current_gyro = [0, 0, 0]
        self.current_temp = 25.0
        self.current_pressure = 1013.25

        # Sensor calibration ranges for proper PPM mapping
        self.sensor_ranges = {
            'acc_x': {'min': -2000, 'max': 2000},     # Typical accelerometer range (mg)
            'acc_y': {'min': -2000, 'max': 2000},
            'acc_z': {'min': -2000, 'max': 2000},
            'gyro_x': {'min': -1000, 'max': 1000},    # Typical gyroscope range (dps)
            'gyro_y': {'min': -1000, 'max': 1000},
            'gyro_z': {'min': -1000, 'max': 1000},
            'temp': {'min': -10, 'max': 60},          # Temperature range (°C)
            'pressure': {'min': 950, 'max': 1050}     # Pressure range (hPa)
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
        sensor_panel.addWidget(self.create_ppm_group())  # Added PPM group
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
        
        # GPS Status with icon-like styling
        self.gps_status = QLabel("Status: Searching...")
        self.gps_status.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #FFA726;
            background-color: rgba(255, 167, 38, 0.1);
            border-radius: 5px;
            padding: 6px;
        """)
        
        # Latitude with coordinate styling
        self.latitude = QLabel("Latitude: 12.9351° N")
        self.latitude.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #42A5F5;
            background-color: rgba(66, 165, 245, 0.1);
            border-radius: 5px;
            padding: 6px;
        """)
        
        # Longitude with coordinate styling
        self.longitude = QLabel("Longitude: 77.5360° E")
        self.longitude.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #AB47BC;
            background-color: rgba(171, 71, 188, 0.1);
            border-radius: 5px;
            padding: 6px;
        """)
        
        layout.addWidget(self.gps_status)
        layout.addWidget(self.latitude)
        layout.addWidget(self.longitude)
        group.setLayout(layout)
        return group

    def create_baro_group(self):
        group = QGroupBox("Barometer")
        layout = QVBoxLayout()
        
        # Altitude with elevation styling
        self.altitude = QLabel("Relative Altitude: -- m")
        self.altitude.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #66BB6A;
            background-color: rgba(102, 187, 106, 0.1);
            border-radius: 5px;
            padding: 6px;
        """)
        
        # Temperature with thermal styling
        self.temp = QLabel("TEMP: -- °C")
        self.temp.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #FF7043;
            background-color: rgba(255, 112, 67, 0.1);
            border-radius: 5px;
            padding: 6px;
        """)
        
        # Pressure with atmospheric styling
        self.press = QLabel("PRESS: -- hPa")
        self.press.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #26C6DA;
            background-color: rgba(38, 198, 218, 0.1);
            border-radius: 5px;
            padding: 6px;
        """)
        
        layout.addWidget(self.altitude)
        layout.addWidget(self.temp)
        layout.addWidget(self.press)
        group.setLayout(layout)
        return group

    def create_imu_group(self):
        group = QGroupBox("IMU / Sensor Data")
        layout = QVBoxLayout()

        # Roll with rotation styling
        self.roll = QLabel("Roll: --°")
        self.roll.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #EF5350;
            background-color: rgba(239, 83, 80, 0.1);
            border-left: 4px solid #EF5350;
            border-radius: 5px;
            padding: 6px;
        """)
        
        # Pitch with tilt styling
        self.pitch = QLabel("Pitch: --°")
        self.pitch.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #5C6BC0;
            background-color: rgba(92, 107, 192, 0.1);
            border-left: 4px solid #5C6BC0;
            border-radius: 5px;
            padding: 6px;
        """)
        
        # Yaw with compass styling
        self.yaw = QLabel("Yaw: --°")
        self.yaw.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #FFCA28;
            background-color: rgba(255, 202, 40, 0.1);
            border-left: 4px solid #FFCA28;
            border-radius: 5px;
            padding: 6px;
        """)

        # Accelerometer with motion styling
        self.accel = QLabel("ACC: ---, ---, ---")
        self.accel.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #8BC34A;
            background-color: rgba(139, 195, 74, 0.1);
            border: 1px solid #8BC34A;
            border-radius: 5px;
            padding: 5px;
        """)
        
        # Gyroscope with rotation styling  
        self.gyro = QLabel("GYRO: ---, ---, ---")
        self.gyro.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #FF9800;
            background-color: rgba(255, 152, 0, 0.1);
            border: 1px solid #FF9800;
            border-radius: 5px;
            padding: 5px;
        """)
        
        # Magnetometer with magnetic styling
        self.mag = QLabel("MAG: ---, ---, ---")
        self.mag.setStyleSheet("""
            font-size: 13px; 
            font-weight: bold; 
            color: #E91E63;
            background-color: rgba(233, 30, 99, 0.1);
            border: 1px solid #E91E63;
            border-radius: 5px;
            padding: 5px;
        """)

        layout.addWidget(self.roll)
        layout.addWidget(self.pitch)
        layout.addWidget(self.yaw)
        layout.addWidget(self.accel)
        layout.addWidget(self.gyro)
        layout.addWidget(self.mag)

        group.setLayout(layout)
        return group

    def create_ppm_group(self):
        group = QGroupBox("PPM Channels (μs)")
        layout = QVBoxLayout()
        
        # Create 6 PPM channel labels with descriptions
        self.ppm_ch1 = QLabel("CH1 (Roll): 1500 μs")
        self.ppm_ch2 = QLabel("CH2 (Pitch): 1500 μs")
        self.ppm_ch3 = QLabel("CH3 (Throttle): 1500 μs")
        self.ppm_ch4 = QLabel("CH4 (Yaw): 1500 μs")
        self.ppm_ch5 = QLabel("CH5 (Aux1): 1500 μs")
        self.ppm_ch6 = QLabel("CH6 (Aux2): 1500 μs")
        
        # Enhanced styling with gradients and borders
        ppm_styles = [
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
        
        for i, label in enumerate([self.ppm_ch1, self.ppm_ch2, self.ppm_ch3, self.ppm_ch4, self.ppm_ch5, self.ppm_ch6]):
            label.setStyleSheet(ppm_styles[i])
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

    def map_to_ppm_range(self, value, sensor_min, sensor_max, ppm_min=1000, ppm_max=2000):
        """
        Map sensor value to PPM range (1000-2000 μs) with proper scaling
        """
        try:
            # Clamp the value to sensor range
            clamped_value = max(sensor_min, min(sensor_max, value))
            
            # Map to 0-1 range
            normalized = (clamped_value - sensor_min) / (sensor_max - sensor_min)
            
            # Map to PPM range
            ppm_value = ppm_min + (normalized * (ppm_max - ppm_min))
            
            return int(ppm_value)
        except:
            return 1500  # Return neutral if calculation fails

    def calculate_ppm_channels(self, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z, temp, pressure):
        """
        Calculate 6 PPM channels with proper sensor-to-PPM mapping
        Each channel represents a different flight control axis
        """
        try:
            # === CHANNEL 1: ROLL (Accelerometer Y-axis) ===
            # Roll channel based on tilt detection
            roll_angle = math.atan2(acc_y, math.sqrt(acc_x**2 + acc_z**2)) * 180 / math.pi
            ch1 = self.map_to_ppm_range(roll_angle, -45, 45)  # ±45° roll range
            
            # === CHANNEL 2: PITCH (Accelerometer X-axis) ===
            # Pitch channel based on forward/backward tilt
            pitch_angle = math.atan2(-acc_x, math.sqrt(acc_y**2 + acc_z**2)) * 180 / math.pi
            ch2 = self.map_to_ppm_range(pitch_angle, -45, 45)  # ±45° pitch range
            
            # === CHANNEL 3: THROTTLE (Accelerometer Z-axis magnitude) ===
            # Throttle based on vertical acceleration magnitude
            z_magnitude = abs(acc_z)
            ch3 = self.map_to_ppm_range(z_magnitude, 800, 1200)  # Typical Z-axis range when moving
            
            # === CHANNEL 4: YAW (Gyroscope Z-axis) ===
            # Yaw rate channel
            ch4 = self.map_to_ppm_range(gyro_z, self.sensor_ranges['gyro_z']['min'], 
                                       self.sensor_ranges['gyro_z']['max'])
            
            # === CHANNEL 5: AUX1 (Temperature-based) ===
            # Auxiliary channel based on temperature
            ch5 = self.map_to_ppm_range(temp, self.sensor_ranges['temp']['min'], 
                                       self.sensor_ranges['temp']['max'])
            
            # === CHANNEL 6: AUX2 (Pressure/Altitude-based) ===
            # Auxiliary channel based on barometric pressure
            ch6 = self.map_to_ppm_range(pressure, self.sensor_ranges['pressure']['min'], 
                                       self.sensor_ranges['pressure']['max'])
            
            return [ch1, ch2, ch3, ch4, ch5, ch6]
            
        except Exception as e:
            print(f"[ERROR calculating PPM channels]: {e}")
            return [1500, 1500, 1500, 1500, 1500, 1500]  # Default neutral values

    def position_updated(self, pos_info):
        """Handle position updates from QGeoPositionInfoSource"""
        if pos_info.isValid():
            coord = pos_info.coordinate()
            self.latitude.setText(f"Latitude: {coord.latitude()}° N")
            self.longitude.setText(f"Longitude: {coord.longitude()}° E")
            self.gps_status.setText("Status: Active")
        else:
            self.gps_status.setText("Status: No Fix")

    def get_channel_status(self, ppm_value):
        """Get color-coded status for PPM value"""
        if ppm_value < 1200:
            return "LOW", "#ff5722"
        elif ppm_value > 1800:
            return "HIGH", "#ff5722"
        else:
            return "OK", "#4caf50"

    def handle_serial_data(self, line):
        print(f"[STM32 → GUI]: {line}")

        try:
            if 'ROLL' in line and 'PITCH' in line and 'YAW' in line:
                parts = [p.strip() for p in line.split('|')]
                for part in parts:
                    if part.startswith("ROLL"):
                        self.roll.setText("Roll: " + part.split(':')[1].strip())
                    elif part.startswith("PITCH"):
                        self.pitch.setText("Pitch: " + part.split(':')[1].strip())
                    elif part.startswith("YAW"):
                        self.yaw.setText("Yaw: " + part.split(':')[1].strip())

            elif 'ACC' in line and 'GYRO' in line and 'MAG' in line:
                parts = [p.strip() for p in line.split('|')]
                for part in parts:
                    if part.startswith("ACC"):
                        acc_data = part.split(':')[1].strip()
                        self.accel.setText("ACC: " + acc_data)
                        # Parse ACC values for PPM calculation
                        acc_values = [int(x.strip()) for x in acc_data.split(',')]
                        self.current_acc = acc_values
                        
                    elif part.startswith("GYRO"):
                        gyro_data = part.split(':')[1].strip()
                        self.gyro.setText("GYRO: " + gyro_data)
                        # Parse GYRO values for PPM calculation
                        gyro_values = [int(x.strip()) for x in gyro_data.split(',')]
                        self.current_gyro = gyro_values
                        
                    elif part.startswith("MAG"):
                        self.mag.setText("MAG: " + part.split(':')[1].strip())

                # Calculate and update PPM channels after parsing ACC/GYRO
                ppm_channels = self.calculate_ppm_channels(
                    self.current_acc[0], self.current_acc[1], self.current_acc[2],
                    self.current_gyro[0], self.current_gyro[1], self.current_gyro[2],
                    self.current_temp, self.current_pressure
                )
                
                # Update PPM channel displays with status indicators
                self.ppm_ch1.setText(f"CH1 (Roll): {ppm_channels[0]} μs")
                self.ppm_ch2.setText(f"CH2 (Pitch): {ppm_channels[1]} μs")
                self.ppm_ch3.setText(f"CH3 (Throttle): {ppm_channels[2]} μs")
                self.ppm_ch4.setText(f"CH4 (Yaw): {ppm_channels[3]} μs")
                self.ppm_ch5.setText(f"CH5 (Aux1): {ppm_channels[4]} μs")
                self.ppm_ch6.setText(f"CH6 (Aux2): {ppm_channels[5]} μs")
                
                # Send PPM data to Radio Calibration tab
                ppm_line = f"CH1: {ppm_channels[0]} | CH2: {ppm_channels[1]} | CH3: {ppm_channels[2]} | CH4: {ppm_channels[3]} | CH5: {ppm_channels[4]} | CH6: {ppm_channels[5]}"
                
                # Emit the PPM line so Radio tab can receive it
                if self.reader and hasattr(self.reader, 'data_received'):
                    self.reader.data_received.emit(ppm_line)
                
                print(f"[DEBUG] PPM Channels: {ppm_channels}")
                print(f"[DEBUG] Sent to Radio tab: {ppm_line}")

            elif 'TEMP' in line and 'PRESS' in line and 'ALT' in line:
                parts = [p.strip() for p in line.split('|')]
                for part in parts:
                    if part.startswith("TEMP"):
                        temp_str = part.split(':')[1].replace('C', '').strip()
                        self.current_temp = float(temp_str)
                        self.temp.setText("TEMP: " + part.split(':')[1].strip())
                        
                    elif part.startswith("PRESS"):
                        press_str = part.split(':')[1].replace('hPa', '').strip()
                        self.current_pressure = float(press_str)
                        self.press.setText("PRESS: " + part.split(':')[1].strip())
                        
                    elif part.startswith("ALT"):
                        self.altitude.setText("Relative Altitude: " + part.split(':')[1].strip())

            # Handle GPS data parsing
            elif 'LAT' in line and 'LON' in line:
                parts = [p.strip() for p in line.split('|')]
                for part in parts:
                    if part.startswith("LAT"):
                        lat_data = part.split(':')[1].strip()
                        self.latitude.setText(f"Latitude: {lat_data}")
                        
                    elif part.startswith("LON"):
                        lon_data = part.split(':')[1].strip()
                        self.longitude.setText(f"Longitude: {lon_data}")
                        
                    elif part.startswith("GPS"):
                        status_data = part.split(':')[1].strip()
                        self.gps_status.setText(f"Status: {status_data}")

        except Exception as e:
            print(f"[ERROR parsing line]: {line} — {e}")

    def update_sensor_ranges(self, sensor_type, min_val, max_val):
        """
        Allow dynamic updating of sensor ranges for better PPM calibration
        """
        if sensor_type in self.sensor_ranges:
            self.sensor_ranges[sensor_type]['min'] = min_val
            self.sensor_ranges[sensor_type]['max'] = max_val
            print(f"[INFO] Updated {sensor_type} range: {min_val} to {max_val}")

    def get_ppm_statistics(self):
        """
        Get current PPM channel statistics for monitoring
        """
        if hasattr(self, 'current_acc') and hasattr(self, 'current_gyro'):
            ppm_channels = self.calculate_ppm_channels(
                self.current_acc[0], self.current_acc[1], self.current_acc[2],
                self.current_gyro[0], self.current_gyro[1], self.current_gyro[2],
                self.current_temp, self.current_pressure
            )
            
            return {
                'channels': ppm_channels,
                'min': min(ppm_channels),
                'max': max(ppm_channels),
                'avg': sum(ppm_channels) / len(ppm_channels),
                'range': max(ppm_channels) - min(ppm_channels)
            }
        return None