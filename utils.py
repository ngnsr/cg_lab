from typing import List, Tuple
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QPolygonF

def compute_bounding_box(polygon: QPolygonF) -> QRectF:
    if not polygon:
        return QRectF()
    x_coords = [p.x() for p in polygon]
    y_coords = [p.y() for p in polygon]
    x_min, x_max = min(x_coords), max(x_coords)
    y_min, y_max = min(y_coords), max(y_coords)
    return QRectF(x_min, y_min, x_max - x_min, y_max - y_min)

def get_intersection_point(p1: QPointF, p2: QPointF, p3: QPointF, p4: QPointF) -> QPointF:
    denom = (p4.y() - p3.y()) * (p2.x() - p1.x()) - (p4.x() - p3.x()) * (p2.y() - p1.y())
    if abs(denom) < 1e-10:
        return None

    ua = ((p4.x() - p3.x()) * (p1.y() - p3.y()) - (p4.y() - p3.y()) * (p1.x() - p3.x())) / denom
    if ua < 0 or ua > 1:
        return None

    ub = ((p2.x() - p1.x()) * (p1.y() - p3.y()) - (p2.y() - p1.y()) * (p1.x() - p3.x())) / denom
    if ub < 0 or ub > 1:
        return None

    x = p1.x() + ua * (p2.x() - p1.x())
    y = p1.y() + ua * (p2.y() - p1.y())
    return QPointF(x, y)

def point_in_polygon_qt(point: QPointF, polygon: QPolygonF) -> bool:
    x, y = point.x(), point.y()
    n = polygon.count()
    inside = False
    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]
        y1, y2 = p1.y(), p2.y()
        x1, x2 = p1.x(), p2.x()
        if (y1 > y) != (y2 > y):
            xinters = (y - y1) * (x2 - x1) / (y2 - y1 + 1e-10) + x1
            if x < xinters:
                inside = not inside
    return inside

def sweep_line_intersection_qt(poly1: QPolygonF, poly2: QPolygonF) -> List[QRectF]:
    if not poly1 or not poly2:
        return []

    bbox1 = compute_bounding_box(poly1)
    bbox2 = compute_bounding_box(poly2)
    if not bbox1.intersects(bbox2):
        return []

    intersection_points = []
    for i in range(poly1.count()):
        p1, p2 = poly1[i], poly1[(i + 1) % poly1.count()]
        for j in range(poly2.count()):
            p3, p4 = poly2[j], poly2[(j + 1) % poly2.count()]
            inter_point = get_intersection_point(p1, p2, p3, p4)
            if inter_point and point_in_polygon_qt(inter_point, poly1) and point_in_polygon_qt(inter_point, poly2):
                intersection_points.append(inter_point)

    events = []
    for i in range(poly1.count()):
        p1, p2 = poly1[i], poly1[(i + 1) % poly1.count()]
        events.append((min(p1.x(), p2.x()), 'start', (p1, p2), 1))
        events.append((max(p1.x(), p2.x()), 'end', (p1, p2), 1))
    for i in range(poly2.count()):
        p1, p2 = poly2[i], poly2[(i + 1) % poly2.count()]
        events.append((min(p1.x(), p2.x()), 'start', (p1, p2), 2))
        events.append((max(p1.x(), p2.x()), 'end', (p1, p2), 2))

    events.sort(key=lambda e: (e[0], e[1] == 'end'))

    x_coords = sorted(set([e[0] for e in events] + [p.x() for p in intersection_points]))
    y_coords = sorted(set([p.y() for p in list(poly1) + list(poly2) + intersection_points]))

    intersection_rects = []
    for i in range(len(x_coords) - 1):
        x1, x2 = x_coords[i], x_coords[i + 1]
        active_segments = []
        for event_x, event_type, segment, poly_id in events:
            if x1 <= event_x <= x2:
                if event_type == 'start':
                    active_segments.append((segment, poly_id))
                elif event_type == 'end' and (segment, poly_id) in active_segments:
                    active_segments.remove((segment, poly_id))

        for j in range(len(y_coords) - 1):
            y1, y2 = y_coords[j], y_coords[j + 1]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            point = QPointF(cx, cy)
            if point_in_polygon_qt(point, poly1) and point_in_polygon_qt(point, poly2):
                rect = QRectF(x1, y1, x2 - x1, y2 - y1)
                intersection_rects.append(rect)

    return intersection_rects