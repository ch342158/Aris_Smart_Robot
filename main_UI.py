from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QVBoxLayout, QFrame
from math import radians

import Send_Command
from Inverse_Calc import inverse_kinematics
from Direct_Calc import direct_kinematics
from Plot_Robot import PlotCanvas
import Motor_Control

ARM1_LENGTH = 120  # Constants for the robot's arms
ARM2_LENGTH = 270
A1_WIDTH = 65

class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('ARIS_SMART.ui', self)

        ################################ Main page function implementations ################################

        #################For Plotting the Robot#################
        # Initialize plot canvas and add it to the plot widget
        self.canvas = PlotCanvas(self.ui.plot_widget)

        # Ensure plot_widget has a layout
        layout = self.ui.plot_widget.layout()
        if layout is None:
            layout = QVBoxLayout(self.ui.plot_widget)
            self.ui.plot_widget.setLayout(layout)

        layout.addWidget(self.canvas)

        #################Initialize UART#################

        self.comport_open = False
        self.comport = 3
        self.comport_open = Send_Command.UART_Init(self.comport)
        self.ui.manual_COM_open.clicked.connect(self.COM_open)

        #################set the microstepping choice to be 64 by default#################
        self.ui.microStep_64.setChecked(True)

        #################Select Control Mode#################
        # Initialize by getting the current tab mode
        self.current_tab_mode = self.ui.tabWidget.currentIndex()

        # Connect the currentChanged signal to a slot (function)
        self.ui.tabWidget.currentChanged.connect(self.on_tab_changed)

        # Define the function to handle the tab change

        #################Go Home#################
        self.ui.inv_gohome.clicked.connect(self.go_home_inverse)

        #################INVERSE KINEMATICS#################

        # Connect the button click event to the function
        self.ui.inv_solve_pb.clicked.connect(self.inv_getAnglesNPlot)
        self.ui.inv_run_pb.clicked.connect(self.run)

        # Configure the inputs
        self.ui.desired_speed_slider.setRange(30, 1000)
        self.ui.desired_acc_slider.setRange(1, 2000)

        self.ui.desired_speed_adjust.setRange(30, 1000)
        self.ui.desired_acc_adjust.setRange(10, 2000)

        self.ui.desired_speed_slider.valueChanged.connect(self.ui.desired_speed_adjust.setValue)
        self.ui.desired_acc_slider.valueChanged.connect(self.ui.desired_acc_adjust.setValue)

        #################DIRECT KINEMATICS#################

        self.ui.dir_check_pb.clicked.connect(self.dir_getCoordinateNPlot)

        # Define your ranges
        dir_ranges = [
            [-60, 240],
            [-120, 120],
            [-180, 180],
            [-180, 180]
        ]

        # Corresponding sliders and spin boxes
        theta_sliders = [
            self.ui.j1_theta_slider,
            self.ui.j2_theta_slider,
            self.ui.j3_theta_slider,
            self.ui.j4_theta_slider
        ]

        dir_theta_spinboxes = [
            self.ui.j1_dir_theta,
            self.ui.j2_dir_theta,
            self.ui.j3_dir_theta,
            self.ui.j4_dir_theta
        ]

        # Set ranges, initial positions, and connect sliders to spin boxes
        for i in range(4):
            min_val, max_val = dir_ranges[i]
            midpoint = (min_val + max_val) // 2

            theta_sliders[i].setRange(min_val, max_val)
            dir_theta_spinboxes[i].setRange(min_val, max_val)

            theta_sliders[i].setValue(midpoint)  # Set slider to midpoint
            dir_theta_spinboxes[i].setValue(midpoint)  # Set spin box to midpoint

            # Link slider to spin box
            theta_sliders[i].valueChanged.connect(dir_theta_spinboxes[i].setValue)

            # Link spin box to slider, casting float to int
            dir_theta_spinboxes[i].valueChanged.connect(
                lambda value, slider=theta_sliders[i]: slider.setValue(int(value)))

    def inv_getAnglesNPlot(self):
        try:
            desiredX = float(self.ui.desired_x.text())
            desiredY = float(self.ui.desired_y.text())
            result = inverse_kinematics(desiredX, desiredY, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)
            if result:
                print("Theta1 =", result['theta1'])
                self.ui.j1_inv_theta.setText(str(result['theta1']))
                print("Theta2 =", result['theta2'])
                self.ui.j2_inv_theta.setText(str(result['theta2']))
                print("Elbow position: (", result['elbow_x'], ",", result['elbow_y'], ")")
                print("Tool position: (", result['tool_x'], ",", result['tool_y'], ")")
                print("Border points:", result['border_points'])
                self.ui.solvability_check.setText('Solvability: OK')

                # Plot the SCARA robot
                self.canvas.plot_scara_robot(
                    result['elbow_x'], result['elbow_y'],
                    result['tool_x'], result['tool_y'],
                    *result['border_points']
                )
            else:
                print("The point is outside the reach of the robot.")
                self.ui.solvability_check.setText('Solvability: Unsolvable')
                QMessageBox.warning(self, "Warning", "The point is outside the reach of the robot.")
        except ValueError:
            print("Invalid input. Please enter numeric values for coordinates.")
            QMessageBox.warning(self, "Input Error", "Invalid input. Please enter numeric values for coordinates.")

        return

    def dir_getCoordinateNPlot(self):
        desiredAngle_J1 = self.ui.j1_dir_theta.value()
        desiredAngle_J2 = self.ui.j2_dir_theta.value()
        desiredAngle_J3 = self.ui.j3_dir_theta.value()
        desiredAngle_J4 = self.ui.j4_dir_theta.value()
        result = direct_kinematics(radians(desiredAngle_J1), radians(desiredAngle_J2), ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)

        self.ui.result_x.setText(str(result['tool_x']))
        self.ui.result_y.setText(str(result['tool_y']))
        # self.ui.result_x.setText(str(result[]))
        # self.ui.result_x.setText(str(result[]))

        self.canvas.plot_scara_robot(
            result['elbow_x'], result['elbow_y'],
            result['tool_x'], result['tool_y'],
            *result['border_points']
        )

    def run(self):
        if self.comport_open == True:
            print(self.current_tab_mode)
            # initialization
            desired_speed = 0
            desired_acc = 0
            desiredAngle_J1 = 0
            desiredAngle_J2 = 0
            desiredAngle_J3 = 0
            desiredAngle_J4 = 0
            desired_microStep = 0
            desired_reduction = 3

            desired_speed = self.ui.desired_speed_adjust.value()
            desired_acc = self.ui.desired_acc_adjust.value()
            print(f"desired acc from the slider is {desired_acc}")

            if self.ui.microStep_32.isChecked():
                desired_microStep = 32
            elif self.ui.microStep_64.isChecked():
                desired_microStep = 64
            elif self.ui.microStep_128.isChecked():
                desired_microStep = 128
            elif self.ui.microStep_256.isChecked():
                desired_microStep = 256

            if self.current_tab_mode == 0:

                print("Inverse Kinematics Control")

                # Check if the j1_theta QLineEdit is empty
                if self.ui.j1_inv_theta.text():
                    desiredAngle_J1 = float(self.ui.j1_inv_theta.text())
                else:
                    QMessageBox.warning(self, 'Warning', 'Please use Solving first for J1')
                    return  # Exit the function if the first input is empty

                # Check if the j2_theta QLineEdit is empty
                if self.ui.j2_inv_theta.text():
                    desiredAngle_J2 = float(self.ui.j2_inv_theta.text())
                else:
                    QMessageBox.warning(self, 'Warning', 'Please use Solving first for J2')
                    return  # Exit the function if the second input is empty

                # # Check if the j3_theta QLineEdit is empty
                # if self.ui.j3_theta.text():
                #     desiredAngle_J3 = float(self.ui.j3_inv_theta.text())
                # else:
                #     QMessageBox.warning(self, 'Warning', 'Please use Solving first for J3')
                #     return  # Exit the function if the second input is empty
                #
                # # Check if the j4_theta QLineEdit is empty
                # if self.ui.j4_theta.text():
                #     desiredAngle_J4 = float(self.ui.j4_inv_theta.text())
                # else:
                #     QMessageBox.warning(self, 'Warning', 'Please use Solving first for J4')ch
                #     return  # Exit the function if the second input is empty
            elif self.current_tab_mode == 1:

                print("Direct Kinematics Control")

                desiredAngle_J1 = self.ui.j1_dir_theta.value()
                desiredAngle_J2 = self.ui.j2_dir_theta.value()
                desiredAngle_J3 = self.ui.j3_dir_theta.value()
                desiredAngle_J4 = self.ui.j4_dir_theta.value()

                self.dir_getCoordinateNPlot()

            elif self.current_tab_mode == 2:

                print("Manual Control")
                pass

            elif self.current_tab_mode == 3:

                print("Programmed Control")
                pass

            elif self.current_tab_mode == 4:

                print("Guided Control")
                pass

            Motor_Control.motionActuate(desired_speed, desired_acc, desired_microStep, desired_reduction,
                                        desiredAngle_J1, desiredAngle_J2, desiredAngle_J3, desiredAngle_J4)

            # self.ui.motor_angle_1.setText(f"{str(round(final_position_J1_degree, 2))}\u00B0")
            # self.ui.motor_status_1.setText('RUN OK')
            # self.ui.motor_status_1.setStyleSheet('color: green;')

        else:
            # Show the error message using QMessageBox to tell that comport is not open
            self.show_message_box("USB Port is not OPEN!", "Serial Port Error")

    def on_tab_changed(self, new_tab_mode):
        # Update the current_tab_mode to the new tab index
        tab_modes = ["inverse", "direct", "manual", "programmed", "guided"]
        self.current_tab_mode = new_tab_mode
        print(f"Tab changed to index: {self.current_tab_mode} {tab_modes[self.current_tab_mode]}")

    def COM_open(self):
        # Allow the user to select and open the COM port manually
        comport = int(self.ui.comport_enter.text())
        self.comport_open = Send_Command.UART_Init(comport)

    def show_message_box(self, text, title):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(text)
        msg_box.setWindowTitle(title)
        msg_box.exec()

    def go_home_inverse(self):
        self.ui.desired_x.setText("0")
        self.ui.desired_y.setText("390")
        self.ui.desired_z.setText("0")
        self.ui.desired_rotation.setText("0")

        self.inv_getAnglesNPlot()
    # def go_home_direct(self):
    #     self.ui.j1_dir_theta.setValue

if __name__ == '__main__':
    app = QApplication([])
    ARIS_SMART_UI = MainUI()
    ARIS_SMART_UI.ui.show()

    app.exec()
