import pygame


def _projection_range(axis, points):
  dots = [point.dot(axis) for point in points]
  return min(dots), max(dots)


def _overlaps(range_a, range_b):
  return range_a[0] <= range_b[1] and range_b[0] <= range_a[1]


def _polygon_axes(points):
  axes = []
  count = len(points)
  for index in range(count):
    next_index = (index + 1) % count
    edge = points[next_index] - points[index]
    if edge.length_squared() == 0:
      continue
    normal = pygame.Vector2(-edge.y, edge.x)
    normal_length = normal.length()
    if normal_length == 0:
      continue
    axes.append(normal / normal_length)
  return axes


def _polygon_centroid(points):
  centroid = pygame.Vector2()
  for point in points:
    centroid += point
  return centroid / len(points)


def polygon_collision_mtv(points_a, points_b):
  if not points_a or not points_b:
    return None

  min_overlap = None
  smallest_axis = None

  axes = _polygon_axes(points_a) + _polygon_axes(points_b)
  if not axes:
    return None

  for axis in axes:
    projection_a = _projection_range(axis, points_a)
    projection_b = _projection_range(axis, points_b)
    if not _overlaps(projection_a, projection_b):
      return None

    overlap = min(projection_a[1], projection_b[1]) - max(projection_a[0], projection_b[0])
    if min_overlap is None or overlap < min_overlap:
      min_overlap = overlap
      smallest_axis = axis

  if smallest_axis is None or min_overlap is None:
    return None

  center_a = _polygon_centroid(points_a)
  center_b = _polygon_centroid(points_b)
  direction = center_b - center_a
  if direction.dot(smallest_axis) < 0:
    smallest_axis = -smallest_axis

  return smallest_axis, min_overlap


def polygons_overlap(points_a, points_b):
  return polygon_collision_mtv(points_a, points_b) is not None


def circle_polygon_overlap(center, radius, polygon_points):
  if not polygon_points:
    return False

  axes = _polygon_axes(polygon_points)

  closest_point = min(
    polygon_points,
    key=lambda point: (point - center).length_squared(),
  )
  extra_axis = closest_point - center
  if extra_axis.length_squared() > 0:
    axes.append(extra_axis.normalize())

  for axis in axes:
    poly_range = _projection_range(axis, polygon_points)
    center_projection = center.dot(axis)
    circle_range = (center_projection - radius, center_projection + radius)
    if not _overlaps(poly_range, circle_range):
      return False

  return True
