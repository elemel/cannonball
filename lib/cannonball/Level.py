# Future imports.
from __future__ import division

# Project imports.
from cannonball.Actor import Actor
from cannonball.svg import *

# Third party imports.
import pyglet
from pyglet.gl import *
from Box2D import *

# Standard library imports.
from math import *
import os
import sys
from xml.dom import minidom

class Level(object):
    def __init__(self, path):
        self.path = path
        self.time = 0
        self.actors = {}        
        self.background_color = 0, 0, 0
        self.joints = []
        self.destroying = set()
        self.contacts = set()
        self.textures = {}
        self.load(path)
        background_path = os.path.dirname(os.path.dirname(self.path))
        background_path = os.path.join(background_path, 'textures',
                          'background.jpg')
        try:
            self.background = pyglet.image.load(background_path).get_texture()
        except:
            self.background = None
        self.contact_listener = CannonballContactListener(self)
        self.world.SetContactListener(self.contact_listener)

        self.boundary_listener = CannonballBoundaryListener(self)
        self.world.SetBoundaryListener(self.boundary_listener)

        self.circle_display_list = glGenLists(1)
        glNewList(self.circle_display_list, GL_COMPILE)
        self._draw_circle()
        glEndList()

    def load(self, path):
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
        self.world = b2World(aabb, gravity, doSleep)
        self.background_color = tuple(c / 255 for c in page_color)
        transform = Transform('translate(0 %g) scale(%g) scale(1 -1)' %
                              (height, scale))
        load_layers(self, root, transform)
        for joint_position in self.joints:
            joint_aabb = b2AABB()
            joint_aabb.lowerBound = joint_position
            joint_aabb.upperBound = joint_position
            count, shapes = self.world.Query(joint_aabb, 1000)
            bodies = set(s.GetBody() for s in shapes)
            if len(bodies) == 2:
                body_1, body_2 = bodies
                joint_def = b2RevoluteJointDef()
                joint_def.Initialize(body_1, body_2, joint_position)
                self.world.CreateJoint(joint_def)

    def get_texture(self, path):
        if path not in self.textures:
            p = path
            if not os.path.isabs(p):
                p = os.path.join(os.path.dirname(self.path), p)
            image = pyglet.image.load(p)
            self.textures[path] = image.get_texture()
        return self.textures[path]

    def step(self, dt):
        self.time += dt
        cannonball = self.actors.get('cannonball')
        if cannonball:
            cannonball.step(dt)

        velocityIterations = 10
        positionIterations = 8
        self.contacts.clear()
        self.world.Step(dt, velocityIterations, positionIterations)
        for actor_1, actor_2 in self.contacts:
            actor_1.collide(actor_2)
            actor_2.collide(actor_1)
        for actor in self.destroying:
            if actor.body:
                self.world.DestroyBody(actor.body)
                actor.body = None
                if actor.id:
                    del self.actors[actor.id]
            if actor.display_list is not None:
                glDeleteLists(actor.display_list, 1)
                actor.display_list = None
        self.destroying.clear()

    def queue_destroy(self, actor, delay):
        def destroy(dt):
            self.destroying.add(actor)
        pyglet.clock.schedule_once(destroy, delay)

    def add_contact(self, point):
        actor_1 = point.shape1.GetBody().GetUserData()
        actor_2 = point.shape2.GetBody().GetUserData()
        if actor_1 and actor_2:
            self.contacts.add((actor_1, actor_2))

    def persist_contact(self, point):
        pass

    def remove_contact(self, point):
        pass

    def contact_result(self, point):
        pass

    def boundary_violation(self, body):
        actor = body.userData
        self.destroying.add(actor)

    def draw_circle(self):
        glCallList(self.circle_display_list)

    def _draw_circle(self):
        triangle_count = 256
        glBegin(GL_TRIANGLE_FAN)
        glNormal3d(0, 0, 1)
        glVertex2d(0, 0)
        for i in xrange(triangle_count + 1):
            angle = 2 * pi * i / triangle_count
            glNormal3d(cos(angle), sin(angle), 0)
            glVertex2d(cos(angle), sin(angle))
        glEnd()
        glBegin(GL_LINE_STRIP)
        for i in xrange(triangle_count + 1):
            angle = 2 * pi * i / triangle_count
            glNormal3d(cos(angle), sin(angle), 0)
            glVertex2d(cos(angle), sin(angle))
        glEnd()

    def parse_element_data(self, element):
        data = {}
        for name in ('style', 'inkscape:label'):
            value = element.getAttribute(name)
            data.update(parse_style(value))
        return data
    
class CannonballContactListener(b2ContactListener):
    def __init__(self, level):
        super(CannonballContactListener, self).__init__() 
        self.level = level

    def Add(self, point):
        self.level.add_contact(point)

    def Persist(self, point):
        self.level.persist_contact(point)

    def Remove(self, point):
        self.level.remove_contact(point)

    def Result(self, point):
        self.level.contact_result(point)

class CannonballBoundaryListener(b2BoundaryListener):
    def __init__(self, level):
        super(CannonballBoundaryListener, self).__init__()
        self.level = level

    def Violation(self, body):
        self.level.boundary_violation(body)

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
    data = level.parse_element_data(node)
    actor_name = data.get('actor')
    if actor_name:
        module_name, class_name = actor_name.rsplit('.', 1)
        __import__(module_name)
        module = sys.modules[module_name]
        cls = getattr(module, class_name)
        actor = cls(level)
    else:
        actor = Actor(level)
    actor.id = node.getAttribute('id')
    level.actors[actor.id] = actor
    actor.load(node, transform)
