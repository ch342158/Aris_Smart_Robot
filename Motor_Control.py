import math
import Send_Command
import time

# this program prepares the data to be sent to the edge stm32 controller to control the motor drivers

def motionActuate(speed, acc, micro, reduction, J1, J2, J3, J4):
    acc_J1 = accelerationControl(acc)
    speed_J1 = speedControl(speed, 64, reduction)
    position_J1 = positionControl_J1(J1)

    acc_J2 = accelerationControl(acc)
    speed_J2 = speedControl(speed, 64, reduction)
    position_J2 = positionControl_J2(J2)

    final_Position_J1 = 0
    final_Position_J2 = 0

    Send_Command.UART_sendCommand(1, speed_J1, acc_J1, position_J1)
    time.sleep(0.1)  # Small delay
    Send_Command.UART_sendCommand(2, speed_J2, acc_J2, position_J2)

    return acc_J1, speed_J1, position_J1, acc_J2, speed_J2, position_J2, final_Position_J1, final_Position_J2


def accelerationControl(desired_acc_rad):
    # using rad/s^2 as the unit of angular acceleration
    # the motor driver requires angular acceleration as a analog value from 0-255
    # conversion required

    desired_acc_analog = 0

    desired_acc_analog = 256 - (2 * math.pi) / 60 / (50 * 1e-6 * desired_acc_rad)
    print(f"desired acc rad = {desired_acc_rad}, desired acc analog calculated, value = {desired_acc_analog}")

    return desired_acc_analog


def speedControl(desired_actual_speed, microstepping, reduction_ratio):
    # the speed of the motor is in RPM, however, based on the micro-stepping settings, the actual speed may vary
    # when the micro-stepping value is 16/32/64, actual speed = set speed
    # when the micro-stepping value is other values, actual speed = set speed / 16

    # due to the implementation of belt-driven transmission, reduction_ration exists on some drivetrains
    # when reduction applies, actual speed = set speed / reduction ratio
    # note reduction ratio can be 1, which makes no difference to the set speed

    set_speed = 0

    if microstepping not in [16, 32, 64]:
        set_speed = desired_actual_speed * microstepping / 16 * reduction_ratio

    else:
        set_speed = desired_actual_speed * reduction_ratio

    print(f"set speed = {desired_actual_speed} * {reduction_ratio} = {set_speed}")

    return set_speed


# Functions to convert desired motor positions from angles to encoder codes The encoder's single turn value ranges
# from 0 to 0x4000 (16384 in decimal), meaning the encoder has 16384 slots per revolution. For motors J1 and J2,
# the reduction ratio is 1:3, so the motor must travel 16384 * 3 encoder slots to complete one revolution. Note:
# 16384 = 2^14, as the encoder is a 14-bit encoder.

# Accordingly, the relationship is:
# 0x4000 -> 16384 encoder slots -> 360/3 = 120 degrees (reduction ratio 1:3)
# For any desired travel degrees of the motor, the corresponding encoder slot value is:
# slot_value = (16384 / 120) * theta
# This value must be converted into hexadecimal.

# The conversion due to reduction ratio only required on J1 and J2. J3 and J4 don't need it due to no reduction.

# Variable: setEncoderValue_Jx will be the value transmitted to the edge controller.
# Variable: desired_position_J1 is the desired final coordinate (in degrees) of the motor after one motion.


def positionControl_J1(desired_position_J1):  # arm1

    setEncoderValue_J1 = round(desired_position_J1 * (16384 / 120))

    return setEncoderValue_J1


def positionControl_J2(desired_position_J2):  # arm2

    setEncoderValue_J2 = round(desired_position_J2 * (16384 / 120))

    return setEncoderValue_J2


def positionControl_J3(desired_position_J3):  # vertical actuator

    setEncoderValue_J3 = round(desired_position_J3 * (16384 / 360))

    return setEncoderValue_J3


def positionControl_J4(desired_position_J4):  # rotational actuator

    setEncoderValue_J4 = round(desired_position_J4 * (16384 / 360))

    return setEncoderValue_J4
