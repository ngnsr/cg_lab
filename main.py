import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QMessageBox
)
from grid import GridView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Interactive Grid Viewer")
        self.resize(800, 600)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create grid view
        self.grid_view = GridView(self)
        self.main_layout.addWidget(self.grid_view)
        
        # Create controls panel
        self.controls_panel = QWidget()
        self.controls_layout = QHBoxLayout(self.controls_panel)
        
        # Create input fields for coordinates
        self.inputX = QLineEdit()
        self.inputX.setPlaceholderText('x')
        self.inputY = QLineEdit()
        self.inputY.setPlaceholderText('y')
        
        # Create buttons for point and polygon manipulation
        self.add_button = QPushButton('Add Point')
        self.add_button.clicked.connect(self.add_point)
        
        self.find_button = QPushButton('Find Point')
        self.find_button.clicked.connect(self.find_point)
        
        self.remove_last_point_button = QPushButton('Remove Last Point')
        self.remove_last_point_button.clicked.connect(self.remove_last_point)
        
        self.remove_polygon_button = QPushButton('Remove Polygon')
        self.remove_polygon_button.clicked.connect(self.remove_polygon)
        
        # Add widgets to controls layout
        self.controls_layout.addWidget(self.inputX)
        self.controls_layout.addWidget(self.inputY)
        self.controls_layout.addWidget(self.add_button)
        self.controls_layout.addWidget(self.find_button)
        self.controls_layout.addWidget(self.remove_last_point_button)
        self.controls_layout.addWidget(self.remove_polygon_button)
        
        # Add controls panel to main layout
        self.main_layout.addWidget(self.controls_panel)
        
        # Add help button
        self.help_button = QPushButton('Help')
        self.help_button.clicked.connect(self.show_help)
        self.controls_layout.addWidget(self.help_button)
        
        # Set the central widget
        self.setCentralWidget(self.central_widget)
    
    def add_point(self):
        try:
            x = float(self.inputX.text())
            y = float(self.inputY.text())
            self.grid_view.add_polygon_point(x, y)
            self.inputX.clear()
            self.inputY.clear()
        except ValueError:
            # Show error if inputs are not valid numbers
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numerical coordinates.")
    
    def find_point(self):
        try:
            x = float(self.inputX.text())
            y = float(self.inputY.text())
            self.grid_view.center_on_point(x, y)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numerical coordinates.")
    
    def remove_last_point(self):
        self.grid_view.remove_last_point()
    
    def remove_polygon(self):
        self.grid_view.remove_polygon()
    
    def show_help(self):
        help_text = """
<h3>Interactive Grid Viewer Help</h3>
<p><b>Navigation:</b></p>
<ul>
  <li>Right-click and drag to pan the view</li>
  <li>Mouse wheel to zoom in/out</li>
  <li>Left-click on a grid point to select it (green dot shows nearest grid point)</li>
</ul>
<p><b>Point Management:</b></p>
<ul>
  <li>Enter x, y coordinates and click "Add Point" to add a point to the polygon</li>
  <li>"Find Point" centers the view on the specified coordinates</li>
  <li>"Remove Last Point" deletes the last added point</li>
  <li>"Remove Polygon" clears all points</li>
</ul>
"""
        QMessageBox.information(self, "Help", help_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())