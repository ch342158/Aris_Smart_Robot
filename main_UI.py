from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QVBoxLayout, QFrame
from Inverse_Calc import inverse_kinematics
from Plot_Robot import PlotCanvas
import Motor_Control


class MainUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = uic.loadUi('ARIS_SMART.ui',self)

        # Initialize plot canvas and add it to the plot widget
        self.canvas = PlotCanvas(self.ui.plot_widget)

        # Ensure plot_widget has a layout
        layout = self.ui.plot_widget.layout()
        if layout is None:
            layout = QVBoxLayout(self.ui.plot_widget)
            self.ui.plot_widget.setLayout(layout)

        layout.addWidget(self.canvas)

        # Main page function implementations
        # Connect the button click event to the function
        self.ui.inv_solve_pb.clicked.connect(self.getCoordinate)
        self.ui.inv_run_pb.clicked.connect(self.run)

        self.ui.desired_speed_slider.setRange(30, 1000)
        self.ui.desired_acc_slider.setRange(1, 2000)

        self.ui.desired_speed_adjust.setRange(30, 1000)
        self.ui.desired_acc_adjust.setRange(10, 2000)

        self.ui.desired_speed_slider.valueChanged.connect(self.ui.desired_speed_adjust.setValue)
        self.ui.desired_acc_slider.valueChanged.connect(self.ui.desired_acc_adjust.setValue)

        # set the microstepping choice to be 64 by default
        self.ui.microStep_64.setChecked(True)



    def getCoordinate(self):
        try:
            desiredX = float(self.ui.desired_x.text())
            desiredY = float(self.ui.desired_y.text())
            arm1_length = 120  # Constants for the robot's arms
            arm2_length = 270
            a1_width = 65
            result = inverse_kinematics(desiredX, desiredY, arm1_length, arm2_length, a1_width)
            if result:
                print("Theta1 =", result['theta1'])
                self.ui.j1_theta.setText(str(result['theta1']))
                print("Theta2 =", result['theta2'])
                self.ui.j2_theta.setText(str(result['theta2']))
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

    def run(self):

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

        # Check if the j1_theta QLineEdit is empty
        if self.ui.j1_theta.text():
            desiredAngle_J1 = float(self.ui.j1_theta.text())
        else:
            QMessageBox.warning(self, 'Warning', 'Please use Solving first for J1')
            return  # Exit the function if the first input is empty

        # Check if the j2_theta QLineEdit is empty
        if self.ui.j2_theta.text():
            desiredAngle_J2 = float(self.ui.j2_theta.text())
        else:
            QMessageBox.warning(self, 'Warning', 'Please use Solving first for J2')
            return  # Exit the function if the second input is empty

        # # Check if the j3_theta QLineEdit is empty
        # if self.ui.j3_theta.text():
        #     desiredAngle_J2 = float(self.ui.j2_theta.text())
        # else:
        #     QMessageBox.warning(self, 'Warning', 'Please use Solving first for J3')
        #     return  # Exit the function if the second input is empty
        #
        # # Check if the j4_theta QLineEdit is empty
        # if self.ui.j4_theta.text():
        #     desiredAngle_J2 = float(self.ui.j2_theta.text())
        # else:
        #     QMessageBox.warning(self, 'Warning', 'Please use Solving first for J4')
        #     return  # Exit the function if the second input is empty

        if self.ui.microStep_32.isChecked():
            desired_microStep = 32
        elif self.ui.microStep_64.isChecked():
            desired_microStep = 64
        elif self.ui.microStep_128.isChecked():
            desired_microStep = 128
        elif self.ui.microStep_256.isChecked():
            desired_microStep = 256

        print(Motor_Control.motionActuate(desired_speed, desired_acc, desired_microStep, desired_reduction,
                                          desiredAngle_J1, desiredAngle_J2, desiredAngle_J3, desiredAngle_J4))




if __name__ == '__main__':
    app = QApplication([])
    ARIS_SMART_UI = MainUI()
    ARIS_SMART_UI.ui.show()

    app.exec()
