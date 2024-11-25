import time

from PyQt6.QtCore import Qt
from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QVBoxLayout,QTableWidgetItem
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

        ################### For Plotting the Robot ###################
        # Initialize plot canvas and add it to the plot widget
        self.canvas = PlotCanvas(self.ui.plot_widget)

        # Ensure plot_widget has a layout
        layout = self.ui.plot_widget.layout() or QVBoxLayout(self.ui.plot_widget)
        self.ui.plot_widget.setLayout(layout)
        layout.addWidget(self.canvas)

        ################### Set Plot to Robot Home Position ###################
        self.inverseControl_goHome()
        self.directControl_goHome()

        ################### Initialize UART ###################
        self.comport_open = False
        self.comport = 6
        self.comport_open = Send_Command.UART_Init(self.comport)
        self.ui.manual_COM_open.clicked.connect(self.COM_open)

        ################### Set default microstepping to 64 ###################
        self.ui.microStep_64.setChecked(True)

        ################### Select Control Mode ###################
        self.current_tab_mode = self.ui.tabWidget.currentIndex()
        self.ui.tabWidget.currentChanged.connect(self.on_tab_changed)

        ################### Go Home Button ###################
        self.ui.inv_gohome.clicked.connect(self.inverseControl_goHome)
        self.ui.dir_gohome.clicked.connect(self.directControl_goHome)

        ################### Inverse Kinematics ###################
        # self.ui.inv_solve_pb.clicked.connect(self.inv_findAnglesNPlot)
        self.ui.run_pb.clicked.connect(self.run)

        # Connect X and Y fields to the inverse kinematics function
        self.ui.desired_x.textChanged.connect(self.inv_findAnglesNPlot)
        self.ui.desired_y.textChanged.connect(self.inv_findAnglesNPlot)
        self.ui.desired_z.textChanged.connect(self.inv_findAnglesNPlot)
        self.ui.desired_rotation.textChanged.connect(self.inv_findAnglesNPlot)


        self.setup_slider_spinbox(self.ui.desired_speed_slider, self.ui.desired_speed_adjust, 1, 50, 25)
        self.setup_slider_spinbox(self.ui.desired_acc_slider, self.ui.desired_acc_adjust, 10, 100, 25)

        ################### Direct Kinematics ###################
        # self.ui.dir_check_pb.clicked.connect(self.dir_findCoordinateNPlot)
        self.ui.j1_dir_theta.valueChanged.connect(self.dir_findCoordinateNPlot)
        self.ui.j2_dir_theta.valueChanged.connect(self.dir_findCoordinateNPlot)
        self.ui.j3_dir_theta.valueChanged.connect(self.dir_findCoordinateNPlot)
        self.ui.j4_dir_theta.valueChanged.connect(self.dir_findCoordinateNPlot)


        self.setup_joint_controls()

        # Set up programmed controls
        self.setup_programmed_controls()
        self.move_increment = 0  # NOTE NOTE NOTE this is only for testing the program, will not use on motor control

        # Connect the buttons to press and release events
        self.ui.man_j1_minus.pressed.connect(lambda: self.start_manual_move("J1", 1))
        self.ui.man_j1_plus.pressed.connect(lambda: self.start_manual_move("J1", 0))
        self.ui.man_j2_minus.pressed.connect(lambda: self.start_manual_move("J2", 1)) # direction for J2 is reversed due to the mechanical design, the motion of the motor is reversed by the belt gear
        self.ui.man_j2_plus.pressed.connect(lambda: self.start_manual_move("J2", 0))
        self.ui.man_j3_minus.pressed.connect(lambda: self.start_manual_move("J3", 1))
        self.ui.man_j3_plus.pressed.connect(lambda: self.start_manual_move("J3", 0))
        self.ui.man_j4_minus.pressed.connect(lambda: self.start_manual_move("J4", 1))
        self.ui.man_j4_plus.pressed.connect(lambda: self.start_manual_move("J4", 0))

        # Button release events to stop movement
        self.ui.man_j1_minus.released.connect(self.stop_manual_move)
        self.ui.man_j1_plus.released.connect(self.stop_manual_move)
        self.ui.man_j2_minus.released.connect(self.stop_manual_move)
        self.ui.man_j2_plus.released.connect(self.stop_manual_move)
        self.ui.man_j3_minus.released.connect(self.stop_manual_move)
        self.ui.man_j3_plus.released.connect(self.stop_manual_move)
        self.ui.man_j4_minus.released.connect(self.stop_manual_move)
        self.ui.man_j4_plus.released.connect(self.stop_manual_move)


    def setup_joint_controls(self):
        dir_ranges = [
            [-100, 100], [-90, 90], [-180, 180], [-180, 180]
        ]

        theta_sliders = [
            self.ui.j1_theta_slider, self.ui.j2_theta_slider,
            self.ui.j3_theta_slider, self.ui.j4_theta_slider
        ]

        dir_theta_spinboxes = [
            self.ui.j1_dir_theta, self.ui.j2_dir_theta,
            self.ui.j3_dir_theta, self.ui.j4_dir_theta
        ]

        for i, (slider, spinbox) in enumerate(zip(theta_sliders, dir_theta_spinboxes)):
            midpoint = (dir_ranges[i][0] + dir_ranges[i][1]) // 2
            self.setup_slider_spinbox(slider, spinbox, *dir_ranges[i], midpoint)

    def setup_slider_spinbox(self, slider, spinbox, min_val, max_val, initial_val):
        slider.setRange(min_val, max_val)
        spinbox.setRange(min_val, max_val)
        slider.setValue(initial_val)
        spinbox.setValue(initial_val)
        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(lambda value: slider.setValue(int(value)))

    # Legacy Version of this function
    # def inv_findAnglesNPlot(self):
    #     try:
    #         desiredX = float(self.ui.desired_x.text())
    #         desiredY = float(self.ui.desired_y.text())
    #         result = inverse_kinematics(desiredX, desiredY, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)
    #         if result:
    #             self.update_theta_ui(result['theta1'], result['theta2'])
    #             self.ui.solvability_check.setText('Solvability: OK')
    #             self.plot_robot(result)
    #         else:
    #             self.ui.solvability_check.setText('Solvability: Unsolvable')
    #             QMessageBox.warning(self, "Warning", "The point is outside the reach of the robot.")
    #     except ValueError:
    #         QMessageBox.warning(self, "Input Error", "Invalid input. Please enter numeric values for coordinates.")

    def inv_findAnglesNPlot(self):
        try:
            # Get values from the input fields
            desiredX = float(self.ui.desired_x.text())
            desiredY = float(self.ui.desired_y.text())
            desiredZ = float(self.ui.desired_z.text())
            desiredR = float(self.ui.desired_rotation.text())

            # Perform inverse kinematics calculation
            result = inverse_kinematics(desiredX, desiredY,desiredZ,desiredR, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)

            if result:
                # Update UI with calculated angles
                self.update_theta_ui(result['theta1'], result['theta2'], result['theta3'], result['theta4'])
                self.ui.solvability_check.setText('Reachability: Within Range')

                # Clear any previous warnings in input fields
                self.ui.desired_x.setStyleSheet("")
                self.ui.desired_y.setStyleSheet("")

                # Plot the robot
                self.plot_robot(result)
            else:
                # Display warning in the solvability line edit
                self.ui.solvability_check.setText('Reachability: Out of Range')

                # Highlight the fields with invalid values
                self.ui.desired_x.setStyleSheet("background-color: yellow;")
                self.ui.desired_y.setStyleSheet("background-color: yellow;")
        except ValueError:
            # Handle non-numeric input with a warning
            self.ui.solvability_check.setText('Invalid Input')
            self.ui.desired_x.setStyleSheet("background-color: red;")
            self.ui.desired_y.setStyleSheet("background-color: red;")

    # Legacy Version of this function
    # def dir_findCoordinateNPlot(self):
    #     desiredAngles = [
    #          radians(self.ui.j1_dir_theta.value()), # offsets to makeup the zero/home position for arm 1
    #         radians(self.ui.j2_dir_theta.value()),
    #         # radians(self.ui.j3_dir_theta.value()),
    #         # radians(self.ui.j4_dir_theta.value())
    #     ]
    #     result = direct_kinematics(*desiredAngles, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH) # will have 7 inputs in the
    #     self.ui.result_x.setText(str(result['tool_x']))
    #     self.ui.result_y.setText(str(result['tool_y']))
    #     self.plot_robot(result)

    def dir_findCoordinateNPlot(self):
        try:
            # Get values from the sliders/spin boxes
            j1_angle = radians(self.ui.j1_dir_theta.value())  # Convert degrees to radians
            j2_angle = radians(self.ui.j2_dir_theta.value())
            j3_angle = radians(self.ui.j3_dir_theta.value())
            j4_angle = radians(self.ui.j4_dir_theta.value())

            # Add other joints if needed, e.g., J3 and J4
            desiredAngles = [j1_angle, j2_angle, j3_angle, j4_angle]

            # Perform direct kinematics calculation
            result = direct_kinematics(*desiredAngles, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)

            # Update result field
            self.ui.result_x.setText(f"{result['tool_x']:.2f}")
            self.ui.result_y.setText(f"{result['tool_y']:.2f}")
            self.ui.result_z.setText(f"{result['tool_z']:.2f}")
            self.ui.result_rotation.setText(f"{result['tool_r']:.2f}")

            # Plot the robot
            self.plot_robot(result)
        except Exception as e:
            QMessageBox.warning(self, "Calculation Error", f"An error occurred: {e}")

    def plot_robot(self, result):
        self.canvas.plot_scara_robot(
            result['elbow_x'], result['elbow_y'],
            result['tool_x'], result['tool_y'],
            *result['border_points']
        )


    def run(self):
        if not self.comport_open:
            self.show_message_box("USB Port is not OPEN!", "Serial Port Error")
            return

        desired_speed = self.ui.desired_speed_adjust.value()
        desired_acc = self.ui.desired_acc_adjust.value()

        microstep_mapping = {
            self.ui.microStep_32: 32,
            self.ui.microStep_64: 64,
            self.ui.microStep_128: 128,
            self.ui.microStep_256: 256
        }
        desired_microStep = next(
            (step for checkbox, step in microstep_mapping.items() if checkbox.isChecked()), 64
        )

        tab_handlers = {
            0: self.handle_inverse_tab,
            1: self.handle_direct_tab,
            # 2: self.handle_manual_tab,
            # 3: self.handle_programmed_tab,
            # 4: self.handle_guided_tab
        }

        if self.current_tab_mode in tab_handlers:
            tab_handlers[self.current_tab_mode](desired_speed, desired_acc, desired_microStep)

    def handle_inverse_tab(self, desired_speed, desired_acc, desired_microStep):
        try:
            desiredAngle_J1 = float(self.ui.j1_inv_theta.text())
            desiredAngle_J2 = float(self.ui.j2_inv_theta.text())
            desiredAngle_J3 = float(self.ui.j3_inv_theta.text())
            desiredAngle_J4 = float(self.ui.j4_inv_theta.text())
        except ValueError:
            QMessageBox.warning(self, 'Warning', 'Please use Solving first for J1 and J2')
            return

        Motor_Control.semiAuto_motionActuate(desired_speed, desired_acc, desired_microStep, 3,
                                             desiredAngle_J1, desiredAngle_J2, desiredAngle_J3, desiredAngle_J4)

    def handle_direct_tab(self, desired_speed, desired_acc, desired_microStep):
        angles = [-self.ui.j1_dir_theta.value(), -self.ui.j2_dir_theta.value(),
                  self.ui.j3_dir_theta.value(), self.ui.j4_dir_theta.value()]
        Motor_Control.semiAuto_motionActuate(desired_speed, desired_acc, desired_microStep, 3, *angles)

    # Define other tab handlers here (manual, programmed, guided)

    def on_tab_changed(self, new_tab_mode):
        self.current_tab_mode = new_tab_mode
        print(f"Tab changed to: {self.current_tab_mode}")

    def COM_open(self):
        try:
            comport = int(self.ui.comport_enter.text())
            self.comport_open = Send_Command.UART_Init(comport)
            if not self.comport_open:
                raise IOError("Failed to open COM port.")
        except ValueError:
            self.show_message_box("Please enter a valid COM port number.", "Input Error")
        except IOError as e:
            self.show_message_box(str(e), "COM Port Error")

    def show_message_box(self, text, title):
        QMessageBox.warning(self, title, text)

    def update_theta_ui(self, theta1, theta2, theta3, theta4):
        self.ui.j1_inv_theta.setText(str(theta1))
        self.ui.j2_inv_theta.setText(str(theta2))
        self.ui.j3_inv_theta.setText(str(theta3))
        self.ui.j4_inv_theta.setText(str(theta4))

    def inverseControl_goHome(self):
        self.ui.desired_x.setText("0")
        self.ui.desired_y.setText("390")
        self.ui.desired_z.setText("0")
        self.ui.desired_rotation.setText("0")
        self.inv_findAnglesNPlot()

    def directControl_goHome(self):
        self.ui.j1_theta_slider.setValue(0)
        self.ui.j2_theta_slider.setValue(0)
        self.ui.j3_theta_slider.setValue(0)
        self.ui.j4_theta_slider.setValue(0)
        self.dir_findCoordinateNPlot()

    def setup_programmed_controls(self):
        # Connect add, remove, and execute buttons
        self.ui.add_action_button.clicked.connect(self.add_programmed_action)
        self.ui.remove_action_button.clicked.connect(self.remove_programmed_action)
        self.ui.execute_programmed_button.clicked.connect(self.execute_programmed_actions)

    def add_programmed_action(self):
        # Add a new row to the programmed action table
        row_position = self.ui.programmed_table.rowCount()
        self.ui.programmed_table.insertRow(row_position)

        # Initialize each cell in the new row with an empty QTableWidgetItem to allow editing
        for col in range(self.ui.programmed_table.columnCount()):
            item = QTableWidgetItem("")  # Create an empty table item
            # Set flags to make sure the item is editable
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
            self.ui.programmed_table.setItem(row_position, col, item)

    def remove_programmed_action(self):
        # Remove the selected row from the table
        current_row = self.ui.programmed_table.currentRow()
        if current_row >= 0:
            self.ui.programmed_table.removeRow(current_row)
        else:
            QMessageBox.warning(self, "Selection Error", "Please select a row to remove.")

    def execute_programmed_actions(self):
        actions = []

        # Iterate through the table rows to collect the action data
        for row in range(self.ui.programmed_table.rowCount()):
            try:
                # Extract joint angles and coordinates from the table
                j1_angle = float(self.ui.programmed_table.item(row, 0).text())
                j2_angle = float(self.ui.programmed_table.item(row, 1).text())
                j3_angle = float(self.ui.programmed_table.item(row, 2).text())
                j4_angle = float(self.ui.programmed_table.item(row, 3).text())
                #x_coord = float(self.ui.programmed_table.item(row, 4).text())
                #y_coord = float(self.ui.programmed_table.item(row, 5).text())
                #z_coord = float(self.ui.programmed_table.item(row, 6).text())

                # Store each action as a dictionary
                actions.append({
                    "j1_angle": j1_angle,
                    "j2_angle": j2_angle,
                    "j3_angle": j3_angle,
                    "j4_angle": j4_angle,
                    #"x_coord": x_coord,
                    #"y_coord": y_coord,
                    #"z_coord": z_coord
                })
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "Input Error",
                                    f"Invalid input at row {row + 1}. Please enter numeric values.")
                return

        # Perform each action sequentially
        for action in actions:
            #waiting for optimization, return message.
            self.perform_action(action)
            time.sleep(10)


    def perform_action(self, action):
        # Extract values from the action
        j1 = action["j1_angle"]
        j2 = action["j2_angle"]
        j3 = action["j3_angle"]
        j4 = action["j4_angle"]

        # Convert angles to radians if needed
        j1_rad = radians(j1)
        j2_rad = radians(j2)
        j3_rad = radians(j3)
        j4_rad = radians(j4)

        # Send commands to the robot
        Motor_Control.semiAuto_motionActuate(
            speed=500,  # Default speed value, can be customized
            acc=100,  # Default acceleration value, can be customized
            micro=64,  # Default microstepping
            reduction=3,
            J1=j1,
            J2=j2,
            J3=j3,
            J4=j4
        )

        # Update the plot with the new robot position (based on the direct kinematics result)
        result = direct_kinematics(j1_rad, j2_rad, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)
        self.plot_robot(result)

    def plot_robot(self, result):
        # Plot the SCARA robot's new position based on calculated coordinates
        self.canvas.plot_scara_robot(
            result['elbow_x'], result['elbow_y'],
            result['tool_x'], result['tool_y'],
            *result['border_points']
        )

    def start_manual_move(self, joint, direction):
        """Start continuous motion of the given joint in the specified direction."""
        self.current_joint = joint
        self.movement_direction = direction
        desired_speed = self.ui.desired_speed_adjust.value()
        desired_acc = self.ui.desired_acc_adjust.value()

        # Send command for continuous motion
        Motor_Control.fullManual_motionStart(desired_speed, desired_acc, 3, joint, direction)

    def stop_manual_move(self):
        """Stop continuous motion of the joint."""
        if self.current_joint:
            Motor_Control.fullManual_motionStop(self.current_joint)

        # Reset state
        self.current_joint = None
        self.movement_direction = 0

    # the following function implement the tick-by-tick control, which may not be the best but i would leave it here
    # for now i have discovered a better approach for manual control of one motor: the speed control mode,
    # which a command is sent to the motor to keep it moving, and can be stopped by another command.
    """def send_manual_command(self):
        #Send the move command for the relative movement (for now just print).
        desired_speed = self.ui.desired_speed_adjust.value()
        desired_acc = self.ui.desired_acc_adjust.value()
        if self.current_joint and self.movement_direction:  # Increment or decrement J1 position based on the movement direction
            Motor_Control.fullManual_motionActuate(desired_speed,desired_acc,3,self.current_joint,self.movement_direction*2)
"""
if __name__ == '__main__':
    app = QApplication([])
    ARIS_SMART_UI = MainUI()
    ARIS_SMART_UI.ui.show()
    app.exec()
