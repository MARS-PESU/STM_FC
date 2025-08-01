import serial

port = "COM12"   # Your STM32's port 
baudrate = 9600  # Match this with your STM32 code

try:
    ser = serial.Serial(port, baudrate, timeout=1)
    print(f"Connected to {port} at {baudrate} baud")

    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line:
            print("Received:", line)
except Exception as e:
    print("Serial error:", e)
