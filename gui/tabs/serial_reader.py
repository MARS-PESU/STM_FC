import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal


class SerialReader(QObject):
    data_received = pyqtSignal(str)

    def __init__(self, port=None, baudrate=115200):  # Updated baudrate
        super().__init__()
        self.port = port or self.auto_detect_port()
        self.baudrate = baudrate
        self.ser = None
        self.running = False

    @staticmethod
    def auto_detect_port():
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "ttyACM" in port.device or "COM" in port.device or "ttyUSB" in port.device:
                print(f"[SerialReader] Auto-detected port: {port.device}")
                return port.device
        print("[SerialReader] No serial port auto-detected.")
        return None

    def start_reading(self):
        if not self.port:
            print("[SerialReader] ❌ No serial port detected.")
            return

        self.running = True
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"[SerialReader] ✅ Connected to {self.port} at {self.baudrate} baud")
            print("[SerialReader] Entering read loop...")

            while self.running and self.ser.is_open:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    print(f"[RAW FROM STM32]: {line}")  # << 🔥 Debug print here
                    self.data_received.emit(line)

        except serial.SerialException as e:
            print(f"[SerialReader] Serial error: {e}")
        except Exception as e:
            print(f"[SerialReader] Unexpected error: {e}")

    def stop(self):
        print("[SerialReader] Stopping serial reader...")
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[SerialReader] Serial port closed")
