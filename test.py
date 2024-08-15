import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import QSize

class CustomButtonDemo(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Custom Push Button Demo')
        self.setGeometry(100, 100, 300, 200)

        # Create a QPushButton
        button = QPushButton('ON', self)
        button.setFixedSize(100, 100)  # Set the size of the button

        # Apply a stylesheet to make the button look like the image
        button.setStyleSheet("""
            QPushButton {
                background-color: #00C851;
                border-radius: 50px;  /* Circular shape */
                color: white;
                font-size: 20px;
                font-weight: bold;
                border: 5px solid #888;
            }
            QPushButton:pressed {
                background-color: #007E33;
            }
        """)

        # Set up the layout and central widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(button)
        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = CustomButtonDemo()
    demo.show()
    sys.exit(app.exec())
