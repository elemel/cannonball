from __future__ import division

from math import cos, pi, sin, tan
import re

class SVGError(Exception):
    pass

class Vector(object):
    def __init__(self, comps):
        self.__comps = tuple(comps)

    @property
    def x(self):
        return self.__comps[0]

    @property
    def y(self):
        return self.__comps[1]

    def __add__(self, other):
        """
        >>> Vector([1, 2]) + Vector([3, 5])
        Vector([4, 7])
        """
        return Vector(a + b for a, b in zip(self, other))

    def __sub__(self, other):
        return Vector(a - b for a, b in zip(self, other))

    def __mul__(self, k):
        return Vector(a * k for a in self)

    __rmul__ = __mul__

    def __div__(self, k):
        return Vector(a / k for a in self)

    def __neg__(self):
        return Vector(-a for a in self)

    def __eq__(self, other):
        return all(a == b for a, b in zip(self, other))

    def __len__(self):
        return len(self.__comps)

    def __iter__(self):
        return iter(self.__comps)

    def __abs__(self):
        return sqrt(a ** 2 for a in self)

    def __str__(self):
        return str(list(self))

    def __repr__(self):
        return 'Vector(%s)' % self

    @property
    def norm(self):
        return self / abs(self)

    @property
    def perp(self):
        """
        >>> Vector([1, 2]).perp
        Vector([-2, 1])
        """
        x, y = self
        return Vector([-y, x])

class Polygon(object):
    def __init__(self, vertices):
        self.vertices = [Vector(v) for v in vertices]
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
        return self if self.clockwise else Polygon(reversed(self.vertices))

    def __iter__(self):
        return iter(self.vertices)

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

def bezier_points(points, steps=5):
    """
    http://www.niksula.cs.hut.fi/~hkankaan/Homepages/bezierfast.html
    """

    t = 1 / steps
    t2 = t ** 2

    p0, p1, p2, p3 = points
    f = p0
    fd = 3 * (p1 - p0) * t
    fdd_per_2 = 3 * (p0 - 2 * p1 + p2) * t2
    fddd_per_2 = 3 * (3 * (p1 - p2) + p3 - p0) * t2 * t

    fddd = fddd_per_2 + fddd_per_2
    fdd = fdd_per_2 + fdd_per_2
    fddd_per_6 = fddd_per_2 * (1 / 3)

    for x in xrange(steps):
        f += fd + fdd_per_2 + fddd_per_6
        yield f
        fd += fdd + fddd_per_2
        fdd += fddd
        fdd_per_2 += fddd_per_2

class Color(object):
    def __init__(self, s):
        if s[0] ==  '#':
            self.red = int(s[1:3], 16)
            self.green = int(s[3:5], 16)
            self.blue = int(s[5:7], 16)
        else:
            raise SVGError('invalid color: %s' % s)

    def __iter__(self):
        yield self.red
        yield self.green
        yield self.blue

    def __str__(self):
        """
        >>> str(Color('#abcdef'))
        '#abcdef'
        """
        return '#%2x%2x%2x' % (self.red, self.green, self.blue)

def parse_command(s):
    s = s.replace(',', ' ')
    name = s[0]
    args = map(float, s[1:].split())
    return Command(name, args)

class Path(object):
    subpath_re = re.compile('M[^M]*')

    def __init__(self, subpaths):
        if isinstance(subpaths, basestring):
            self.subpaths = map(Subpath, self.subpath_re.findall(subpaths))
        else:
            self.subpaths = list(subpaths)

    def __str__(self):
        return ' '.join(str(s) for s in self.subpaths)

    def triangulate(self):
        for subpath in self.subpaths:
            for triangle in subpath.linearize().normalize().triangulate():
                yield triangle

class Subpath(object):
    command_re = re.compile('[A-Za-z][^A-Za-z]*')

    def __init__(self, commands):
        if isinstance(commands, basestring):
            self.commands = map(parse_command,
                                self.command_re.findall(commands))
        else:
            self.commands = list(commands)

    def __str__(self):
        return ' '.join(str(c) for c in self.commands)

    def linearize(self):
        vertices = []
        start_point = Vector([0, 0])
        for command in self.commands:
            if command.name == 'M':
                start_point = Vector(command.args)
                vertices.append(command.args)
            elif command.name == 'L':
                start_point = Vector(command.args)
                vertices.append(command.args)
            elif command.name == 'C':
                control_points = [start_point, Vector(command.args[0:2]),
                                  Vector(command.args[2:4]),
                                  Vector(command.args[4:6])]
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

def parse_style(style):
    def parse_pair(pair):
        key, value = pair.split(':')
        return key.strip(), value.strip()
    return dict(parse_pair(pair) for pair in style.split(';') if pair.strip())

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
