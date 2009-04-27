from xml.dom import minidom

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
        self.layers = [Layer(n) for n in self.element.childNodes
                       if n.nodeName == 'g' and
                       n.getAttribute('inkscape:groupmode') == 'layer']

class Layer(object):
    def __init__(self, element):
        self.element = element
        self.bodies = [Group(n) for n in element.childNodes
                       if n.nodeName == 'g']

class Group(object):
    def __init__(self, element):
        self.element = element
        self.data = parse_element_data(element)
        self.paths = [Path(n) for n in element.childNodes
                      if n.nodeName == 'path']

class PathError(Exception):
    pass

class Path(object):
    def __init__(self, element):
        self.element = element
        self.data = parse_element_data(element)

        points = element.getAttribute('d').strip()
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
        points = [Point(*p) for p in points]
        self.points = points
        print self.points

class Point(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return '(%g, %g)' % (self.x, self.y)

    def __repr__(self):
        return 'Point(%g, %g)' % (self.x, self.y)
