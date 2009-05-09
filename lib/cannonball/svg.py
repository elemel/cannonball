from __future__ import division

import numpy

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
