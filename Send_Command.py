import serial
import time
import Motor_Control

ser = None  # Declare ser globally


def UART_Init():
    global ser  # Use the global ser variable
    port = 'COM6'
    baudrate = 9600
    timeout = 1

    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        if ser.is_open:
            print(f"Serial Port Open at {port}")
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")


def UART_sendCommand(slaveAddr, speed, acc, angle):
    global ser  # Use the global ser variable

    if ser is None or not ser.is_open:
        print("Serial port is not open")
        return

    try:
        command = f"{round(slaveAddr)} {round(speed)} {round(acc)} {round(angle)}\n"
        ser.write(command.encode())
        print(f"Sent: {command.strip()}")

        response = ser.readline().decode().strip()
        if response:
            print(f"Received: {response}")
        time.sleep(1)

    except serial.SerialException as e:
        print(f"Error during communication: {e}")
    except KeyboardInterrupt:
        print("Program interrupted by the user")
    finally:
        if ser.is_open:
            ser.close()
            print("Serial port closed")


def UART_ReceiveMessage():
    # Implementation goes here
    pass
