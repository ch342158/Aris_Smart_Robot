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

        ################### Initialize UART ###################
        self.comport_open = False
        self.comport = 3
        self.comport_open = Send_Command.UART_Init(self.comport)
        self.ui.manual_COM_open.clicked.connect(self.COM_open)

        ################### Set default microstepping to 64 ###################
        self.ui.microStep_64.setChecked(True)

        ################### Select Control Mode ###################
        self.current_tab_mode = self.ui.tabWidget.currentIndex()
        self.ui.tabWidget.currentChanged.connect(self.on_tab_changed)

        ################### Go Home Button ###################
        self.ui.inv_gohome.clicked.connect(self.go_home_inverse)

        ################### Inverse Kinematics ###################
        self.ui.inv_solve_pb.clicked.connect(self.inv_getAnglesNPlot)
        self.ui.inv_run_pb.clicked.connect(self.run)
        #self.ui.desired_speed_slider.setRange(30, 1000)
        #self.ui.desired_acc_slider.setRange(1, 2000)
        #self.ui.desired_speed_adjust.setRange(30, 1000)
        #self.ui.desired_acc_adjust.setRange(10, 2000)
        #self.ui.desired_speed_slider.valueChanged.connect(self.ui.desired_speed_adjust.setValue)
        #self.ui.desired_acc_slider.valueChanged.connect(self.ui.desired_acc_adjust.setValue)

        self.setup_slider_spinbox(self.ui.desired_speed_slider, self.ui.desired_speed_adjust, 30, 1000, 500)
        self.setup_slider_spinbox(self.ui.desired_acc_slider, self.ui.desired_acc_adjust, 10, 2000, 1000)

        ################### Direct Kinematics ###################
        self.ui.dir_check_pb.clicked.connect(self.dir_getCoordinateNPlot)
        self.setup_joint_controls()

        # Set up programmed controls
        self.setup_programmed_controls()



    def setup_joint_controls(self):
        dir_ranges = [
            [-60, 240], [-120, 120], [-180, 180], [-180, 180]
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

    def inv_getAnglesNPlot(self):
        try:
            desiredX = float(self.ui.desired_x.text())
            desiredY = float(self.ui.desired_y.text())
            result = inverse_kinematics(desiredX, desiredY, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)
            if result:
                self.update_theta_ui(result['theta1'], result['theta2'])
                self.ui.solvability_check.setText('Solvability: OK')
                self.plot_robot(result)
            else:
                self.ui.solvability_check.setText('Solvability: Unsolvable')
                QMessageBox.warning(self, "Warning", "The point is outside the reach of the robot.")
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Invalid input. Please enter numeric values for coordinates.")

    def dir_getCoordinateNPlot(self):
        desiredAngles = [
            radians(self.ui.j1_dir_theta.value()),
            radians(self.ui.j2_dir_theta.value()),
            radians(self.ui.j3_dir_theta.value()),
            radians(self.ui.j4_dir_theta.value())
        ]
        result = direct_kinematics(*desiredAngles, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)
        self.ui.result_x.setText(str(result['tool_x']))
        self.ui.result_y.setText(str(result['tool_y']))
        self.plot_robot(result)

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
            2: self.handle_manual_tab,
            3: self.handle_programmed_tab,
            4: self.handle_guided_tab
        }

        if self.current_tab_mode in tab_handlers:
            tab_handlers[self.current_tab_mode](desired_speed, desired_acc, desired_microStep)

    def handle_inverse_tab(self, desired_speed, desired_acc, desired_microStep):
        try:
            desiredAngle_J1 = float(self.ui.j1_inv_theta.text())
            desiredAngle_J2 = float(self.ui.j2_inv_theta.text())
        except ValueError:
            QMessageBox.warning(self, 'Warning', 'Please use Solving first for J1 and J2')
            return

        Motor_Control.motionActuate(desired_speed, desired_acc, desired_microStep, 3,
                                    desiredAngle_J1, desiredAngle_J2, 0, 0)

    def handle_direct_tab(self, desired_speed, desired_acc, desired_microStep):
        angles = [self.ui.j1_dir_theta.value(), self.ui.j2_dir_theta.value(),
                  self.ui.j3_dir_theta.value(), self.ui.j4_dir_theta.value()]
        Motor_Control.motionActuate(desired_speed, desired_acc, desired_microStep, 3, *angles)

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

    def update_theta_ui(self, theta1, theta2):
        self.ui.j1_inv_theta.setText(str(theta1))
        self.ui.j2_inv_theta.setText(str(theta2))

    def go_home_inverse(self):
        self.ui.desired_x.setText("0")
        self.ui.desired_y.setText("390")
        self.inv_getAnglesNPlot()

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
                x_coord = float(self.ui.programmed_table.item(row, 4).text())
                y_coord = float(self.ui.programmed_table.item(row, 5).text())
                z_coord = float(self.ui.programmed_table.item(row, 6).text())

                # Store each action as a dictionary
                actions.append({
                    "j1_angle": j1_angle,
                    "j2_angle": j2_angle,
                    "j3_angle": j3_angle,
                    "j4_angle": j4_angle,
                    "x_coord": x_coord,
                    "y_coord": y_coord,
                    "z_coord": z_coord
                })
            except (ValueError, AttributeError):
                QMessageBox.warning(self, "Input Error",
                                    f"Invalid input at row {row + 1}. Please enter numeric values.")
                return

        # Perform each action sequentially
        for action in actions:
            self.perform_action(action)

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
        Motor_Control.motionActuate(
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
if __name__ == '__main__':
    app = QApplication([])
    ARIS_SMART_UI = MainUI()
    ARIS_SMART_UI.ui.show()
    app.exec()
