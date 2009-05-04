import os, pyglet
from xml.dom import minidom
from Box2D import *
from cannonball.svg import *

def load_textures(root):
    textures = {}
    for dir_name, _, file_names in os.walk(root):
        for file_name in file_names:
            texture_name, ext = os.path.splitext(file_name)
            if ext == '.jpg':
                path = os.path.join(dir_name, file_name)
                image = pyglet.image.load(path)
                textures[texture_name] = image.get_texture()
    return textures

class Level(object):
    def __init__(self, world):
        self.world = world
        self.bodies = {}

def load_level(path, scale=0.2):
    doc = minidom.parse(path)
    root = [n for n in doc.childNodes if n.nodeName == 'svg'][0]
    width = float(root.getAttribute('width')) * scale
    height = float(root.getAttribute('height')) * scale
    aabb = b2AABB()
    aabb.lowerBound = 0, 0
    aabb.upperBound = width, height
    gravity = 0, -10
    doSleep = True
    world = b2World(aabb, gravity, doSleep)
    level = Level(world)
    transform = Transform('translate(0 %g) scale(%g) scale(1 -1)' %
                          (height, scale))
    load_layers(level, root, transform)
    return level

def load_layers(level, root, transform):
    for layer in root.childNodes:
        if (layer.nodeName == 'g' and
            layer.getAttribute('inkscape:groupmode') == 'layer'):
            for node in layer.childNodes:
                load_body(level, node, transform)

def load_body(level, node, transform):
    pass

def parse_data(s):
    try:
        def parse_kv(kv):
            k, v = kv.split(':')
            return k.strip(), v.strip()
        return dict(parse_kv(kv) for kv in s.split(';') if kv.strip())
    except:
        return {}

def parse_element_data(element):
    data = {}
    for name in ('style', 'inkscape:label'):
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
        self.id = element.getAttribute('id')
        self.element = element
        self.data = parse_element_data(element)
        self.paths = [PathElement(n) for n in element.childNodes
                      if n.nodeName == 'path']
        self.transform = Transform(self.element.getAttribute('transform'))

class PathElement(object):
    def __init__(self, element):
        self.element = element
        self.data = parse_element_data(element)
        self.path = Path(element.getAttribute('d'))
        self.transform = Transform(self.element.getAttribute('transform'))
