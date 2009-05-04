import os, pyglet
from xml.dom import minidom
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
