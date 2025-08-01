import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox,
    QGridLayout, QComboBox, QLCDNumber
)
from PyQt5.QtCore import Qt

class FlightModesTab(QWidget):
    def __init__(self, serial_reader=None, mode_channel=4):
        """
        mode_channel: zero-based channel index for mode switch (CH5=4)
        """
        super().__init__()
        self.reader = serial_reader
        self.mode_channel = mode_channel  # CH5 by default

        layout = QVBoxLayout()

        # ───────────── Flight Mode Assignment Section ─────────────
        mode_group = QGroupBox("Flight Mode Assignment")
        mode_layout = QGridLayout()
        mode_group.setLayout(mode_layout)

        self.mode_selectors = []
        self.default_modes = ["Stabilize", "AltHold", "Loiter", "Auto", "RTL", "Acro"]

        for i in range(6):
            label = QLabel(f"PWM Range {i+1}:")
            combo = QComboBox()
            combo.addItems(self.default_modes)
            combo.setCurrentIndex(i % len(self.default_modes))  # Set different defaults
            self.mode_selectors.append(combo)
            mode_layout.addWidget(label, i, 0)
            mode_layout.addWidget(combo, i, 1)

        layout.addWidget(mode_group)

        # ───────────── Current PWM Display Section ─────────────
        pwm_group = QGroupBox("Current Mode Channel / Auto Detection")
        pwm_layout = QVBoxLayout()
        pwm_group.setLayout(pwm_layout)

        self.pwm_lcd = QLCDNumber()
        self.pwm_lcd.setDigitCount(5)
        self.pwm_lcd.setFixedHeight(80)
        self.pwm_lcd.display(0)  # Initialize with 0
        pwm_layout.addWidget(self.pwm_lcd)

        # Mode source indicator
        self.mode_source_label = QLabel("Mode Source: Waiting for Data...")
        self.mode_source_label.setAlignment(Qt.AlignCenter)
        self.mode_source_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFD54F;")
        pwm_layout.addWidget(self.mode_source_label)

        layout.addSpacing(20)
        layout.addWidget(pwm_group)

        # ───────────── Active Flight Mode Display ─────────────
        mode_display_group = QGroupBox("Active Flight Mode")
        mode_display_layout = QVBoxLayout()
        mode_display_group.setLayout(mode_display_layout)

        self.mode_label = QLabel("Waiting...")
        self.mode_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00e676;")
        self.mode_label.setAlignment(Qt.AlignCenter)
        mode_display_layout.addWidget(self.mode_label)

        layout.addSpacing(20)
        layout.addWidget(mode_display_group)

        self.setLayout(layout)

        # Color map for quick visual identification
        self.mode_colors = {
            "STABILIZE": "#00e676",
            "ALTHOLD": "#2196f3", 
            "LOITER": "#ffca28",
            "AUTO": "#ff5722",
            "RTL": "#9c27b0",
            "ACRO": "#f44336"
        }

        # PWM ranges for mode detection (will be auto-calibrated)
        self.pwm_ranges = [
            (1000, 1200),  # Mode 1
            (1200, 1400),  # Mode 2  
            (1400, 1600),  # Mode 3
            (1600, 1700),  # Mode 4
            (1700, 1850),  # Mode 5
            (1850, 2000),  # Mode 6
        ]

        # Track channel values for auto calibration
        self.ch_values = []
        self.calibration_samples = 0
        self.max_samples = 50  # Collect 50 samples for auto-calibration

        # Cache last known sensor values
        self.last_roll = 0
        self.last_pitch = 0
        self.last_alt = 0

        if self.reader:
            self.reader.data_received.connect(self.handle_serial_data)

    def handle_serial_data(self, line):
        try:
            raw_line = line.strip()
            print(f"[DEBUG] Raw serial data: {repr(raw_line)}")

            # Remove STM32 prefix if present
            if raw_line.startswith("[STM32") and "]: " in raw_line:
                raw_line = raw_line.split("]: ", 1)[1]

            line_upper = raw_line.upper()
            print(f"[DEBUG] Processed line: {line_upper}")

            # ═══════════════════════════════════════════════════════════
            # 🎯 PRIORITY 1: Handle PPM Data (RC Transmitter Mode)
            # ═══════════════════════════════════════════════════════════
            if self.try_parse_ppm(line_upper):
                return  # Successfully parsed PPM, skip sensor mode

            # ═══════════════════════════════════════════════════════════
            # 🎯 PRIORITY 2: Handle Sensor Data (Auto Mode Fallback)
            # ═══════════════════════════════════════════════════════════
            self.try_parse_sensors(line_upper)

        except Exception as e:
            print(f"[ERROR] Failed to parse line '{line}': {e}")

    def try_parse_ppm(self, line_upper):
        """Try to parse PPM data. Returns True if successful."""
        # Look for various PPM formats
        ppm_patterns = [
            r"PPM:\s*([\d\s]+)",           # PPM: 1500 1600 1400...
            r"CH:\s*([\d\s]+)",            # CH: 1500 1600 1400...  
            r"CHANNELS:\s*([\d\s]+)",      # CHANNELS: 1500 1600...
            r"RC:\s*([\d\s]+)",            # RC: 1500 1600...
            r"PWM:\s*([\d\s]+)",           # PWM: 1500 1600...
        ]
        
        # Special pattern for your format: CH1: 1463 | CH2: 1543 | etc.
        channel_pattern = r"CH(\d+):\s*(\d+)"
        channel_matches = re.findall(channel_pattern, line_upper)
        
        if channel_matches:
            print(f"[DEBUG] Found channel pattern matches: {channel_matches}")
            # Convert to channel values array
            channel_values = [0] * 8  # Initialize with 8 channels
            
            for ch_num, ch_value in channel_matches:
                ch_index = int(ch_num) - 1  # Convert to 0-based index
                if 0 <= ch_index < len(channel_values):
                    channel_values[ch_index] = int(ch_value)
            
            print(f"[DEBUG] Parsed channel array: {channel_values}")
            
            if len(channel_values) > self.mode_channel and channel_values[self.mode_channel] > 0:
                ch_value = channel_values[self.mode_channel]
                print(f"[DEBUG] Mode channel (CH{self.mode_channel+1}) value: {ch_value}")
                
                # Update PWM display
                self.pwm_lcd.display(ch_value)
                self.mode_source_label.setText(f"Mode Source: RC Channel {self.mode_channel+1}")
                self.mode_source_label.setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #4CAF50;"
                )
                
                # Determine flight mode from PWM value
                mode = self.pwm_to_mode(ch_value)
                self.update_mode_label(mode)
                
                return True  # Successfully parsed channel data

        for pattern in ppm_patterns:
            match = re.search(pattern, line_upper)
            if match:
                values_str = match.group(1).strip()
                print(f"[DEBUG] Found PPM pattern: {pattern} -> {values_str}")
                
                # Parse channel values
                try:
                    channel_values = [int(x) for x in values_str.split() if x.isdigit()]
                    print(f"[DEBUG] Parsed channels: {channel_values}")
                    
                    if len(channel_values) > self.mode_channel:
                        ch_value = channel_values[self.mode_channel]
                        print(f"[DEBUG] Mode channel (CH{self.mode_channel+1}) value: {ch_value}")
                        
                        # Update PWM display
                        self.pwm_lcd.display(ch_value)
                        self.mode_source_label.setText(f"Mode Source: RC Channel {self.mode_channel+1}")
                        self.mode_source_label.setStyleSheet(
                            "font-size: 14px; font-weight: bold; color: #4CAF50;"
                        )
                        
                        # Determine flight mode from PWM value
                        mode = self.pwm_to_mode(ch_value)
                        self.update_mode_label(mode)
                        
                        return True  # Successfully parsed PPM
                        
                except ValueError as e:
                    print(f"[ERROR] Failed to parse channel values: {e}")
                    
        return False  # No PPM data found

    def pwm_to_mode(self, pwm_value):
        """Convert PWM value to flight mode using ranges."""
        # Auto-calibrate ranges if we have enough samples
        if self.calibration_samples < self.max_samples:
            self.ch_values.append(pwm_value)
            self.calibration_samples += 1
            
            if self.calibration_samples == self.max_samples:
                self.auto_calibrate_ranges()
        
        # Find which range the PWM value falls into
        for i, (min_val, max_val) in enumerate(self.pwm_ranges):
            if min_val <= pwm_value <= max_val:
                selected_mode = self.mode_selectors[i].currentText()
                print(f"[DEBUG] PWM {pwm_value} -> Range {i+1} -> Mode: {selected_mode}")
                return selected_mode
        
        # Default fallback
        return "Unknown"

    def auto_calibrate_ranges(self):
        """Auto-calibrate PWM ranges based on collected samples."""
        if not self.ch_values:
            return
            
        self.ch_values.sort()
        min_pwm = min(self.ch_values)
        max_pwm = max(self.ch_values)
        
        print(f"[DEBUG] Auto-calibrating: min={min_pwm}, max={max_pwm}")
        
        # Create 6 equal ranges
        range_size = (max_pwm - min_pwm) / 6
        self.pwm_ranges = []
        
        for i in range(6):
            range_min = int(min_pwm + i * range_size)
            range_max = int(min_pwm + (i + 1) * range_size)
            self.pwm_ranges.append((range_min, range_max))
            
        print(f"[DEBUG] Calibrated ranges: {self.pwm_ranges}")

    def try_parse_sensors(self, line_upper):
        """Try to parse sensor data for auto mode detection."""
        parts = [p.strip() for p in line_upper.split("|")]
        roll = pitch = alt = None

        for part in parts:
            if "ROLL" in part and ":" in part:
                try:
                    val = re.sub(r"[^0-9.\-]", "", part.split(":")[1])
                    if val:
                        roll = float(val)
                        self.last_roll = roll
                except:
                    pass
                    
            elif "PITCH" in part and ":" in part:
                try:
                    val = re.sub(r"[^0-9.\-]", "", part.split(":")[1])
                    if val:
                        pitch = float(val)
                        self.last_pitch = pitch
                except:
                    pass
                    
            elif "ALT" in part and ":" in part:
                try:
                    val = re.sub(r"[^0-9.\-]", "", part.split(":")[1])
                    if val:
                        alt = float(val)
                        self.last_alt = alt
                except:
                    pass

        # Use last known values if current line didn't include them
        roll = roll if roll is not None else self.last_roll
        pitch = pitch if pitch is not None else self.last_pitch  
        alt = alt if alt is not None else self.last_alt

        print(f"[DEBUG] Sensor values: roll={roll}, pitch={pitch}, alt={alt}")

        # Determine mode from sensor data
        if roll is not None and pitch is not None:
            mode = None
            if abs(roll) < 5 and abs(pitch) < 5:
                mode = "Loiter" if alt and alt > 0.5 else "Stabilize"
            elif abs(roll) > 25 or abs(pitch) > 25:
                mode = "Acro"
            else:
                mode = "AltHold"

            if mode:
                self.pwm_lcd.display(0)  # 0 indicates sensor mode
                self.mode_source_label.setText("Mode Source: Sensor Auto Mode")
                self.mode_source_label.setStyleSheet(
                    "font-size: 14px; font-weight: bold; color: #FFD54F;"
                )
                print(f"[DEBUG] Sensor mode detected: {mode}")
                self.update_mode_label(mode)

    def update_mode_label(self, mode_name):
        """Updates the active mode label text and color."""
        self.mode_label.setText(mode_name)
        color = self.mode_colors.get(mode_name.upper(), "#00e676")
        self.mode_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
        print(f"[DEBUG] Mode label updated: {mode_name} (color: {color})")

    def set_mode_channel(self, channel):
        """Change which channel is used for mode switching (0-based)."""
        self.mode_channel = channel
        print(f"[DEBUG] Mode channel changed to: CH{channel+1}")

    def manual_test_ppm(self, test_values):
        """Manual test function for debugging."""
        test_line = f"PPM: {' '.join(map(str, test_values))}"
        print(f"[TEST] Sending test PPM: {test_line}")
        self.handle_serial_data(test_line)