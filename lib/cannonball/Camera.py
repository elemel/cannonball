from __future__ import division

import pyglet
import math
from pyglet.gl import *
from Box2D import *

class Camera(object):
    min_scale = 10
    max_scale = 50

    def __init__(self, window, level, textures):
        self.window = window
        self.level = level
        self.textures = textures
        
        self.position = 0, 0
        self.scale = 20
        
        self.zooming_in = False
        self.zooming_out = False

        self.circle_display_list = glGenLists(1)
        glNewList(self.circle_display_list, GL_COMPILE)
        self.draw_circle(256)
        glEndList()

    def step(self, dt):
        if self.zooming_in:
            self.scale *= 10 ** dt
        if self.zooming_out:
            self.scale /= 10 ** dt
 
        self.scale = max(self.scale, self.min_scale)
        self.scale = min(self.scale, self.max_scale)

        cannonball = self.level.agents.get('cannonball')
        if cannonball:
            self.position = cannonball.body.position.tuple()

    def draw(self):
        x, y = self.position

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.window.width / self.window.height
        height = 30
        width = aspect_ratio * height
        min_x = x - width / 2
        min_y = y - height / 2
        max_x = x + width / 2
        max_y = y + height / 2
        world_aabb = self.level.world.GetWorldAABB()
        if min_x < world_aabb.lowerBound.x:
            max_x += world_aabb.lowerBound.x - min_x
            min_x = world_aabb.lowerBound.x
        elif max_x > world_aabb.upperBound.x:
            min_x -= max_x - world_aabb.upperBound.x
            max_x = world_aabb.upperBound.x
        if min_y < world_aabb.lowerBound.y:
            max_y += world_aabb.lowerBound.y - min_y
            min_y = world_aabb.lowerBound.y
        elif max_y > world_aabb.upperBound.y:
            min_y -= max_y - world_aabb.upperBound.y
            max_y = world_aabb.upperBound.y

        glOrtho(min_x, max_x, min_y, max_y, -1, 1)
        glMatrixMode(GL_MODELVIEW)

        query_aabb = b2AABB()
        query_aabb.lowerBound = min_x, min_y
        query_aabb.upperBound = max_x, max_y
        count, shapes = self.level.world.Query(query_aabb, 1000)
        agents = set(s.GetBody().userData for s in shapes)
        for agent in agents:
            self.draw_agent(agent)

    def draw_agent(self, agent):
        glPushMatrix()
        p = agent.body.GetPosition()
        a = agent.body.GetAngle()
        glTranslated(p.x, p.y, 0)
        glRotated(a * 180 / math.pi, 0, 0, 1)
        if agent.display_list is None:
            agent.display_list = glGenLists(1)
            glNewList(agent.display_list, GL_COMPILE)
            for shape in agent.body.shapeList:
                self.draw_shape(shape)
            glEndList()
        glCallList(agent.display_list)
        if agent.id == 'cannonball':
            glPushMatrix()
            if agent.cannon:
                color = agent.cannon.color
            else:
                color = 0.5, 0.5, 0.5
            glColor3d(*color)
            glTranslated(0.5, 0, 0)
            glScaled(0.5, 0.5, 1)
            glCallList(self.circle_display_list)
            glPopMatrix()
        glPopMatrix()

    def draw_shape(self, shape):
        data = shape.GetUserData() or {}
        material = shape.GetUserData().get('material')
        if material:
            material_obj = self.level.materials[material]
            texture = self.textures[material_obj.texture]
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
            glCallList(self.circle_display_list)
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

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.PLUS:
            self.zooming_in = True
        if symbol == pyglet.window.key.MINUS:
            self.zooming_out = True

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.PLUS:
            self.zooming_in = False
        if symbol == pyglet.window.key.MINUS:
            self.zooming_out = False
