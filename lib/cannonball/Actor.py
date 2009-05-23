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
        texture_name = data.get('texture')
        if texture_name:
            texture = self.level.textures[texture_name]
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
            self.level.draw_circle()
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

