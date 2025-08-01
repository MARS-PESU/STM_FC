import serial
import time

port = "COM12"
baudrate = 115200

try:
    ser = serial.Serial(port, baudrate, timeout=0.5)
    print(f"Connected to {port} at {baudrate} baud.")
    time.sleep(2)  # Give STM32 time to reset/init

    while True:
        line = ser.readline().decode("utf-8", errors="ignore")
        if line:
            print(f"[STM32]: {line}", end='')  # Don't strip \n to see if it’s sent
except Exception as e:
    print("Error:", e)
