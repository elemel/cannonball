from Box2D import *
from pyglet.gl import *
import math
import random

class Agent(object):
    def __init__(self, level):
        self.level = level
        self.id = None
        self.body = None
        self.display_list = None
        
    def collide(self, other):
        pass

    def draw(self):
        glPushMatrix()
        p = self.body.GetPosition()
        a = self.body.GetAngle()
        glTranslated(p.x, p.y, 0)
        glRotated(a * 180 / math.pi, 0, 0, 1)
        if self.display_list is None:
            self.display_list = glGenLists(1)
            glNewList(self.display_list, GL_COMPILE)
            for shape in self.body.shapeList:
                self.draw_shape(shape)
            glEndList()
        glCallList(self.display_list)
        if self.id == 'cannonball':
            glPushMatrix()
            if self.cannon:
                color = self.cannon.color
            else:
                color = 0.5, 0.5, 0.5
            glColor3d(*color)
            glTranslated(0.5, 0, 0)
            glScaled(0.5, 0.5, 1)
            self.draw_circle(32)
            glPopMatrix()
        glPopMatrix()

    def draw_shape(self, shape):
        data = shape.GetUserData() or {}
        material = shape.GetUserData().get('material')
        if material:
            material_obj = self.level.materials[material]
            texture = self.level.textures[material_obj.texture]
            glColor3d(1, 1, 1)
        else:
            texture = None
            color = data.get('color', (1, 1, 1))
            glColor3d(*color)
        polygon = shape.asPolygon()
        circle = shape.asCircle()
        if polygon:
            self.draw_polygon(polygon, texture)
        elif circle:
            glPushMatrix()
            p = circle.localPosition
            glTranslated(p.x, p.y, 0)
            glScaled(circle.radius, circle.radius, 1)
            self.draw_circle(128)
            glPopMatrix()

    def draw_polygon(self, polygon, texture):
        if texture:
            glEnable(texture.target)
            glBindTexture(texture.target, texture.id)
        vertices = list(polygon.vertices)
        vertices.append(vertices[0])
        glBegin(GL_POLYGON)
        for x, y in vertices:
            if texture:
                glTexCoord2d(x * 0.1, y * 0.1)
            glVertex2d(x, y)
        glEnd()
        glBegin(GL_LINE_STRIP)
        for x, y in vertices:
            if texture:
                glTexCoord2d(x * 0.1, y * 0.1)
            glVertex2d(x, y)
        glEnd()
        if texture:
            glDisable(texture.target)

    def draw_circle(self, triangle_count):
        glBegin(GL_POLYGON)
        for i in xrange(triangle_count + 1):
            a = 2 * math.pi * i / triangle_count
            glVertex2d(math.cos(a), math.sin(a))
        glEnd()
        glBegin(GL_LINE_STRIP)
        for i in xrange(triangle_count + 1):
            a = 2 * math.pi * i / triangle_count
            glVertex2d(math.cos(a), math.sin(a))
        glEnd()

