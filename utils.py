from PySide6.QtCore import QPointF

def is_inside(point: QPointF, edge_start: QPointF, edge_end: QPointF, clip_polygon: list[QPointF]) -> bool:
    """Determine if point is inside the half-plane defined by edge_start to edge_end."""
    dx = edge_end.x() - edge_start.x()
    dy = edge_end.y() - edge_start.y()
    px = point.x() - edge_start.x()
    py = point.y() - edge_start.y()

    # Find the next edge to determine the correct side
    next_idx = (clip_polygon.index(edge_end) + 1) % len(clip_polygon)
    next_point = clip_polygon[next_idx]
    next_dx = next_point.x() - edge_end.x()
    next_dy = next_point.y() - edge_end.y()

    # Cross product to determine the side where the polygon continues
    cross = dx * next_dy - dy * next_dx
    if abs(cross) < 1e-10:  # Collinear case
        return (min(edge_start.x(), edge_end.x()) <= point.x() <= max(edge_start.x(), edge_end.x()) and
                min(edge_start.y(), edge_end.y()) <= point.y() <= max(edge_start.y(), edge_end.y()))

    # Cross product with point vector
    cross_point = dx * py - dy * px
    return cross_point >= 0 if cross > 0 else cross_point <= 0  # Inside based on polygon orientation

def compute_intersection(p1: QPointF, p2: QPointF, edge_start: QPointF, edge_end: QPointF, clip_polygon: list[QPointF]) -> QPointF:
    """Compute intersection of line segment p1-p2 with clip edge edge_start-edge_end."""
    print(f"\nComputing intersection:")
    print(f"  Segment: P1=({p1.x()}, {p1.y()}) to P2=({p2.x()}, {p2.y()})")
    print(f"  Clip edge: Start=({edge_start.x()}, {edge_start.y()}) to End=({edge_end.x()}, {edge_end.y()})")
    
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    edx = edge_end.x() - edge_start.x()
    edy = edge_end.y() - edge_start.y()
    
    if edge_start.x() == edge_end.x():  # Vertical clip edge
        print(f"  Clip edge is vertical (x = {edge_start.x()})")
        if dx == 0:  # Parallel to vertical edge
            print("  Segments are parallel")
            if p1.x() == edge_start.x():
                y_min, y_max = min(edge_start.y(), edge_end.y()), max(edge_start.y(), edge_end.y())
                p_y, q_y = p1.y(), p2.y()
                if max(p_y, q_y) >= y_min and min(p_y, q_y) <= y_max:
                    print(f"  Segment overlaps clip edge, returning midpoint")
                    return QPointF(p1.x(), (p1.y() + p2.y()) / 2)
            print("  No intersection")
            return None
        t = (edge_start.x() - p1.x()) / dx
        print(f"  Parameter t = {t}")
        if 0 <= t <= 1:  # Intersection within p1-p2 segment (inclusive)
            y = p1.y() + t * dy
            print(f"  Calculated y = {y}")
            y_min, y_max = min(edge_start.y(), edge_end.y()), max(edge_start.y(), edge_end.y())
            print(f"  Clip edge y bounds: [{y_min}, {y_max}]")
            # Accept intersection if on boundary and p2 is Inside
            if (t == 1 and is_inside(p2, edge_start, edge_end, clip_polygon)) or (y_min <= y <= y_max):
                print(f"  Valid intersection at ({edge_start.x()}, {y})")
                return QPointF(edge_start.x(), y)
            else:
                print(f"  Intersection y ({y}) out of bounds or invalid")
        else:
            print(f"  Intersection t ({t}) out of segment bounds [0, 1]")
    else:  # Horizontal clip edge
        print(f"  Clip edge is horizontal (y = {edge_start.y()})")
        if dy == 0:  # Parallel to horizontal edge
            print("  Segments are parallel")
            if p1.y() == edge_start.y():
                x_min, x_max = min(edge_start.x(), edge_end.x()), max(edge_start.x(), edge_end.x())
                p_x, q_x = p1.x(), p2.x()
                if max(p_x, q_x) >= x_min and min(p_x, q_x) <= x_max:
                    print(f"  Segment overlaps clip edge, returning midpoint")
                    return QPointF((p1.x() + p2.x()) / 2, p1.y())
            print("  No intersection")
            return None
        t = (edge_start.y() - p1.y()) / dy
        print(f"  Parameter t = {t}")
        if 0 <= t <= 1:  # Intersection within p1-p2 segment (inclusive)
            x = p1.x() + t * dx
            print(f"  Calculated x = {x}")
            x_min, x_max = min(edge_start.x(), edge_end.x()), max(edge_start.x(), edge_end.x())
            print(f"  Clip edge x bounds: [{x_min}, {x_max}]")
            if (t == 1 and is_inside(p2, edge_start, edge_end, clip_polygon)) or (x_min <= x <= x_max):
                print(f"  Valid intersection at ({x}, {edge_start.y()})")
                return QPointF(x, edge_start.y())
            else:
                print(f"  Intersection x ({x}) out of bounds or invalid")
        else:
            print(f"  Intersection t ({t}) out of segment bounds [0, 1]")
    print("  No valid intersection found")
    return None

def clip_polygon(subject_polygon: list[QPointF], clip_polygon: list[QPointF]) -> list[QPointF]:
    if len(subject_polygon) < 3 or len(clip_polygon) < 3:
        print("Invalid input: Subject or clip polygon has fewer than 3 points.")
        return []

    output_list = subject_polygon[:]
    print(f"Initial subject polygon: {[(p.x(), p.y()) for p in output_list]}")
    
    for i in range(len(clip_polygon)):
        input_list = output_list
        output_list = []
        A = clip_polygon[i]
        B = clip_polygon[(i + 1) % len(clip_polygon)]
        
        print(f"\nClipping against edge {i}: from ({A.x()}, {A.y()}) to ({B.x()}, {B.y()})")
        print(f"Input list: {[(p.x(), p.y()) for p in input_list]}")

        for j in range(len(input_list)):
            P = input_list[j]
            Q = input_list[(j + 1) % len(input_list)]
            
            inside_p = is_inside(P, A, B, clip_polygon)
            inside_q = is_inside(Q, A, B, clip_polygon)
            
            print(f"  Vertex {j}: P=({P.x()}, {P.y()}), Q=({Q.x()}, {Q.y()})")
            print(f"    Inside P: {inside_p}, Inside Q: {inside_q}")

            if inside_p and inside_q:
                print(f"    Adding Q (both inside): ({Q.x()}, {Q.y()})")
                output_list.append(Q)
            elif inside_p and not inside_q:
                intersection = compute_intersection(P, Q, A, B, clip_polygon)
                if intersection:
                    print(f"    Intersection (P inside, Q outside): ({intersection.x()}, {intersection.y()})")
                    output_list.append(intersection)
            elif not inside_p and inside_q:
                intersection = compute_intersection(P, Q, A, B, clip_polygon)
                if intersection:
                    print(f"    Intersection (P outside, Q inside): ({intersection.x()}, {intersection.y()})")
                    output_list.append(intersection)
                print(f"    Adding Q (Q inside): ({Q.x()}, {Q.y()})")
                output_list.append(Q)
            else:  # Both outside
                pass  # No intersection to compute

        print(f"Output list after edge {i}: {[(p.x(), p.y()) for p in output_list]}")
        
        if len(output_list) < 3:
            print(f"Output list has fewer than 3 points after edge {i}. Returning empty list.")
            return []

    print(f"\nFinal intersection: {[(p.x(), p.y()) for p in output_list]}")
    return output_list