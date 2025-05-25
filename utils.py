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
    if abs(cross) < 1e-10:  # Collinear case (on the edge)
        x_min, x_max = min(edge_start.x(), edge_end.x()), max(edge_start.x(), edge_end.x())
        y_min, y_max = min(edge_start.y(), edge_end.y()), max(edge_start.y(), edge_end.y())
        on_edge = (x_min <= point.x() <= x_max and y_min <= point.y() <= y_max)
        return on_edge

    # Cross product with point vector
    cross_point = dx * py - dy * px
    # Inside if on the same side as the next edge
    is_inside_halfplane = (cross_point >= -1e-10 if cross > 0 else cross_point <= 1e-10)
    
    # Ensure point is within clip polygon bounds
    x_bounds = [v.x() for v in clip_polygon]
    y_bounds = [v.y() for v in clip_polygon]
    within_bounds = (min(x_bounds) <= point.x() <= max(x_bounds) and min(y_bounds) <= point.y() <= max(y_bounds))
    
    return is_inside_halfplane and within_bounds

def compute_intersection(p1: QPointF, p2: QPointF, edge_start: QPointF, edge_end: QPointF, clip_polygon: list[QPointF]) -> QPointF:
    print(f"\nComputing intersection:")
    print(f"  Segment: P1=({p1.x()}, {p1.y()}) to P2=({p2.x()}, {p2.y()})")
    print(f"  Clip edge: Start=({edge_start.x()}, {edge_start.y()}) to End=({edge_end.x()}, {edge_end.y()})")
    
    # Line segment p1-p2: p(t) = p1 + t * (p2 - p1), 0 <= t <= 1
    dx = p2.x() - p1.x()
    dy = p2.y() - p1.y()
    # Clip edge: e(s) = edge_start + s * (edge_end - edge_start), 0 <= s <= 1
    edx = edge_end.x() - edge_start.x()
    edy = edge_end.y() - edge_start.y()
    
    # Denominator for intersection
    denom = dx * edy - dy * edx
    if abs(denom) < 1e-10:  # Parallel or near-parallel
        print("  Segments are parallel")
        # Optional: Handle overlap by checking if segment lies on edge
        return None
    
    # Compute intersection parameters
    t = ((edge_start.x() - p1.x()) * edy - (edge_start.y() - p1.y()) * edx) / denom
    s = ((edge_start.x() - p1.x()) * dy - (edge_start.y() - p1.y()) * dx) / denom
    print(f"  Parameters: t = {t}, s = {s}")
    
    # Check if intersection is within both segments (including endpoints)
    if 0 <= t <= 1 and 0 <= s <= 1:
        x = p1.x() + t * dx
        y = p1.y() + t * dy
        print(f"  Valid intersection at ({x}, {y})")
        return QPointF(x, y)
    
    print("  No valid intersection (outside segment bounds)")
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
                pass
                # intersection = compute_intersection(P, Q, A, B, clip_polygon)
                # if intersection:
                #     print(f"    Intersection (both outside, boundary check): ({intersection.x()}, {intersection.y()})")
                #     output_list.append(intersection)
                # # Preserve if on clip polygon boundary
                # if (abs(P.y() - Q.y()) < 1e-10 and any(abs(P.y() - v.y()) < 1e-10 for v in clip_polygon)) or \
                #    (abs(P.x() - Q.x()) < 1e-10 and any(abs(P.x() - v.x()) < 1e-10 for v in clip_polygon)):
                #     print(f"    Adding P and Q as boundary segment: ({P.x()}, {P.y()}) to ({Q.x()}, {Q.y()})")
                #     output_list.append(P)
                #     output_list.append(Q)

        # Remove duplicates and filter points outside clip polygon bounds
        x_bounds = [v.x() for v in clip_polygon]
        y_bounds = [v.y() for v in clip_polygon]
        filtered_output = []
        for p in output_list:
            if (min(x_bounds) <= p.x() <= max(x_bounds) and min(y_bounds) <= p.y() <= max(y_bounds)):
                filtered_output.append(p)
            else:
                print(f"    Filtered out point outside clip bounds: ({p.x()}, {p.y()})")
        output_list = [filtered_output[i] for i in range(len(filtered_output)) if i == 0 or filtered_output[i] != filtered_output[i-1]]
        print(f"Output list after edge {i} (no duplicates): {[(p.x(), p.y()) for p in output_list]}")
        
        if len(output_list) < 3 and i < len(clip_polygon) - 1:
            print("Warning: Fewer than 3 points, but continuing clipping.")
            continue

    if len(output_list) < 3:
        print("Final output has fewer than 3 points. Returning empty list.")
        return []

    # Ensure the polygon is closed by adding the first point if not already present
    if output_list and output_list[-1] != output_list[0]:
        output_list.append(output_list[0])
        print(f"Closed polygon by adding first point: {output_list[0]}")

    print(f"\nFinal intersection: {[(p.x(), p.y()) for p in output_list]}")
    return output_list