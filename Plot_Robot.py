from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(PlotCanvas, self).__init__(fig)
        self.setParent(parent)

        # Set fixed limits for the plot to keep the origin centered
        self.fixed_limit = 450  # Set the fixed limit for both x and y
        self.axes.set_xlim(- self.fixed_limit,  self.fixed_limit)
        self.axes.set_ylim(- self.fixed_limit,  self.fixed_limit)

    def reset_limits(self):
        """Ensure the plot always maintains fixed limits."""
        self.axes.set_xlim(-self.fixed_limit, self.fixed_limit)
        self.axes.set_ylim(-self.fixed_limit, self.fixed_limit)

    def plot_scara_robot(self, elbow_x, elbow_y, tool_x, tool_y, RT_x, RT_y, LT_x, LT_y, RB_x, RB_y, LB_x, LB_y):
        ax = self.axes
        ax.clear()

        # Draw the arms
        ax.plot([0, elbow_x], [0, elbow_y], 'ko-')  # Base to elbow
        ax.plot([elbow_x, tool_x], [elbow_y, tool_y], 'ro-')  # Elbow to tool end

        # Draw the elbow arm boarders
        ax.plot([RB_x, RT_x], [RB_y, RT_y], 'go-')  # right bottom point to right top point
        ax.plot([LB_x, LT_x], [LB_y, LT_y], 'go-')  # left bottom point to left top point

        ax.plot([RB_x, LB_x], [RB_y, LB_y], 'go-')  # right bottom point to left bottom point
        ax.plot([RT_x, LT_x], [RT_y, LT_y], 'go-')  # right top point to left top point

        # Marking the joint points
        ax.plot(0, 0, 'ko', label='Base')
        ax.plot(elbow_x, elbow_y, 'ko', label=f'Elbow Joint ({elbow_x:.2f}, {elbow_y:.2f})')  # point out the arm1 end
        ax.plot(tool_x, tool_y, 'ro', label=f'Tool End ({tool_x:.2f}, {tool_y:.2f})')  # point out the tool end

        # Marking the border points
        ax.plot(RT_x, RT_y, 'ro')
        ax.plot(LT_x, LT_y, 'ro')

        ax.plot(RB_x, RB_y, 'ro')
        ax.plot(LB_x, LB_y, 'ro')

        # Drawing bold axes through the origin
        ax.axhline(0, color='black', linewidth=2)  # Horizontal line (x-axis)
        ax.axvline(0, color='black', linewidth=2)  # Vertical line (y-axis)

        # Drawing the robot base and holding arm
        ax.plot([-60, 60], [-150, -150], 'b-', linewidth=3)  # Base edge
        ax.plot([-60, -60], [-150, -30], 'b-', linewidth=3)  # Left side of the base
        ax.plot([60, 60], [-150, -30], 'b-', linewidth=3)  # Right side of the base
        ax.plot([-60, 60], [-30, -30], 'b-', linewidth=3)  # Top side of the base

        ax.plot([-33, 33], [-30, -30], 'g-', linewidth=3)  # Bottom side of the holding arm
        ax.plot([-33, -33], [-30, 0], 'g-', linewidth=3)  # Left side of the holding arm
        ax.plot([33, 33], [-30, 0], 'g-', linewidth=3)  # Right side of the holding arm
        ax.plot([-33, 33], [0, 0], 'g-', linewidth=3)  # Top side of the holding arm

        # Setting labels and grid
        ax.set_xlabel('X coordinate')
        ax.set_ylabel('Y coordinate')
        ax.legend()
        ax.grid(True)
        ax.axis('equal')  # Ensures that distances in X and Y are represented equally

        ax.set_title('SCARA Robot Arm Position with Base and Holding Arm')

        self.reset_limits()

        self.draw()
