from PyQt6 import uic
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QVBoxLayout
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
        self.ui.run_pb.clicked.connect(self.run)
        #self.ui.desired_speed_slider.setRange(30, 1000)
        #self.ui.desired_acc_slider.setRange(1, 2000)
        #self.ui.desired_speed_adjust.setRange(30, 1000)
        #self.ui.desired_acc_adjust.setRange(10, 2000)
        #self.ui.desired_speed_slider.valueChanged.connect(self.ui.desired_speed_adjust.setValue)
        #self.ui.desired_acc_slider.valueChanged.connect(self.ui.desired_acc_adjust.setValue)

        self.setup_slider_spinbox(self.ui.desired_speed_slider, self.ui.desired_speed_adjust, 1, 10, 1)
        self.setup_slider_spinbox(self.ui.desired_acc_slider, self.ui.desired_acc_adjust, 10, 2000, 1000)

        ################### Direct Kinematics ###################
        self.ui.dir_check_pb.clicked.connect(self.dir_getCoordinateNPlot)
        self.setup_joint_controls()

        ################### Manual Control ###################
        # Timer for sending repeated commands during manual control
        self.manual_timer = QTimer()
        # self.manual_timer.timeout.connect(self.send_manual_command)
        self.current_joint = None  # Track which joint to move
        self.movement_direction = 0  # Track the direction (1 for positive, -1 for negative)

        self.move_increment = 0  # NOTE NOTE NOTE this is only for testing the program, will not use on motor control

        # Connect the buttons to press and release events
        self.ui.man_j1_minus.pressed.connect(lambda: self.start_manual_move("J1", 0))
        self.ui.man_j1_plus.pressed.connect(lambda: self.start_manual_move("J1", 1))
        self.ui.man_j2_minus.pressed.connect(lambda: self.start_manual_move("J2", 0))
        self.ui.man_j2_plus.pressed.connect(lambda: self.start_manual_move("J2", 1))
        self.ui.man_j3_minus.pressed.connect(lambda: self.start_manual_move("J3", 0))
        self.ui.man_j3_plus.pressed.connect(lambda: self.start_manual_move("J3", 1))
        self.ui.man_j4_minus.pressed.connect(lambda: self.start_manual_move("J4", 0))
        self.ui.man_j4_plus.pressed.connect(lambda: self.start_manual_move("J4", 1))

        # Button release events to stop movement
        self.ui.man_j1_minus.released.connect(self.stop_manual_move)
        self.ui.man_j1_plus.released.connect(self.stop_manual_move)
        self.ui.man_j2_minus.released.connect(self.stop_manual_move)
        self.ui.man_j2_plus.released.connect(self.stop_manual_move)
        self.ui.man_j3_minus.released.connect(self.stop_manual_move)
        self.ui.man_j3_plus.released.connect(self.stop_manual_move)
        self.ui.man_j4_minus.released.connect(self.stop_manual_move)
        self.ui.man_j4_plus.released.connect(self.stop_manual_move)

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
            #print(str("result: ")+str(result))
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
            # required for J3 and J4, do not remove
            # radians(self.ui.j3_dir_theta.value()),
            # radians(self.ui.j4_dir_theta.value())
        ]
        result = direct_kinematics(*desiredAngles, ARM1_LENGTH, ARM2_LENGTH, A1_WIDTH)  # will have 7 inputs in the
        # future for J3 and J4
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
        # NOTE NOTE　NOTE: Manual Control is not managed by RUN button and function, thus excluded from it
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
            # 3: self.handle_programmed_tab,
            # 4: self.handle_guided_tab
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

        Motor_Control.semiAuto_motionActuate(desired_speed, desired_acc, desired_microStep, 3,
                                             desiredAngle_J1, desiredAngle_J2, 0, 0)

    def handle_direct_tab(self, desired_speed, desired_acc, desired_microStep):
        angles = [self.ui.j1_dir_theta.value(), self.ui.j2_dir_theta.value(),
                  self.ui.j3_dir_theta.value(), self.ui.j4_dir_theta.value()]
        Motor_Control.semiAuto_motionActuate(desired_speed, desired_acc, desired_microStep, 3, *angles)

    # Define other tab handlers here (manual, programmed, guided)

    def handle_manual_tab(self):

        pass

    def on_tab_changed(self, new_tab_mode):
        self.current_tab_mode = new_tab_mode
        if self.current_tab_mode == 2:
            self.ui.run_pb.setEnabled(False)
        else:
            self.ui.run_pb.setEnabled(True)
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


if __name__ == '__main__':
    app = QApplication([])
    ARIS_SMART_UI = MainUI()
    ARIS_SMART_UI.ui.show()
    app.exec()
