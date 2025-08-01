from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QGroupBox, QGridLayout
)

class RadioCalibrationTab(QWidget):
    def __init__(self, serial_reader=None):
        super().__init__()
        self.reader = serial_reader
        self.setStyleSheet("font-size: 14px;")

        self.channel_count = 6
        self.channel_bars = []
        self.channel_labels = []

        layout = QVBoxLayout()

        # Group Box for Channels
        group_box = QGroupBox("Radio Channels")
        group_layout = QGridLayout()

        for i in range(self.channel_count):
            label = QLabel(f"CH{i+1}: 1500 µs")
            progress = QProgressBar()
            progress.setRange(1000, 2000)
            progress.setValue(1500)
            progress.setTextVisible(False)
            group_layout.addWidget(label, i, 0)
            group_layout.addWidget(progress, i, 1)
            self.channel_labels.append(label)
            self.channel_bars.append(progress)

        group_box.setLayout(group_layout)
        layout.addWidget(group_box)

        # Button Row
        button_layout = QHBoxLayout()
        self.calibrate_button = QPushButton("Calibrate")
        self.save_button = QPushButton("Save")
        self.reset_button = QPushButton("Reset")

        button_layout.addWidget(self.calibrate_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.reset_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Connect shared serial reader
        if self.reader:
            self.reader.data_received.connect(self.handle_serial_data)

    def handle_serial_data(self, line):
        try:
            # Look for PPM channel data
            if "CH1:" in line and "|" in line:
                print(f"[Radio Tab] Received PPM line: {line}")
                
                # Expecting: CH1: 1500 | CH2: 1485 | ...
                parts = [p.strip() for p in line.split('|')]
                
                for part in parts:
                    if ':' in part and 'CH' in part:
                        # Split on colon
                        ch_label, val_str = part.split(':', 1)
                        
                        # Extract channel number
                        ch_label = ch_label.strip()
                        if ch_label.startswith('CH'):
                            try:
                                ch_num = ch_label[2:]  # Get number after "CH"
                                ch_index = int(ch_num) - 1
                                
                                # Extract value and remove units
                                val_str = val_str.strip().replace('μs', '').replace('µs', '').strip()
                                value = int(val_str)
                                
                                # Update channel if valid
                                if 0 <= ch_index < self.channel_count and 1000 <= value <= 2000:
                                    self.channel_bars[ch_index].setValue(value)
                                    self.channel_labels[ch_index].setText(f"CH{ch_index+1}: {value} µs")
                                    print(f"[Radio Tab] Updated CH{ch_index+1}: {value}")
                                    
                            except (ValueError, IndexError) as e:
                                print(f"[Radio Tab] Error parsing '{part}': {e}")
                                
        except Exception as e:
            print(f"[Radio Tab] Failed to parse line: {line} — {e}")