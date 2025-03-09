import sys
import math
from PySide6.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QLabel
from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QFont


class GridView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create scene with generous bounds
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(-10000, -10000, 20000, 20000)
        self.setScene(self.scene)
        
        # Remove scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Grid settings
        self.base_grid_size = 50
        self.scale_factor = 1.0
        self.zoom_factor = 1.2
        
        # Axis snapping threshold (in scene units)
        self.axis_snap_threshold = 0.1
        
        # Last mouse position for panning
        self.last_mouse_pos = QPoint()
        
        # Enable mouse tracking to get hover events
        self.setMouseTracking(True)
        
        # Rendering settings
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Visual settings
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
        
        # Create a QLabel for coordinates display (fixed size, not affected by zoom)
        self.coords_label = QLabel(self)
        self.coords_label.setFont(QFont("Arial", 12, QFont.Bold))
        self.coords_label.setStyleSheet("""
            background-color: rgba(40, 40, 40, 220); 
            color: white;
            padding: 8px; 
            border: 2px solid #555;
            border-radius: 4px;
        """)
        self.coords_label.move(10, self.height() - 40)
        self.coords_label.setText("Coordinates: (0.00, 0.00)")  # Initial text
        self.coords_label.adjustSize()
        self.coords_label.show()
        
        # Create a QLabel for grid size info display
        self.grid_info_label = QLabel(self)
        self.grid_info_label.setFont(QFont("Arial", 10))
        self.grid_info_label.setStyleSheet("""
            background-color: rgba(40, 40, 40, 200); 
            color: white;
            padding: 4px; 
            border: 1px solid #555;
            border-radius: 3px;
        """)
        self.grid_info_label.move(10, 10)
        self.grid_info_label.setText("Grid: 50.0px | Scale: 1.0000x")  # Initial text
        self.grid_info_label.adjustSize()
        self.grid_info_label.show()
        
        # Initial view
        self.centerOn(0, 0)
        
    def resizeEvent(self, event):
        """Handle resize events to reposition the labels"""
        super().resizeEvent(event)
        self.coords_label.move(10, self.height() - 50)
        self.grid_info_label.move(10, 10)
        
    def get_adaptive_grid_size(self):
        """Calculate the grid size based on current zoom level"""
        # Get the current transform scale
        transform = self.transform()
        current_scale = transform.m11()  # Get the horizontal scale factor
        
        # Base grid size for different zoom levels using powers of 10
        if current_scale <= 0.01:
            return 1000
        elif current_scale <= 0.1:
            return 100
        elif current_scale <= 1:
            return 50
        elif current_scale <= 10:
            return 10
        elif current_scale <= 100:
            return 1
        else:
            return 0.1  # Very fine grid for extreme zoom
        
    def drawBackground(self, painter, rect):
        """Custom background drawing to create the grid"""
        super().drawBackground(painter, rect)
        
        # Get the current transform scale
        transform = self.transform()
        current_scale = transform.m11()  # Get the horizontal scale factor
        
        # Calculate adaptive grid size based on zoom level
        effective_grid_size = self.get_adaptive_grid_size()
        
        # Get visible area in scene coordinates
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        
        # Calculate grid boundaries - ensure they align perfectly with the origin
        # Use math.floor and math.ceil to avoid floating point issues
        left = math.floor(visible_rect.left() / effective_grid_size) * effective_grid_size
        top = math.floor(visible_rect.top() / effective_grid_size) * effective_grid_size
        right = math.ceil(visible_rect.right() / effective_grid_size) * effective_grid_size
        bottom = math.ceil(visible_rect.bottom() / effective_grid_size) * effective_grid_size
        
        # Set up the grid pen with width that compensates for zoom
        pen_width = min(0.5 / current_scale, 0.5)  # Prevent lines from getting too thick at high zoom
        
        thin_pen = QPen(QColor(200, 200, 200))
        thin_pen.setWidthF(pen_width)
        
        thick_pen = QPen(QColor(120, 120, 120))
        thick_pen.setWidthF(pen_width * 2)
        
        # Fix for high zoom: ensure step is not smaller than machine precision
        if effective_grid_size < 0.00001:
            effective_grid_size = 0.00001
            
        # Create fixed step intervals to avoid floating point errors
        step = effective_grid_size
        
        # Draw horizontal grid lines
        y = top
        while y <= bottom:
            # Determine if this is a major grid line
            major_line = round(y / effective_grid_size) % 5 == 0
            
            if major_line:
                painter.setPen(thick_pen)
            else:
                painter.setPen(thin_pen)
                
            painter.drawLine(left, y, right, y)
            y += step
            
        # Draw vertical grid lines
        x = left
        while x <= right:
            # Determine if this is a major grid line
            major_line = round(x / effective_grid_size) % 5 == 0
            
            if major_line:
                painter.setPen(thick_pen)
            else:
                painter.setPen(thin_pen)
                
            painter.drawLine(x, top, x, bottom)
            x += step
            
        # Highlight the axes - drawn last to be on top
        axis_pen = QPen(QColor(0, 0, 0))
        axis_width = max(2 / current_scale, 0.5)  # Scale the axis width with zoom
        axis_pen.setWidthF(axis_width)
        painter.setPen(axis_pen)
        painter.drawLine(0, top, 0, bottom)  # Y-axis
        painter.drawLine(left, 0, right, 0)  # X-axis
        
        # Update the grid info label
        self.grid_info_label.setText(f"Grid: {effective_grid_size:.1f}px | Scale: {current_scale:.4f}x")
        self.grid_info_label.adjustSize()
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self.last_mouse_pos = event.globalPosition().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        # Map the mouse position to scene coordinates
        scene_pos = self.mapToScene(event.pos())
        
        # Update the current scale for proper snapping threshold
        current_scale = self.transform().m11()
        # Adjust the snap threshold based on the current zoom level
        adjusted_threshold = self.axis_snap_threshold / current_scale
        
        # Snap to axes when close enough
        if abs(scene_pos.x()) < adjusted_threshold:
            scene_pos.setX(0)
        if abs(scene_pos.y()) < adjusted_threshold:
            scene_pos.setY(0)
        
        # Round to 2 decimal places for display
        rounded_x = round(scene_pos.x(), 2)
        rounded_y = round(scene_pos.y(), 2)
        
        # Update the coordinate label (fixed size UI element)
        self.coords_label.setText(f"Coordinates: ({rounded_x}, {rounded_y})")
        self.coords_label.adjustSize()  # Adjust size to fit content
        
        # Handle right-button dragging for panning
        if event.buttons() & Qt.RightButton:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self.last_mouse_pos)
            self.last_mouse_pos = event.pos()
            
            # Move the scene in the direction opposite to mouse movement (for natural feel)
            self.translate(-delta.x(), -delta.y())
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.RightButton:
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
        
    def wheelEvent(self, event):
        """Handle wheel events for zooming"""
        # Limit zoom levels to prevent precision issues
        zoom_in = event.angleDelta().y() > 0
        
        if zoom_in:
            # Prevent extreme zoom in
            current_scale = self.transform().m11()
            if current_scale < 1000:  # Maximum zoom in limit
                self.scale_factor *= self.zoom_factor
                self.scale(self.zoom_factor, self.zoom_factor)
        else:
            # Prevent extreme zoom out
            current_scale = self.transform().m11()
            if current_scale > 0.001:  # Maximum zoom out limit
                self.scale_factor /= self.zoom_factor
                self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
            
        # Force update
        self.viewport().update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Interactive Grid Viewer")
        self.resize(800, 600)
        
        self.grid_view = GridView(self)
        self.setCentralWidget(self.grid_view)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())