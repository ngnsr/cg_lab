import sys
import math
from PySide6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QLabel
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPolygonF

from main_window import MainWindow

class GridView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Polygon management variables
        self.polygon_points = []  # List of QPointF for polygon vertices
        self.current_polygon = None  # Will be a QGraphicsPolygonItem
        self.point_items = []  # List to keep track of point markers
        self.completed_polygons = []
        
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
        
        # Nearest grid point variables
        self.nearest_grid_point = QPointF(0, 0)
        self.highlight_radius = 5  # Radius of the green highlight circle
        self.highlight_nearest = False  # Whether to show the highlight
        self.highlight_max_distance = 30  # Maximum pixel distance to show highlight

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
    
    def find_nearest_grid_point(self, scene_pos):
        """Find the nearest grid intersection point to the given scene position"""
        grid_size = self.get_adaptive_grid_size()
        
        # Calculate the nearest grid point
        grid_x = round(scene_pos.x() / grid_size) * grid_size
        grid_y = round(scene_pos.y() / grid_size) * grid_size
        
        return QPointF(grid_x, grid_y)
        
    def drawForeground(self, painter, rect):
        """Draw foreground elements including the green highlight dot"""
        super().drawForeground(painter, rect)
        
        # Draw the green highlight at the nearest grid point if enabled
        if self.highlight_nearest:
            # Get the current transform scale
            transform = self.transform()
            current_scale = transform.m11()
            
            # Scale the highlight size based on zoom level
            scaled_radius = self.highlight_radius / current_scale
            
            # Create a green pen for the highlight
            highlight_pen = QPen(QColor(0, 180, 0))
            highlight_pen.setWidthF(2 / current_scale)
            painter.setPen(highlight_pen)
            
            # Create a semi-transparent green brush
            highlight_brush = QBrush(QColor(0, 255, 0, 180))
            painter.setBrush(highlight_brush)
            
            # Draw the highlight circle
            painter.drawEllipse(self.nearest_grid_point, scaled_radius, scaled_radius)
        
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
        
        # Find the nearest grid point
        self.nearest_grid_point = self.find_nearest_grid_point(scene_pos)
        
        # Calculate distance to nearest grid point in pixels
        nearest_point_in_view = self.mapFromScene(self.nearest_grid_point)
        mouse_pos_in_view = event.pos()
        
        # Use Euclidean distance instead of Manhattan distance for more accurate detection
        dx = nearest_point_in_view.x() - mouse_pos_in_view.x()
        dy = nearest_point_in_view.y() - mouse_pos_in_view.y()
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Only highlight if the nearest point is within the threshold distance
        self.highlight_nearest = distance <= self.highlight_max_distance
        
        # Round to 2 decimal places for display
        rounded_x = round(scene_pos.x(), 2)
        rounded_y = round(-scene_pos.y(), 2)
        
        # Update the coordinate label (fixed size UI element)
        self.coords_label.setText(f"Coordinates: ({rounded_x}, {rounded_y})")
        self.coords_label.adjustSize()  # Adjust size to fit content
        
        # Handle right-button dragging for panning
        if event.buttons() & Qt.RightButton:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self.last_mouse_pos)
            self.last_mouse_pos = event.pos()
            
            # Move the scene in the direction opposite to mouse movement (for natural feel)
            self.translate(-delta.x(), -delta.y())
        
        # Force update to refresh the highlight
        self.viewport().update()
            
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

    def update_polygon(self):
        """Update the polygon with current points"""
        # Remove existing polygon if any
        if self.current_polygon:
            self.scene.removeItem(self.current_polygon)
            self.current_polygon = None
        
        # Need at least 2 points to draw a line
        if len(self.polygon_points) >= 2:
            # Create a QPolygonF from the points
            poly = QPolygonF(self.polygon_points)
            
            # Create a polygon item with semi-transparent fill
            self.current_polygon = self.scene.addPolygon(
                poly,
                QPen(QColor(0, 0, 255, 200), 2/self.transform().m11()),
                QBrush(QColor(0, 0, 255, 50))
            )

    def remove_last_point(self):
        """Remove the last added point"""
        if self.polygon_points:
            # Remove the last point
            removed_point = self.polygon_points.pop()
            
            # Remove its visual marker
            if self.point_items:
                last_marker = self.point_items.pop()
                self.scene.removeItem(last_marker)
            
            # Update the polygon
            self.update_polygon()
            
            # Print the removed point
            print(f"Removed point: ({removed_point.x()}, {removed_point.y()})")

    def center_on_point(self, x, y):
        """Center the view on a specific point"""
        self.centerOn(x, y)
        print(f"Centered on point: ({x}, {y})")

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.RightButton:
            self.setDragMode(QGraphicsView.NoDrag)
            self.last_mouse_pos = event.globalPosition().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton:
            # If a grid point is highlighted, try to add it to the polygon
            if self.highlight_nearest:
                x, y = self.nearest_grid_point.x(), self.nearest_grid_point.y()
                # Print the coordinates of the highlighted grid point to the console
                print(f"Selected grid point: ({x}, {y})")
                # Try to add this point to the polygon with validation
                self.add_polygon_point(x, y)
            
        super().mousePressEvent(event)

    def is_isothetic_direction(self, last_point, new_point):
        """Check if the direction from last_point to new_point is horizontal or vertical (isothetic)"""
        # A movement is isothetic if it's either purely horizontal or purely vertical
        return (abs(last_point.x() - new_point.x()) < 0.001) or (abs(last_point.y() - new_point.y()) < 0.001)

    def is_polygon_closed(self, new_point):
        """Check if adding this point would close the polygon by returning to the starting point"""
        if len(self.polygon_points) >= 3:  # Need at least 3 points before closing
            start_point = self.polygon_points[0]
            return (abs(start_point.x() - new_point.x()) < 0.001 and 
                    abs(start_point.y() - new_point.y()) < 0.001)
        return False

    def is_valid_isothetic_polygon(self):
        """Check if the current polygon follows isothetic rules (each segment is horizontal or vertical)"""
        if len(self.polygon_points) < 4:
            return False
            
        for i in range(len(self.polygon_points)):
            p1 = self.polygon_points[i]
            p2 = self.polygon_points[(i + 1) % len(self.polygon_points)]
            
            if not self.is_isothetic_direction(p1, p2):
                return False
                
        return True

    def add_polygon_point(self, x, y):
        """Add a point to the current polygon with isothetic validation"""
        new_point = QPointF(x, y)
        
        # Check if this would be valid in the isothetic polygon
        if self.polygon_points:
            last_point = self.polygon_points[-1]
            
            # If not an isothetic move, don't add the point
            if not self.is_isothetic_direction(last_point, new_point):
                print(f"Invalid point: ({x}, {y}) - not horizontal or vertical from last point")
                return False
                
            # Check if this closes the polygon
            if self.is_polygon_closed(new_point):
                # Complete the polygon if it's valid
                if self.is_valid_isothetic_polygon():
                    print(f"Polygon completed! It's a valid isothetic polygon.")
                    # Finalize the current polygon
                    self.finalize_polygon()
                    return True
                else:
                    print("Cannot close polygon: not a valid isothetic polygon")
                    return False
        
        # Add the point to the polygon
        self.polygon_points.append(new_point)
        
        # Create a visual point marker
        point_marker = self.scene.addEllipse(
            x - 5/self.transform().m11(), 
            y - 5/self.transform().m11(), 
            10/self.transform().m11(), 
            10/self.transform().m11(), 
            QPen(QColor(255, 0, 0)), 
            QBrush(QColor(255, 0, 0, 200))
        )
        self.point_items.append(point_marker)
        
        # Update the polygon
        self.update_polygon()
        
        # Print the added point
        print(f"Added point: ({x}, {y})")
        return True

    def finalize_polygon(self):
        """Finalize the current polygon and prepare for a new one"""
        # Store the completed polygon
        if not hasattr(self, 'completed_polygons'):
            self.completed_polygons = []
            
        # Create a copy of the current polygon points
        completed_points = [QPointF(p) for p in self.polygon_points]
        self.completed_polygons.append({
            'points': completed_points,
            'polygon': self.current_polygon
        })
        
        # The current polygon is now part of completed polygons, don't remove it
        self.current_polygon = None
        
        # Clear current points but keep the graphical items visible
        self.polygon_points = []
        self.point_items = []
        
        print(f"Polygon finalized, total polygons: {len(self.completed_polygons)}")

    def remove_polygon(self):
        """Remove the current polygon being drawn or the last completed one if no current polygon"""
        if self.polygon_points:
            # Remove current polygon being drawn
            for marker in self.point_items:
                self.scene.removeItem(marker)
            self.point_items.clear()
            
            if self.current_polygon:
                self.scene.removeItem(self.current_polygon)
                self.current_polygon = None
                
            self.polygon_points.clear()
            print("Current polygon removed")
        elif hasattr(self, 'completed_polygons') and self.completed_polygons:
            # Remove the last completed polygon
            last_polygon = self.completed_polygons.pop()
            self.scene.removeItem(last_polygon['polygon'])
            print(f"Last completed polygon removed, {len(self.completed_polygons)} remaining")
        else:
            print("No polygons to remove")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())