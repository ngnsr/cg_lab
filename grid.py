import math
import json
from typing import List
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QLabel
from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPolygonF
from utils import grid_based_intersection_qt

class GridView(QGraphicsView):
    invalid_action = Signal(str)  # Signal for showing toast messages
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Polygon management variables
        self.polygon_points = []  # List of QPointF for polygon vertices
        self.current_polygon = None  # Will be a QGraphicsPolygonItem
        self.point_items = []  # List to keep track of point markers
        self.completed_polygons = []
        self.intersection_polygons = []  # Store intersection polygon
        
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
        self.last_mouse_pos = QPointF()
        
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
        transform = self.transform()
        current_scale = transform.m11()
        
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
            return 0.1
    
    def find_nearest_grid_point(self, scene_pos):
        """Find the nearest grid intersection point to the given scene position"""
        grid_size = self.get_adaptive_grid_size()
        grid_x = round(scene_pos.x() / grid_size) * grid_size
        grid_y = round(scene_pos.y() / grid_size) * grid_size
        return QPointF(grid_x, grid_y)
    
    def drawForeground(self, painter, rect):
        """Draw foreground elements including the green highlight dot"""
        super().drawForeground(painter, rect)
        
        if self.highlight_nearest:
            transform = self.transform()
            current_scale = transform.m11()
            scaled_radius = self.highlight_radius / current_scale
            highlight_pen = QPen(QColor(0, 180, 0))
            highlight_pen.setWidthF(2 / current_scale)
            painter.setPen(highlight_pen)
            highlight_brush = QBrush(QColor(0, 255, 0, 180))
            painter.setBrush(highlight_brush)
            painter.drawEllipse(self.nearest_grid_point, scaled_radius, scaled_radius)
    
    def drawBackground(self, painter, rect):
        """Custom background drawing to create the grid"""
        super().drawBackground(painter, rect)
        
        transform = self.transform()
        current_scale = transform.m11()
        effective_grid_size = self.get_adaptive_grid_size()
        visible_rect = self.mapToScene(self.viewport().rect()).boundingRect()
        
        left = math.floor(visible_rect.left() / effective_grid_size) * effective_grid_size
        top = math.floor(visible_rect.top() / effective_grid_size) * effective_grid_size
        right = math.ceil(visible_rect.right() / effective_grid_size) * effective_grid_size
        bottom = math.ceil(visible_rect.bottom() / effective_grid_size) * effective_grid_size
        
        pen_width = min(0.5 / current_scale, 0.5)
        thin_pen = QPen(QColor(200, 200, 200))
        thin_pen.setWidthF(pen_width)
        thick_pen = QPen(QColor(120, 120, 120))
        thick_pen.setWidthF(pen_width * 2)
        
        if effective_grid_size < 0.00001:
            effective_grid_size = 0.00001
        step = effective_grid_size
        
        y = top
        while y <= bottom:
            major_line = round(y / effective_grid_size) % 5 == 0
            painter.setPen(thick_pen if major_line else thin_pen)
            painter.drawLine(left, y, right, y)
            y += step
            
        x = left
        while x <= right:
            major_line = round(x / effective_grid_size) % 5 == 0
            painter.setPen(thick_pen if major_line else thin_pen)
            painter.drawLine(x, top, x, bottom)
            x += step
            
        axis_pen = QPen(QColor(0, 0, 0))
        axis_width = max(2 / current_scale, 0.5)
        axis_pen.setWidthF(axis_width)
        painter.setPen(axis_pen)
        painter.drawLine(0, top, 0, bottom)
        painter.drawLine(left, 0, right, 0)
        
        self.grid_info_label.setText(f"Grid: {effective_grid_size:.1f}px | Scale: {current_scale:.4f}x")
        self.grid_info_label.adjustSize()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        scene_pos = self.mapToScene(event.pos())
        current_scale = self.transform().m11()
        adjusted_threshold = self.axis_snap_threshold / current_scale
        
        if abs(scene_pos.x()) < adjusted_threshold:
            scene_pos.setX(0)
        if abs(scene_pos.y()) < adjusted_threshold:
            scene_pos.setY(0)
        
        self.nearest_grid_point = self.find_nearest_grid_point(scene_pos)
        nearest_point_in_view = self.mapFromScene(self.nearest_grid_point)
        mouse_pos_in_view = event.pos()
        dx = nearest_point_in_view.x() - mouse_pos_in_view.x()
        dy = nearest_point_in_view.y() - mouse_pos_in_view.y()
        distance = math.sqrt(dx*dx + dy*dy)
        self.highlight_nearest = distance <= self.highlight_max_distance
        
        rounded_x = round(scene_pos.x(), 2)
        rounded_y = round(-scene_pos.y(), 2)
        self.coords_label.setText(f"Coordinates: ({rounded_x}, {rounded_y})")
        self.coords_label.adjustSize()
        
        if event.buttons() & Qt.RightButton:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self.last_mouse_pos)
            self.last_mouse_pos = event.pos()
            self.translate(-delta.x(), -delta.y())
        
        self.viewport().update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.RightButton:
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Handle wheel events for zooming"""
        zoom_in = event.angleDelta().y() > 0
        current_scale = self.transform().m11()
        
        if zoom_in:
            if current_scale < 1000:
                self.scale_factor *= self.zoom_factor
                self.scale(self.zoom_factor, self.zoom_factor)
        else:
            if current_scale > 0.001:
                self.scale_factor /= self.zoom_factor
                self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
        
        self.viewport().update()
    
    def update_polygon(self):
        """Update the polygon with current points"""
        if self.current_polygon:
            self.scene.removeItem(self.current_polygon)
            self.current_polygon = None
        
        if len(self.polygon_points) >= 2:
            poly = QPolygonF(self.polygon_points)
            self.current_polygon = self.scene.addPolygon(
                poly,
                QPen(QColor(0, 0, 255, 200), 2/self.transform().m11()),
                QBrush(QColor(0, 0, 255, 50))
            )
    
    def remove_last_point(self):
        """Remove the last added point"""
        if self.polygon_points:
            removed_point = self.polygon_points.pop()
            if self.point_items:
                last_marker = self.point_items.pop()
                self.scene.removeItem(last_marker)
            self.update_polygon()
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
            if self.highlight_nearest:
                x, y = self.nearest_grid_point.x(), self.nearest_grid_point.y()
                print(f"Selected grid point: ({x}, {y})")
                self.add_polygon_point(x, y)
        super().mousePressEvent(event)
    
    def is_isothetic_direction(self, last_point, new_point):
        """Check if the direction from last_point to new_point is horizontal or vertical"""
        return (abs(last_point.x() - new_point.x()) < 0.001) or (abs(last_point.y() - new_point.y()) < 0.001)
    
    def add_polygon_point(self, x, y):
        """Add a point to the current polygon with isothetic validation"""
        new_point = QPointF(x, y)
        
        if self.polygon_points:
            last_point = self.polygon_points[-1]
            if not self.is_isothetic_direction(last_point, new_point):
                self.invalid_action.emit("Invalid point: not horizontal or vertical from last point")
                print(f"Invalid point: ({x}, {y}) - not horizontal or vertical from last point")
                return False
        
        self.polygon_points.append(new_point)
        point_marker = self.scene.addEllipse(
            x - 5/self.transform().m11(), 
            y - 5/self.transform().m11(), 
            10/self.transform().m11(), 
            10/self.transform().m11(), 
            QPen(QColor(255, 0, 0)), 
            QBrush(QColor(255, 0, 0, 200))
        )
        self.point_items.append(point_marker)
        self.update_polygon()
        print(f"Added point: ({x}, {y})")
        return True
    
    def finalize_polygon(self):
        """Finalize the current polygon and prepare for a new one"""
        if len(self.polygon_points) < 3:
            self.invalid_action.emit("Polygon must have at least 3 points")
            print("Cannot finalize polygon: must have at least 3 points")
            return
        
        start_point = self.polygon_points[0]
        last_point = self.polygon_points[-1]
        if abs(start_point.x() - last_point.x()) > 0.001 or abs(start_point.y() - last_point.y()) > 0.001:
            self.invalid_action.emit("Polygon must be closed by selecting the starting point")
            print("Cannot finalize polygon: last point must match the starting point")
            return
        
        completed_points = [QPointF(p) for p in self.polygon_points[:-1]]
        if self.current_polygon:
            self.completed_polygons.append({
                'points': completed_points,
                'polygon': self.current_polygon
            })
            self.current_polygon = None
        
        for marker in self.point_items:
            self.scene.removeItem(marker)
        self.point_items = []
        self.polygon_points = []
        self.update_polygon()
        print(f"Polygon finalized, total polygons: {len(self.completed_polygons)}")
    
    def remove_polygon(self):
        """Remove the current polygon being drawn or the last completed one"""
        if self.polygon_points:
            for marker in self.point_items:
                self.scene.removeItem(marker)
            self.point_items.clear()
            if self.current_polygon:
                self.scene.removeItem(self.current_polygon)
                self.current_polygon = None
            self.polygon_points.clear()
            print("Current polygon removed")
        elif self.completed_polygons:
            last_polygon = self.completed_polygons.pop()
            self.scene.removeItem(last_polygon['polygon'])
            print(f"Last completed polygon removed, {len(self.completed_polygons)} remaining")
        else:
            print("No polygons to remove")
    

    def calculate_intersection(self):
        """Calculate the grid-based intersection of all completed polygons."""
        if len(self.completed_polygons) < 2:
            self.invalid_action.emit("Need at least two polygons to calculate intersection")
            print("Need at least two polygons to calculate intersection")
            return

        # Clear previous intersection graphics
        if hasattr(self, 'scene') and self.scene is not None:
            for item in self.intersection_polygons:
                if item.scene() == self.scene:
                    self.scene.removeItem(item)
        self.intersection_polygons.clear()

        # Compute intersection rectangles
        intersection_rects = self.compute_all_polygons_intersection()

        if intersection_rects:
            current_transform = self.transform() if hasattr(self, 'transform') else None
            pen_width_scale_factor = current_transform.m11() if current_transform and current_transform.m11() != 0 else 1.0

            if hasattr(self, 'scene') and self.scene is not None:
                print(intersection_rects)

                # Єдиний стиль для всіх прямокутників
                pen = QPen(QColor(0, 200, 0, 255), 1 / pen_width_scale_factor)  # насичена зелена рамка
                brush = QBrush(QColor(0, 255, 0, 100))  # менш прозорий зелений заповнення


                for rect in intersection_rects:
                    rect_item = self.scene.addRect(rect, pen, brush)
                    self.intersection_polygons.append(rect_item)

                self.invalid_action.emit("Grid-based intersection calculated")
                print("Grid-based intersection calculated")
            else:
                self.invalid_action.emit("Scene not available for rendering intersection")
                print("Scene not available for rendering intersection")
        else:
            self.invalid_action.emit("No common intersection found")
            print("No common intersection found")


    def compute_all_polygons_intersection(self) -> List[QRectF]:
        """Compute the intersection of all completed polygons using grid-based method."""
        if len(self.completed_polygons) < 2:
            return []

        base_poly = QPolygonF(self.completed_polygons[0].get('points', []))
        if base_poly.count() < 3:
            return []

        for i in range(1, len(self.completed_polygons)):
            next_poly = QPolygonF(self.completed_polygons[i].get('points', []))
            if next_poly.count() < 3:
                return []

            # Перетинаємо дві множини прямокутників
            if i == 1:
                intersection_rects = grid_based_intersection_qt(base_poly, next_poly)
            else:
                intersection_rects = [
                    rect for rect in intersection_rects
                    if any(
                        grid_based_intersection_qt(QPolygonF([
                            QPointF(rect.left(), rect.top()),
                            QPointF(rect.right(), rect.top()),
                            QPointF(rect.right(), rect.bottom()),
                            QPointF(rect.left(), rect.bottom())
                        ]), next_poly)
                    )
                ]

            if not intersection_rects:
                return []

        return intersection_rects

    def export_polygons(self, file_name):
        """Export completed polygons and intersection to a JSON file"""
        data = {
            "polygons": [
                [{"x": p.x(), "y": -p.y()} for p in poly['points']]
                for poly in self.completed_polygons
            ],
            "intersection": [
                [{"x": p.x(), "y": -p.y()} for p in inter]
                for inter in [
                    QPolygonF(item.polygon()).toList()
                    for item in self.intersection_polygons
                ]
            ]
        }
        
        with open(file_name, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Polygons exported to {file_name}")
    
    def import_polygons(self, file_name):
        """Import polygons and intersection from a JSON file"""
        try:
            with open(file_name, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
        
        # Validate structure
        if not isinstance(data, dict) or "polygons" not in data:
            raise ValueError("Invalid file format: missing 'polygons' key")
        
        # Clear existing polygons and intersections
        for poly in self.completed_polygons:
            self.scene.removeItem(poly['polygon'])
        self.completed_polygons.clear()
        for item in self.intersection_polygons:
            self.scene.removeItem(item)
        self.intersection_polygons.clear()
        if self.current_polygon:
            self.scene.removeItem(self.current_polygon)
            self.current_polygon = None
        for marker in self.point_items:
            self.scene.removeItem(marker)
        self.point_items.clear()
        self.polygon_points.clear()
        
        # Load polygons
        for poly_points in data.get("polygons", []):
            if len(poly_points) < 3:
                raise ValueError("Polygon must have at least 3 points")
            
            # Validate isothetic property
            points = [QPointF(p["x"], -p["y"]) for p in poly_points]
            for i in range(len(points)):
                prev_point = points[i - 1]
                curr_point = points[i]
                if not self.is_isothetic_direction(prev_point, curr_point):
                    raise ValueError(f"Non-isothetic edge detected in polygon at point {i}")
            
            # Create and add the polygon
            poly = QPolygonF(points)
            polygon_item = self.scene.addPolygon(
                poly,
                QPen(QColor(0, 0, 255, 200), 2/self.transform().m11()),
                QBrush(QColor(0, 0, 255, 50))
            )
            self.completed_polygons.append({
                'points': points,
                'polygon': polygon_item
            })
        
        # Load intersection if present
        intersection_loaded = False
        for inter_points in data.get("intersection", []):
            if len(inter_points) < 3:
                raise ValueError("Intersection polygon must have at least 3 points")
            
            # Validate isothetic property
            points = [QPointF(p["x"], -p["y"]) for p in inter_points]
            for i in range(len(points)):
                prev_point = points[i - 1]
                curr_point = points[i]
                if not self.is_isothetic_direction(prev_point, curr_point):
                    raise ValueError(f"Non-isothetic edge detected in intersection at point {i}")
            
            # Create and add the intersection polygon
            poly = QPolygonF(points)
            intersection_item = self.scene.addPolygon(
                poly,
                QPen(QColor(0, 255, 0, 200), 2/self.transform().m11()),
                QBrush(QColor(0, 255, 0, 50))
            )
            self.intersection_polygons.append(intersection_item)
            intersection_loaded = True
        
        toast_message = f"Imported {len(self.completed_polygons)} polygons"
        if intersection_loaded:
            toast_message += " with intersection"
        self.invalid_action.emit(toast_message)
        print(f"Imported {len(self.completed_polygons)} polygons from {file_name}, intersection loaded: {intersection_loaded}")