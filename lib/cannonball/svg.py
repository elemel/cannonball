from __future__ import division

from math import cos, pi, sin, tan
import re

class SVGError(Exception):
    pass

class Vector(object):
    __slots__ = '__x', '__y'

    def __init__(self, x, y):
        self.__x = float(x)
        self.__y = float(y)

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

    def __div__(self, k):
        return type(self)(self.x / k, self.y / k)

    def __neg__(self):
        return type(self)(-self.x, -self.y)

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

class Polygon(object):
    def __init__(self, vertices):
        self.vertices = [tuple(v) for v in vertices]
        if self.vertices[-1] == self.vertices[0]:
            self.vertices.pop()

    def contains(self, point):
        if len(self.vertices) != 3:
            raise SVGError('only implemented for triangles')
        p1, p2, p3 = self.vertices
        for a, b in [(p1, p2), (p2, p3), (p3, p1)]:
            if Polygon([a, b, point]).area < 0:
                return False
        return True

    def __repr__(self):
        return 'Polygon(%r)' % self.vertices

    @property
    def clockwise(self):
        return self.area >= 0

    def normalize(self):
        if not self.clockwise:
            self.reverse()

    def normalized(self):
        result = Polygon(self)
        result.normalize()
        return result

    def __iter__(self):
        return iter(self.vertices)

    def reverse(self):
        self.vertices.reverse()

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

    def triangulate(self):
        vertices = list(self.vertices)
        if not self.clockwise:
            raise SVGError('Cannot triangulate counter-clockwise polygon')
        triangles = []
        while len(vertices) >= 3:
            for i in xrange(len(vertices)):
                triangle = Polygon([vertices[(i - 1) % len(vertices)],
                                    vertices[i],
                                    vertices[(i + 1) % len(vertices)]])
                if triangle.clockwise and all(not triangle.contains(v)
                                              for v in vertices
                                              if v not in triangle.vertices):
                    del vertices[i]
                    triangles.append(triangle)
                    break
            else:
                raise SVGError('Cannot triangulate polygon')
        return triangles

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

class Color(object):
    def __init__(self, s):
        if s[0] ==  '#':
            self.r, self.g, self.b = (int(s[1:3], 16), int(s[3:5], 16),
                                      int(s[5:7], 16))
        else:
            raise SVGError('invalid color: %s' % s)

    def __iter__(self):
        yield self.r / 255
        yield self.g / 255
        yield self.b / 255

    def __str__(self):
        """
        >>> str(Color('#abcdef'))
        '#abcdef'
        """
        return '#%2x%2x%2x' % (self.r, self.g, self.b)

subpath_re = re.compile('M[^M]*')
command_re = re.compile('[A-Za-z][^A-Za-z]*')

def parse_path(s):
    return Path(parse_subpath(p) for p in subpath_re.findall(s))

def parse_subpath(s):
    return Subpath(parse_command(c) for c in command_re.findall(s))

def parse_command(s):
    s = s.replace(',', ' ')
    name = s[0]
    args = map(float, s[1:].split())
    return Command(name, args)

class Path(object):
    def __init__(self, subpaths):
        if isinstance(subpaths, basestring):
            self.subpaths = parse_path(subpaths).subpaths
        else:
            self.subpaths = list(subpaths)

    def __str__(self):
        return ' '.join(str(s) for s in self.subpaths)

    def triangulate(self):
        for subpath in self.subpaths:
            for triangle in subpath.linearize().normalized().triangulate():
                yield triangle

class Subpath(object):
    def __init__(self, commands):
        self.commands = list(commands)

    def __str__(self):
        return ' '.join(str(c) for c in self.commands)

    def linearize(self):
        vertices = []
        start_point = 0, 0
        for command in self.commands:
            if command.name == 'M':
                start_point = tuple(command.args)
                vertices.append(command.args)
            elif command.name == 'L':
                start_point = tuple(command.args)
                vertices.append(command.args)
            elif command.name == 'C':
                control_points = [start_point, command.args[0:2],
                                  command.args[2:4], command.args[4:6]]
                vertices.extend(bezier_points(control_points))
                start_point = control_points[-1]
            elif command.name == 'z':
                pass
        return Polygon(vertices)

class Command(object):
    def __init__(self, name, args):
        self.name = name
        self.args = list(float(a) for a in args)

    def __str__(self):
        result = [self.name]
        result.extend(str(a) for a in self.args)
        return ' '.join(result)

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
            raise SVGError('invalid transform name: ' + name)
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
        if isinstance(matrix, basestring):
            self.matrix = parse_transform(matrix).matrix
        else:
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
