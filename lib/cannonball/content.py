# Project imports.
from cannonball.Actor import Actor
from cannonball.Level import *
from cannonball.svg import *

# Third party imports.
from Box2D import *

# Standard library imports.
import imp
import os
import pyglet
from xml.dom import minidom

def load_textures(root):
    textures = {}
    for dir_name, _, file_names in os.walk(root):
        for file_name in file_names:
            texture_name, ext = os.path.splitext(file_name)
            if ext in ('.jpg', '.png'):
                path = os.path.join(dir_name, file_name)
                image = pyglet.image.load(path)
                textures[texture_name] = image.get_texture()
    return textures

def load_actor_factories(root):
    actor_factories = {}
    for dir_path, _, file_names in os.walk(root):
        for file_name in file_names:
            module_name, ext = os.path.splitext(file_name)
            if ext == '.py':
                module_info = imp.find_module(module_name, [dir_path])
                module = imp.load_module(module_name, *module_info)
                cls = getattr(module, module_name)
                actor_factories[module_name] = cls
    return actor_factories

def load_level(path, actor_factories, scale=0.2):
    doc = minidom.parse(path)
    root = [n for n in doc.childNodes if n.nodeName == 'svg'][0]
    named_view = root.getElementsByTagName('sodipodi:namedview')[0]
    page_color = Color(named_view.getAttribute('pagecolor') or '#000000')
    width = float(root.getAttribute('width')) * scale
    height = float(root.getAttribute('height')) * scale
    aabb = b2AABB()
    aabb.lowerBound = 0, 0
    aabb.upperBound = width, height
    gravity = 0, -10
    doSleep = True
    world = b2World(aabb, gravity, doSleep)
    level = Level(world)
    level.actor_factories = actor_factories
    level.background_color = tuple(page_color)
    transform = parse_transform('translate(0 %g) scale(%g) scale(1 -1)' %
                                (height, scale))
    load_layers(level, root, transform)
    return level

def load_layers(level, root, transform):
    for layer in root.childNodes:
        if (layer.nodeName == 'g' and
            layer.getAttribute('inkscape:groupmode') == 'layer'):
            for node in layer.childNodes:
                if node.nodeName in ('g', 'path'):
                    load_body(level, node, transform)

def load_body(level, node, transform):
    data = parse_element_data(node)
    if data.get('actor'):
        actor_factory = level.actor_factories[data['actor']]
        actor = actor_factory(level)
    else:
        actor = Actor(level)
    actor.id = node.getAttribute('id')
    level.actors[actor.id] = actor
    body_def = b2BodyDef()
    actor.body = level.world.CreateBody(body_def)
    actor.body.SetUserData(actor)
    load_shapes(level, actor, node, transform)
    actor.body.SetMassFromShapes()

def load_shapes(level, actor, node, transform):
    transform = transform * parse_transform(node.getAttribute('transform'))
    if node.nodeName == 'g':
        for child in node.childNodes:
            if child.nodeName in ('g', 'path'):
                load_shapes(level, actor, child, transform)
    elif node.nodeName == 'path':
        load_shape(level, actor, node, transform)

def load_shape(level, actor, node, transform):
    data = parse_element_data(node)
    color = Color('#ffffff')
    texture = None
    fill = data.get('fill')
    if fill.startswith('#'):
        color = Color(fill)
    elif fill.startswith('url(#') and fill.endswith(')'):
        pattern_id = fill.lstrip('url(#').rstrip(')')
        texture = get_image_name(node.ownerDocument, pattern_id)
    path = node.getAttribute('d')
    path = linearize_path(path)
    path = parse_path(path)
    for triangle in path.triangulate():
        triangle = [transform * (x, y) for x, y in reversed(triangle.vertices)]
        shape_def = b2PolygonDef()
        shape_def.vertices = triangle
        if data.get('sensor') == 'true':
            shape_def.isSensor = True
        shape_def.density = float(data.get('density', '0'))
        shape = actor.body.CreateShape(shape_def)
        shape.SetUserData({'color': tuple(color), 'texture': texture})

def get_image_name(document, pattern_id):
    pattern_elements = document.getElementsByTagName('pattern')
    pattern_element = [e for e in pattern_elements
                       if e.getAttribute('id') == pattern_id][0]
    if pattern_element.getAttribute('xlink:href'):
        pattern_id = pattern_element.getAttribute('xlink:href').lstrip('#')
        return get_image_name(document, pattern_id)
    image_elements = pattern_element.getElementsByTagName('image')
    if image_elements:
        image_name = image_elements[0].getAttribute('xlink:href')
        image_name = os.path.split(image_name)[1]
        image_name = os.path.splitext(image_name)[0]
        return image_name
    return None

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
