import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import QTimer, Qt
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
        self.remove_last_point_button.clicked.connect(self.grid_view.remove_last_point)
        
        self.remove_polygon_button = QPushButton('Remove Polygon')
        self.remove_polygon_button.clicked.connect(self.grid_view.remove_polygon)
        
        # Add "Finish Polygon" button
        self.finish_button = QPushButton('Finish Polygon')
        self.finish_button.clicked.connect(self.finish_polygon)
        
        # Add "Calculate Intersection" button (singular, to reflect single intersection)
        self.intersect_button = QPushButton('Calculate Intersection')
        self.intersect_button.clicked.connect(self.grid_view.calculate_intersection)
        
        # Add help button
        self.help_button = QPushButton('Help')
        self.help_button.clicked.connect(self.show_help)
        
        # Add widgets to controls layout
        self.controls_layout.addWidget(self.inputX)
        self.controls_layout.addWidget(self.inputY)
        self.controls_layout.addWidget(self.add_button)
        self.controls_layout.addWidget(self.find_button)
        self.controls_layout.addWidget(self.remove_last_point_button)
        self.controls_layout.addWidget(self.remove_polygon_button)
        self.controls_layout.addWidget(self.finish_button)
        self.controls_layout.addWidget(self.intersect_button)
        self.controls_layout.addWidget(self.help_button)
        
        # Add controls panel to main layout
        self.main_layout.addWidget(self.controls_panel)
        
        # Set the central widget
        self.setCentralWidget(self.central_widget)
        
        # Create toast label for messages
        self.toast_label = QLabel(self.central_widget)
        self.toast_label.setStyleSheet("background-color: #333; color: white; padding: 10px; border-radius: 5px;")
        self.toast_label.setAlignment(Qt.AlignCenter)
        self.toast_label.setFixedSize(400, 50)
        self.toast_label.move((self.width() - 400) // 2, self.height() - 60)
        self.toast_label.hide()
        
        # Connect GridView's invalid_action signal to show_toast
        self.grid_view.invalid_action.connect(self.show_toast)
    
    def resizeEvent(self, event):
        """Reposition toast label on resize"""
        super().resizeEvent(event)
        self.toast_label.move((self.width() - 400) // 2, self.height() - 60)
    
    def show_toast(self, message, duration=2000):
        """Show a toast message"""
        self.toast_label.setText(message)
        self.toast_label.show()
        QTimer.singleShot(duration, self.toast_label.hide)
    
    def add_point(self):
        try:
            x = float(self.inputX.text())
            y = float(self.inputY.text())
            result = self.grid_view.add_polygon_point(x, -y)
            if not result:
                # If add_polygon_point returns False, an invalid point was selected
                pass  # The toast will be shown via signal
            self.inputX.clear()
            self.inputY.clear()
        except ValueError:
            # Show error if inputs are not valid numbers
            self.show_toast("Invalid Input: Please enter valid numerical coordinates.")
    
    def find_point(self):
        try:
            x = float(self.inputX.text())
            y = float(self.inputY.text())
            self.grid_view.center_on_point(x, y)
        except ValueError:
            self.show_toast("Invalid Input: Please enter valid numerical coordinates.")
    
    def finish_polygon(self):
        """Call GridView's finalize_polygon method"""
        self.grid_view.finalize_polygon()
    
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
  <li>"Remove Polygon" clears all points or the last completed polygon</li>
  <li>"Finish Polygon" finalizes the current polygon (must have at least 3 points and be closed)</li>
  <li>"Calculate Intersection" computes and displays the common intersection of all completed polygons</li>
</ul>
"""
        QMessageBox.information(self, "Help", help_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())