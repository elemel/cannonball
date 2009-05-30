from __future__ import division

from cannonball.svg import *

from Box2D import *
from pyglet.gl import *

import math
import random

class Actor(object):
    z = 0

    def __init__(self, level):
        self.level = level
        self.id = None
        self.body = None
        self.display_list = glGenLists(1)
        self.dirty_display_list = True

    def load(self, element, transform):
        body_def = b2BodyDef()
        self.body = self.level.world.CreateBody(body_def)
        self.body.SetUserData(self)
        self.load_shapes(element, transform)
        self.body.SetMassFromShapes()

    def load_shapes(self, element, transform):
        transform = transform * Transform(element.getAttribute('transform'))
        if element.nodeName == 'g':
            for child in node.childNodes:
                if child.nodeName in ('g', 'path'):
                    self.load_shapes(child, transform)
        elif element.nodeName == 'path':
            self.load_shape(element, transform)

    def load_shape(self, element, transform):
        data = self.level.parse_element_data(element)
        color = Color('#ffffff')
        texture = None
        fill = data.get('fill')
        if fill.startswith('#'):
            color = Color(fill)
        elif fill.startswith('url(#') and fill.endswith(')'):
            pattern_id = fill.lstrip('url(#').rstrip(')')
            image_path = get_image_path(element.ownerDocument, pattern_id)
            texture = self.level.get_texture(image_path)
        path = Path(element.getAttribute('d'))
        for subpath in path.subpaths:
            polygon = subpath.linearize()
            polygon = Polygon(transform * v for v in polygon.vertices)
            polygon = polygon.normalize()
            normal_dict = {}
            vertices = list(polygon)
            for i, vertex in enumerate(vertices):
                before = vertex - vertices[(i - 1) % len(vertices)]
                after = vertices[(i + 1) % len(vertices)] - vertex
                normal = (before.perp().norm() + after.perp().norm()).norm()
                normal = Vector(tuple(normal) + (0.001,)).norm()
                normal_dict[vertex] = normal
            for triangle in polygon.triangulate():
                normals = [normal_dict[v] for v in triangle]
                shape_def = b2PolygonDef()
                shape_def.vertices = map(tuple, triangle)
                if data.get('sensor') == 'true':
                    shape_def.isSensor = True
                shape_def.density = float(data.get('density', '0'))
                shape = self.body.CreateShape(shape_def)
                shape.SetUserData(dict(color=tuple(c / 255 for c in color),
                                       texture=texture, normals=normals))

    def collide(self, other):
        pass

    def draw(self):
        glPushMatrix()
        p = self.body.GetPosition()
        a = self.body.GetAngle()
        glTranslated(p.x, p.y, 0)
        glRotated(a * 180 / math.pi, 0, 0, 1)
        if self.dirty_display_list:
            self.dirty_display_list = False
            glNewList(self.display_list, GL_COMPILE_AND_EXECUTE)
            self.draw_geometry()
            glEndList()
        else:
            glCallList(self.display_list)
        glPopMatrix()

    def draw_geometry(self):
        for shape in self.body.shapeList:
            self.draw_shape(shape)

    def draw_shape(self, shape):
        data = shape.GetUserData() or {}
        texture = data.get('texture')
        if texture:
            glColor3d(1, 1, 1)
        else:
            texture = None
            color = data.get('color', (1, 1, 1))
            glColor3d(*color)
        polygon = shape.asPolygon()
        circle = shape.asCircle()
        if polygon:
            self.draw_polygon(polygon, data.get('normals'), texture)
        elif circle:
            glPushMatrix()
            p = circle.localPosition
            glTranslated(p.x, p.y, 0)
            glScaled(circle.radius, circle.radius, 1)
            self.level.draw_circle()
            glPopMatrix()

    def draw_polygon(self, polygon, normals, texture):
        if texture:
            glEnable(texture.target)
            glBindTexture(texture.target, texture.id)
        vertices = list(polygon.vertices)
        vertices.append(vertices[0])
        if not normals:
            normals = [(0, 0, 1)] * len(polygon.vertices)
        else:
            normals = list(normals)
            normals.append(normals[0])
        glBegin(GL_POLYGON)
        for vertex, normal in zip(vertices, normals):
            if texture:
                x, y = vertex
                glTexCoord2d(x * 0.1, y * 0.1)
            glNormal3d(*normal)
            glVertex2d(*vertex)
        glEnd()
        glBegin(GL_LINE_STRIP)
        for vertex, normal in zip(vertices, normals):
            if texture:
                x, y = vertex
                glTexCoord2d(x * 0.1, y * 0.1)
            glNormal3d(*normal)
            glVertex2d(*vertex)
        glEnd()
        if texture:
            glDisable(texture.target)

def get_image_path(document, pattern_id):
    pattern_elements = document.getElementsByTagName('pattern')
    pattern_element = [e for e in pattern_elements
                       if e.getAttribute('id') == pattern_id][0]
    if pattern_element.getAttribute('xlink:href'):
        pattern_id = pattern_element.getAttribute('xlink:href').lstrip('#')
        return get_image_path(document, pattern_id)
    image_elements = pattern_element.getElementsByTagName('image')
    if image_elements:
        return image_elements[0].getAttribute('xlink:href')
    return None
