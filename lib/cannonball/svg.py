from __future__ import division

from math import cos, pi, sin, tan

def polygon_area(points):
    """
    http://local.wasp.uwa.edu.au/~pbourke/geometry/clockwise/
    """
    n = len(points)
    a = 0
    for i in xrange(n):
        j = (i + 1) % n
        x, y = points[i]
        nx, ny = points[j]
        a += x * ny - nx * y
    return a / 2.0

def point_in_triangle(p1, p2, p3, p):
    for a, b in [(p1, p2), (p2, p3), (p3, p1)]:
        if polygon_area((a, b, p)) < 0:
            return False
    return True

def parse_color(s):
    return int(s[1:3], 16) / 255, int(s[3:5], 16) / 255, int(s[5:7], 16) / 255

class PathError(Exception):
    pass

class Path(object):
    def __init__(self, points):
        if type(points) in (str, unicode):
            self.points = self._parse(points)
        else:
            self.points = list(points)

    def _parse(self, points):
        points = points.strip()
        if not points.startswith('M'):
            raise PathError('Path must start with "M" command')
        if not points.endswith('z'):
            raise PathError('Path must end with "z" command')
        points = points.strip('Mz')
        points = points.replace(',', ' ')
        points = points.replace('L', 'C')
        points = points.split('C')
        points = [p.split()[-2:] for p in points]
        points = [(float(x), float(y)) for x, y in points]
        if points[0] == points[-1]:
            points.pop()
        return points

    def __str__(self):
        return 'M %s z' % (' L '.join('%g %g' % (x, y)
                                      for x, y in self.points))

    def __repr__(self):
        return "Path('%s')" % self

    def triangulate(self):
        points = list(self.points)
        if polygon_area(points) < 0:
            points.reverse()
        triangles = []
        while len(points) > 2:
            n = len(points)
            for i in xrange(n):
                tri = points[(i-1) % n], points[i], points[(i+1) % n]
                lp, cp, rp = tri
                is_convex_vertice = polygon_area([lp, cp, rp]) > 0
                if is_convex_vertice and all(not point_in_triangle(rp, cp, lp, p)
                                             for p in points
                                             if p not in tri):
                    del points[i]
                    triangles.append((lp, cp, rp))
                    break
            else:
                raise RuntimeError('Cannot triangulate path')
        return triangles

def parse_transform(s):
    """
    >>> str(parse_transform('translate(3.14)'))
    'Transform((1, 0, 0, 1, 3.14, 0))'
    >>> str(parse_transform('translate(-3.14, 2.72)'))
    'Transform((1, 0, 0, 1, -3.14, 2.72))'
    >>> str(parse_transform('scale(3.14)'))
    'Transform((3.14, 0, 0, 3.14, 0, 0))'
    >>> str(parse_transform('scale(-3.14, 2.72)'))
    'Transform((-3.14, 0, 0, 2.72, 0, 0))'
    >>> str(parse_transform('rotate(45)'))
    'Transform((0.707107, 0.707107, -0.707107, 0.707107, 0, 0))'
    """
    
    transform = Transform()
    for part in s.replace(',', ' ').split(')')[:-1]:
        name, args = part.split('(')
        name = name.strip()
        args = [float(arg) for arg in args.split()]
        if name == 'matrix':
            transform *= Transform(args)
        elif name == 'translate':
            transform *= create_translate_transform(*args)
        elif name == 'scale':
            transform *= create_scale_transform(*args)
        elif name == 'rotate':
            transform *= create_rotate_transform(*args)
        elif name == 'skewX':
            transform *= create_skew_x_transform(*args)
        elif name == 'skewY':
            transform *= create_skew_y_transform(*args)
        else:
            raise ValueError('invalid transform name: ' + name)
    return transform

def create_translate_transform(tx, ty=0):
    return Transform((1, 0, 0, 1, tx, ty))

def create_scale_transform(sx, sy=None):
    if sy is None:
        sy = sx
    return Transform((sx, 0, 0, sy, 0, 0))

def create_rotate_transform(a, cx=None, cy=None):
    a = a * pi / 180
    if cx is None:
        # Rotate around the current origin.
        return Transform((cos(a), sin(a), -sin(a), cos(a), 0, 0))
    else:
        # Rotate around a point.
        return (self._parse_translate(cx, cy) *
                self._parse_rotate(a) *
                self._parse_translate(-cx, -cy))

def create_skew_x_transform(self, a):
    a = a * pi / 180
    return Transform((1, 0, tan(a), 1, 0, 0))

def create_skew_y_transform(self, a):
    a = a * pi / 180
    return Transform((1, tan(a), 0, 1, 0, 0))

class Transform(object):
    def __init__(self, matrix=(1, 0, 0, 1, 0, 0)):
        self.matrix = tuple(float(x) for x in matrix)

    def __mul__(self, other):
        a, b, c, d, e, f = self.matrix
        try:
            x, y = other
            return type(other)((a * x + c * y + e, b * x + d * y + f))
        except:
            a2, b2, c2, d2, e2, f2 = other.matrix
            a3 = a * a2 + c * b2
            b3 = b * a2 + d * b2
            c3 = a * c2 + c * d2
            d3 = b * c2 + d * d2
            e3 = a * e2 + c * f2 + e
            f3 = b * e2 + d * f2 + f
            return Transform((a3, b3, c3, d3, e3, f3))

    def __repr__(self):
        return 'Transform((%g, %g, %g, %g, %g, %g))' % self.matrix

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
