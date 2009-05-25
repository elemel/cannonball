from __future__ import division

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
import sys
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

def load_level(path):
    document = minidom.parse(path)
    root = [n for n in document.childNodes if n.nodeName == 'svg'][0]
    named_view = root.getElementsByTagName('sodipodi:namedview')[0]
    page_color = Color(named_view.getAttribute('pagecolor') or '#000000')
    scale = get_scale(document)
    width = float(root.getAttribute('width')) * scale
    height = float(root.getAttribute('height')) * scale
    aabb = b2AABB()
    aabb.lowerBound = 0, 0
    aabb.upperBound = width, height
    gravity = 0, -10
    doSleep = True
    world = b2World(aabb, gravity, doSleep)
    level = Level(world)
    level.background_color = tuple(c / 255 for c in page_color)
    transform = Transform('translate(0 %g) scale(%g) scale(1 -1)' %
                          (height, scale))
    load_layers(level, root, transform)
    for joint_position in level.joints:
        joint_aabb = b2AABB()
        joint_aabb.lowerBound = joint_position
        joint_aabb.upperBound = joint_position
        count, shapes = world.Query(joint_aabb, 1000)
        bodies = set(s.GetBody() for s in shapes)
        if len(bodies) == 2:
            body_1, body_2 = bodies
            joint_def = b2RevoluteJointDef()
            joint_def.Initialize(body_1, body_2, joint_position)
            world.CreateJoint(joint_def)
    return level

def get_scale(document):
    text_elements = document.getElementsByTagName('text')
    scale_elements = [e for e in text_elements
                      if e.getAttribute('id') == 'scale']
    if scale_elements:
        scale_text = get_text(scale_elements[0]).strip()
        scale_text = scale_text.lstrip('page-width').rstrip('m').strip()
        scale_text = scale_text.lstrip(':').strip()
        scale_width = float(scale_text) if scale_text else 1
        svg_element = document.getElementsByTagName('svg')[0]
        document_width = float(svg_element.getAttribute('width'))
        return scale_width / document_width
    return 1

def get_text(element):
    for node in element.childNodes:
        if node.nodeType == node.TEXT_NODE:
            return node.nodeValue
        elif node.nodeType == node.ELEMENT_NODE:
            return get_text(node)
    return ''

def load_layers(level, root, transform):
    for layer in root.childNodes:
        if (layer.nodeName == 'g' and
            layer.getAttribute('inkscape:groupmode') == 'layer'):
            for node in layer.childNodes:
                if node.nodeName in ('g', 'path'):
                    load_body(level, node, transform)

def load_body(level, node, transform):
    data = parse_element_data(node)
    module_name = data.get('actor')
    if module_name:
        if module_name == 'RevoluteJoint':
            transform = transform * Transform(node.getAttribute('transform'))
            center = (float(node.getAttribute('sodipodi:cx')),
                      float(node.getAttribute('sodipodi:cy')))
            level.joints.append(transform * center)
            return
        __import__(module_name)
        module = sys.modules[module_name]
        class_name = module_name.split('.')[-1]
        cls = getattr(module, class_name)
        actor = cls(level)
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
    transform = transform * Transform(node.getAttribute('transform'))
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
    path = Path(node.getAttribute('d'))
    for triangle in path.triangulate():
        triangle = [transform * (x, y) for x, y in reversed(triangle.vertices)]
        shape_def = b2PolygonDef()
        shape_def.vertices = triangle
        if data.get('sensor') == 'true':
            shape_def.isSensor = True
        shape_def.density = float(data.get('density', '0'))
        shape = actor.body.CreateShape(shape_def)
        shape.SetUserData({'color': tuple(c / 255 for c in color),
                           'texture': texture})

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
