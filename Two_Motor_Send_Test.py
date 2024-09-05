import serial
import time

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
    # Function to send command to the motor
    def send_command(slaveAddr, speed, acc, axis):
        command = f"{slaveAddr} {speed} {acc} {axis}\n"
        ser.write(command.encode())
        print(f"Sent to Motor {slaveAddr}: {command.strip()}")

    # Send command to motor 1
    send_command(1, 2000, 225, 13189)
    time.sleep(0.1)
    # Send command to motor 2
    send_command(2, 800, 225, 7431)

    # Optionally, read any ACKs or responses from the STM32
    while True:
        response = ser.readline().decode().strip()
        if response:
            print(response)
        time.sleep(0.1)  # Small delay to avoid busy-waiting

except KeyboardInterrupt:
    print("Program interrupted by the user")

except serial.SerialException as e:
    print(f"Serial communication error: {e}")

finally:
    # Close the serial port
    ser.close()
    print("Serial port closed")
