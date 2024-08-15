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

try:
    # Example: Send command with slaveAddr=1, speed=60, acc=30, axis=4000
    slaveAddr = 1
    speed = 1600
    acc = 225
    axis = 0

    command = f"{slaveAddr} {speed} {acc} {axis}\n"
    ser.write(command.encode())
    print(f"Sent: {command.strip()}")

    while True:
        # Wait for a response (optional)
        response = ser.readline().decode().strip()
        if response:
            print(f"ACK: {response}")

        time.sleep(1)

except KeyboardInterrupt:
    print("Program interrupted by the user")

# finally:
#     # Close the serial port
#     ser.close()
#     print("Serial port closed")

