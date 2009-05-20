from __future__ import division

from math import cos, pi, sin, tan
import re

class Vector(object):
    __slots__ = '__x', '__y'

    def __init__(self, x, y):
        self.__x = x
        self.__y = y

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    def __add__(self, other):
        return type(self)(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return type(self)(self.x - other.x, self.y - other.y)

    def __mul__(self, k):
        return type(self)(k * self.x, k * self.y)

    __rmul__ = __mul__

class Polygon(object):
    def __init__(self, vertices):
        self.vertices = [tuple(v) for v in vertices]

    @property
    def area(self):
        """
        http://local.wasp.uwa.edu.au/~pbourke/geometry/clockwise/
        """
        result = 0
        for i in xrange(len(self.vertices)):
            j = (i + 1) % len(self.vertices)
            x, y = self.vertices[i]
            nx, ny = self.vertices[j]
            result += x * ny - nx * y
        return result / 2.0

class Triangle(object):
    def __init__(self, vertices):
        self.vertices = [tuple(v) for v in vertices]

    def contains(self, point):
        p1, p2, p3 = self.vertices
        for a, b in [(p1, p2), (p2, p3), (p3, p1)]:
            if Polygon([a, b, point]).area < 0:
                return False
        return True

    @property
    def area(self):
        """
        http://local.wasp.uwa.edu.au/~pbourke/geometry/clockwise/
        """
        result = 0
        for i in xrange(len(self.vertices)):
            j = (i + 1) % len(self.vertices)
            x, y = self.vertices[i]
            nx, ny = self.vertices[j]
            result += x * ny - nx * y
        return result / 2.0

def linearize_path(path):
    """
    Creates a path with only M and L. 
    In path can contain M, L and C. 
    """
    new_path = []
    for type, cs in get_path(path):
        if type == 'M':
            last_p = cs.next()
            new_path.append('M %f,%f' % (last_p))
        elif type == 'L':
            last_p = cs.next()
            new_path.append('L %f,%f' % (last_p))
        elif type == 'C':
            control_points = [last_p] + list(cs)
            for p in bezier_points(control_points):
                new_path.append('L %f,%f' % (p))
            last_p = control_points[-1]
        elif type == 'z':
            new_path.append('z')
    return ' '.join(new_path)

def bezier_points(p, steps=5):
    def bezier_iter(p, steps):
        """
        http://www.niksula.cs.hut.fi/~hkankaan/Homepages/bezierfast.html
        """
        t = 1.0 / steps
        t2 = t*t
    
        p0, p1, p2, p3 = p
        f = p0
        fd = 3 * (p1 - p0) * t
        fdd_per_2 = 3 * (p0 - 2 * p1 + p2) * t2
        fddd_per_2 = 3 * (3 * (p1 - p2) + p3 - p0) * t2 * t
    
        fddd = fddd_per_2 + fddd_per_2
        fdd = fdd_per_2 + fdd_per_2
        fddd_per_6 = fddd_per_2 * (1.0 / 3)
    
        for x in xrange(steps):
            f += fd + fdd_per_2 + fddd_per_6
            yield f
            fd += fdd + fddd_per_2
            fdd += fddd
            fdd_per_2 += fddd_per_2

    p = [Vector(*t) for t in p]
    return ((p.x, p.y) for p in bezier_iter(p, steps))

def get_path(path):
    regex = re.compile('([MLCz])([-\d., ]*)')
    return ((match.group(1),
            (tuple(float(c) for c in p.split(','))
             for p in match.group(2).split()))
             for match in regex.finditer(path))

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
        if Polygon(points).area < 0:
            points.reverse()
        triangles = []
        while len(points) > 2:
            n = len(points)
            for i in xrange(n):
                triangle = Triangle([points[(i - 1) % n], points[i],
                                     points[(i + 1) % n]])
                if triangle.area > 0 and all(not triangle.contains(p)
                                             for p in points
                                             if p not in triangle.vertices):
                    del points[i]
                    triangles.append(triangle)
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
