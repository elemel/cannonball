from xml.dom import minidom
from subprocess import Popen, PIPE
import numpy

def parse_data(s):
    def parse_kv(kv):
        k, v = kv.split(':')
        return k.strip(), v.strip()
    return dict(parse_kv(kv) for kv in s.split(';') if kv.strip())

def parse_element_data(element):
    data = {}
    for name in ('style', 'label'):
        value = element.getAttribute(name)
        data.update(parse_data(value))
    return data

class Document(object):
    def __init__(self, f):
        self.document = minidom.parse(f)
        self.element = [n for n in self.document.childNodes
                        if n.nodeName == 'svg'][0]
        self.layers = [LayerElement(n) for n in self.element.childNodes
                       if n.nodeName == 'g' and
                       n.getAttribute('inkscape:groupmode') == 'layer']

class LayerElement(object):
    def __init__(self, element):
        self.element = element
        self.groups = [GroupElement(n) for n in element.childNodes
                       if n.nodeName == 'g']

class GroupElement(object):
    def __init__(self, element):
        self.element = element
        self.data = parse_element_data(element)
        self.paths = [PathElement(n) for n in element.childNodes
                      if n.nodeName == 'path']

class PathError(Exception):
    pass

class PathElement(object):
    def __init__(self, element):
        self.element = element
        self.data = parse_element_data(element)
        self.path = Path(element.getAttribute('d'))

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
        points = points.split('C')
        points = [p.split()[-2:] for p in points]
        points = [[float(x) for x in p] for p in points]
        if points[0] == points[-1]:
            points.pop()
        return [Point(*p) for p in points]

    def __str__(self):
        return 'M %s z' % (' L '.join('%g %g' % (p.x, p.y)
                                      for p in self.points))

    def __repr__(self):
        return "Path('%s')" % self

    def convexify(self):
        p = Popen('convexify', stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdin = '%d %s' % (len(self.points),
                           ' '.join('%g %g' % (p.x, p.y) for p in self.points))
        stdout, stderr = p.communicate(stdin)
        lines = stdout.splitlines()
        assert(int(lines[0])) + 1 == len(lines)
        paths = []
        for line in lines[1:]:
            args = line.split()
            assert int(args[0]) * 2 + 1 == len(args)
            points = zip(args[1::2], args[2::2])
            points = [Point(float(x), float(y)) for x, y in points]
            paths.append(Path(points))
        return paths

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return '(%g, %g)' % (self.x, self.y)

    def __repr__(self):
        return 'Point(%g, %g)' % (self.x, self.y)

class Transform(object):
    def __init__(self, arg=''):
        if type(arg) in (str, unicode):
            self.matrix = self._parse(arg)
        elif type(arg) is numpy.matrix:
            self.matrix = arg.copy()
        else:
            raise TypeError()

    def _parse(self, s):
        matrix = numpy.mat(numpy.eye(3))
        for transform in s.replace(',', ' ').split(')')[:-1]:
            name, args = transform.split('(')
            name = name.strip()
            args = [float(arg) for arg in args.split()]
            parse = getattr(self, '_parse_%s' % name)
            matrix = matrix * parse(*args)
        return matrix

    def _parse_matrix(self, a, b, c, d, e, f):
        return numpy.mat([[a, c, e],
                          [b, d, f],
                          [0, 0, 1]])

    def _parse_translate(self, tx, ty=0):
        """Parse a translation.
        
        >>> str(Transform('translate(3.14)'))
        'matrix(1, 0, 0, 1, 3.14, 0)'
        >>> str(Transform('translate(-3.14, 2.72)'))
        'matrix(1, 0, 0, 1, -3.14, 2.72)'
        """
        
        return self._parse_matrix(1, 0, 0, 1, tx, ty)

    def _parse_scale(self, sx, sy=None):
        """Parse a scale transform.
        
        >>> str(Transform('scale(3.14)'))
        'matrix(3.14, 0, 0, 3.14, 0, 0)'
        >>> str(Transform('scale(-3.14, 2.72)'))
        'matrix(-3.14, 0, 0, 2.72, 0, 0)'
        """

        if sy is None:
            sy = sx
        return self._parse_matrix(sx, 0, 0, sy, 0, 0)

    def _parse_rotate(self, a, cx=None, cy=None):
        """Parse a rotation.
        
        >>> str(Transform('rotate(45)'))
        'matrix(0.707107, 0.707107, -0.707107, 0.707107, 0, 0)'
        """

        a = a * numpy.pi / 180
        if cx is None:
            # Rotate around the current origin.
            return self._parse_matrix(numpy.cos(a), numpy.sin(a),
                                      -numpy.sin(a), numpy.cos(a), 0, 0)
        else:
            # Rotate around a point.
            return (self._parse_translate(cx, cy) *
                    self._parse_rotate(a) *
                    self._parse_translate(-cx, -cy))

    def _parse_skewX(self, a):
        a = a * numpy.pi / 180
        return self._parse_matrix(1, 0, numpy.tan(a), 1, 0, 0)

    def _parse_skewY(self, a):
        a = a * numpy.pi / 180
        return self._parse_matrix(1, numpy.tan(a), 0, 1, 0, 0)

    def __str__(self):
        a, c, e = self.matrix[0, 0], self.matrix[0, 1], self.matrix[0, 2]
        b, d, f = self.matrix[1, 0], self.matrix[1, 1], self.matrix[1, 2]
        return 'matrix(%g, %g, %g, %g, %g, %g)' % (a, b, c, d, e, f)

    def __repr__(self):
        return "Transform('%s')" % self

    def __mul__(self, other):
        if type(other) is Transform:
            return Transform(self.matrix * other.matrix)
        elif type(other) in (tuple, list):
            v = numpy.dot(self.matrix, tuple(other) + (1,))
            return v[0, 0], v[0, 1]
        else:
            raise TypeError()

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
