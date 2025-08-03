import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, QThread

class SerialReader(QObject):
    data_received = pyqtSignal(str)

    def __init__(self, port=None, baudrate=115200):
        super().__init__()
        self.baudrate = baudrate
        self.port = port or self.auto_detect_port()
        self.ser = None
        self.running = False
        self.thread = None

    def auto_detect_port(self):
        """Auto-detect STM32 or USB serial device."""
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            if "STM" in p.description or "USB" in p.description:
                print(f"[SerialReader] Auto-detected port: {p.device}")
                return p.device
        print("[SerialReader] No STM32 found. Falling back to COM12")
        return "COM12"

    def start_reading(self):
        """Open serial and start reading in a background thread."""
        if self.ser and self.ser.is_open:
            print("[SerialReader] Port already open. Skipping re-open.")
            return

        print(f"[SerialReader] Attempting to open {self.port} at {self.baudrate} baud")
        try:
            # Short timeout for low-latency updates
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.01)
            self.running = True
        except Exception as e:
            print(f"[SerialReader] Serial error: {e}")
            return

        # Move this object to a dedicated QThread
        self.thread = QThread()
        self.moveToThread(self.thread)
        self.thread.started.connect(self.read_loop)
        self.thread.start()
        print("[SerialReader] Serial reading thread started")

    def read_loop(self):
        """Non-blocking continuous read loop with DEBUG output."""
        print("[SerialReader] Entering read loop...")
        buffer = ""
        line_count = 0
        while self.running and self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting:
                    # Read all available data
                    raw_data = self.ser.read(self.ser.in_waiting).decode(errors="ignore")
                    buffer += raw_data
                    
                    if "\n" in buffer:
                        lines = buffer.split("\n")
                        for line in lines[:-1]:
                            line = line.strip()
                            if line:
                                line_count += 1
                                
                                # 🐛 DEBUG: Print every received line
                                print(f"[DEBUG] Line {line_count}: '{line}'")
                                
                                # 🐛 DEBUG: Check if it's RC data
                                if "RC1:" in line:
                                    print(f"[DEBUG] ✅ RC Channel data detected: {line}")
                                elif "RC_STATUS:" in line:
                                    print(f"[DEBUG] ✅ RC Status data detected: {line}")
                                elif line.startswith("[RC]"):
                                    print(f"[DEBUG] ✅ RC Debug message: {line}")
                                else:
                                    print(f"[DEBUG] ❓ Unknown data type: {line}")
                                
                                # Emit the line to main GUI
                                self.data_received.emit(line)
                        buffer = lines[-1]  # keep last incomplete line
            except Exception as e:
                print(f"[SerialReader] Read error: {e}")
                break

    def stop(self):
        """Stop the serial reader safely."""
        print("[SerialReader] Stopping serial thread...")
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SerialReader] Serial port closed")
        if self.thread:
            self.thread.quit()
            self.thread.wait()
            print("[SerialReader] Thread stopped")