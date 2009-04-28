from xml.dom import minidom
from subprocess import Popen, PIPE

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
            points = zip(args[1::1], args[2::1])
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
