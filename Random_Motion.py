import serial
import time
import random

# Configure the serial port
ser = serial.Serial(
    port='COM3',  # Update this to the correct port on your system (e.g., COM3 on Windows)
    baudrate=9600,
    timeout=1  # Timeout in seconds
)

# Ensure the serial port is open
if ser.is_open:
    print("Serial port opened successfully")
else:
    ser.open()
    print("Serial port opened manually")

try:
    while True:
        # Example: Send command with slaveAddr=1, speed=2000, acc=160, axis=random value
        slaveAddr = 1
        speed = 2400
        acc = 220
        axis = random.randint(-4096, 4096)
        # axis = 0

        command = f"{slaveAddr} {speed} {acc} {axis}\n"
        ser.write(command.encode())
        print(f"Sent: {command.strip()}")

        # Wait for a response (optional)
        response = ser.readline().decode().strip()
        if response:
            print(f"Received: {response}")

        time.sleep(1)

except KeyboardInterrupt:
    print("Program interrupted by the user")

finally:
    # Close the serial port
    if ser.is_open:
        ser.close()
    print("Serial port closed")

# Optional sleep time if you intend to pause the script for a long period
# Adjust as needed
time.sleep(1.5)  # Adjust the sleep duration if necessary (currently set to 1.5 seconds)
