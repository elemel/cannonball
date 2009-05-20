from cannonball.agent import Agent
from cannonball.Level import *
from cannonball.svg import *

from Box2D import *
import imp
import os
import pyglet
from xml.dom import minidom

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

def load_agent_factories(root):
    agent_factories = {}
    for dir_path, _, file_names in os.walk(root):
        for file_name in file_names:
            module_name, ext = os.path.splitext(file_name)
            if ext == '.py':
                module_info = imp.find_module(module_name, [dir_path])
                module = imp.load_module(module_name, *module_info)
                cls = getattr(module, module_name)
                agent_factories[module_name] = cls
    return agent_factories

def load_level(path, agent_factories, scale=0.2):
    doc = minidom.parse(path)
    root = [n for n in doc.childNodes if n.nodeName == 'svg'][0]
    named_view = root.getElementsByTagName('sodipodi:namedview')[0]
    page_color = parse_color(named_view.getAttribute('pagecolor') or '#000000')
    width = float(root.getAttribute('width')) * scale
    height = float(root.getAttribute('height')) * scale
    aabb = b2AABB()
    aabb.lowerBound = 0, 0
    aabb.upperBound = width, height
    gravity = 0, -10
    doSleep = True
    world = b2World(aabb, gravity, doSleep)
    level = Level(world)
    level.agent_factories = agent_factories
    level.background_color = page_color
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
    if data.get('agent'):
        agent_factory = level.agent_factories[data['agent']]
        agent = agent_factory(level)
    else:
        agent = Agent(level)
    agent.id = node.getAttribute('id')
    agent.static = data.get('static') != 'false'
    level.agents[agent.id] = agent
    body_def = b2BodyDef()
    agent.body = level.world.CreateBody(body_def)
    agent.body.SetUserData(agent)
    load_shapes(level, agent, node, transform)
    agent.body.SetMassFromShapes()

def load_shapes(level, agent, node, transform):
    transform = transform * parse_transform(node.getAttribute('transform'))
    if node.nodeName == 'g':
        for child in node.childNodes:
            if child.nodeName in ('g', 'path'):
                load_shapes(level, agent, child, transform)
    elif node.nodeName == 'path':
        load_shape(level, agent, node, transform)

def load_shape(level, agent, node, transform):
    data = parse_element_data(node)
    color = parse_color(data.get('fill', '#ffffff'))
    material = data.get('material')
    path = node.getAttribute('d')
    path = linearize_path(path)
    path = Path(path)
    for triangle in path.triangulate():
        triangle = [transform * (x, y) for x, y in reversed(triangle)]
        shape_def = b2PolygonDef()
        shape_def.vertices = triangle
        if data.get('sensor') == 'true':
            shape_def.isSensor = True
        if agent.static:
            density = 0
        elif material:
            density = level.materials[material].density
        else:
            density = 100
        shape_def.density = density
        shape = agent.body.CreateShape(shape_def)
        shape.SetUserData({'color': color, 'material': material})

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