# Send_Command.py
# Called by Motor_Control.py Called by main_UI.py

import serial
from PyQt6.QtWidgets import QMessageBox
import time
import Motor_Control

ser = None  # Declare ser globally


def UART_Init(comport):
    global ser  # Use the global ser variable
    port = f'COM{comport}'
    baudrate = 9600
    timeout = 1

    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        if ser.is_open:
            print(f"Serial Port Open at {port}")
        return True
    except serial.SerialException as e:
        # Show the error message using QMessageBox
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(f"Failed to open serial port: {e}, \n\nPlease initialize the USB port manually in the Main UI")
        msg_box.setWindowTitle("Serial Port Error")
        msg_box.exec()
        return False


def UART_sendCommand(slaveAddr,motionType, speed, acc, angle):
    global ser  # Use the global ser variable

    if ser is None or not ser.is_open:
        print("Serial port is not open")
        return None  # Return None if the serial port is not open

    try:
        # Construct the command string
        command = f"{round(slaveAddr)} {motionType} {round(speed)} {round(acc)} {round(angle)}\n"
        ser.write(command.encode())  # Send the command over UART
        print(f"Sent: {command.strip()}")

    except serial.SerialException as e:
        print(f"Error during communication: {e}")
        return None  # Return None if there is a communication error
    except KeyboardInterrupt:
        print("Program interrupted by the user")
        return None  # Return None if the program is interrupted by the user


def UART_receiveAllPositions():
    global ser  # Use the global ser variable

    # if ser is None or not ser.is_open:
    #     print("Serial port is not open")
    #     return None  # Return None if the serial port is not open

    try:
        # Buffer to store the entire response
        response = ""

        while True:
            # Read one line at a time from the UART
            line = ser.readline().decode().strip()
            if line:
                response += line + "\n"
                # Break the loop if the conclusion mark is found
                if "groupRunCycleDone" in line:
                    break

        # Print and return the full response
        print(f"Received: {response.strip()}")
        return response.strip()

    except serial.SerialException as e:
        print(f"Error during communication: {e}")
        return None
    except KeyboardInterrupt:
        print("Program interrupted by the user")
        return None
