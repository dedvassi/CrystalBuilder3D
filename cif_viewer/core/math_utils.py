import math
import numpy as np

def rotation_matrix(rot_x, rot_y):
    x, y = math.radians(rot_x), math.radians(rot_y)
    rx = np.array(((1, 0, 0), (0, math.cos(x), -math.sin(x)), (0, math.sin(x), math.cos(x))))
    ry = np.array(((math.cos(y), 0, math.sin(y)), (0, 1, 0), (-math.sin(y), 0, math.cos(y))))
    return rx @ ry

def project(point, rot_x, rot_y, scale, center, offset):
    rotated = rotation_matrix(rot_x, rot_y) @ np.asarray(point)
    return center[0] + offset[0] + rotated[0] * scale, center[1] + offset[1] - rotated[1] * scale, rotated[2]

def point_in_polygon(point, polygon):
    x, y = point; inside = False
    for i, (x1, y1) in enumerate(polygon):
        x2, y2 = polygon[(i + 1) % len(polygon)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: inside = not inside
    return inside
