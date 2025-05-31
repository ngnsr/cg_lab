from typing import List
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPolygonF

def point_in_polygon_qt(point: QPointF, polygon: QPolygonF) -> bool:
    x, y = point.x(), point.y()
    inside = False
    n = polygon.count()

    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]

        if ((p1.y() > y) != (p2.y() > y)):
            xinters = (p2.x() - p1.x()) * (y - p1.y()) / (p2.y() - p1.y()) + p1.x()
            if x < xinters:
                inside = not inside

    return inside

def grid_based_intersection_qt(poly1: QPolygonF, 
                                poly2: QPolygonF) -> List[QRectF]:
    # Збираємо координати всіх точок
    all_points = list(poly1) + list(poly2)
    x_coords = sorted(set(p.x() for p in all_points))
    y_coords = sorted(set(p.y() for p in all_points))

    intersection_rects: List[QRectF] = []

    for i in range(len(x_coords) - 1):
        for j in range(len(y_coords) - 1):
            x1, x2 = x_coords[i], x_coords[i + 1]
            y1, y2 = y_coords[j], y_coords[j + 1]

            test_point = QPointF((x1 + x2) / 2, (y1 + y2) / 2)

            if point_in_polygon_qt(test_point, poly1) and point_in_polygon_qt(test_point, poly2):
                rect = QRectF(x1, y1, x2 - x1, y2 - y1)
                intersection_rects.append(rect)

    return intersection_rects