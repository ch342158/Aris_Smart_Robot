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

        # while True:
        #     # Wait for a response (optional)
        #     response = ser.readline().decode().strip()
        #     if response:
        #         print(f"ACK: {response}")
        #         # Check if the response indicates that the motor has finished running
        #         if "Motor 1 finished running" in response:
        #             print("Motor has finished running, breaking the loop.")
        #
        #             # Extract and convert the position from the response
        #             position_str = response.split("position = ")[-1]  # Get the part after 'position = '
        #             try:
        #                 position = int(position_str)  # Convert to integer
        #                 return position  # Return the position value
        #             except ValueError:
        #                 print("Error: Could not convert the position to an integer.")
        #                 return None  # Return None if conversion fails

    except serial.SerialException as e:
        print(f"Error during communication: {e}")
        return None  # Return None if there is a communication error
    except KeyboardInterrupt:
        print("Program interrupted by the user")
        return None  # Return None if the program is interrupted by the user


def UART_ReceiveMessage():
    # Implementation goes here
    pass
