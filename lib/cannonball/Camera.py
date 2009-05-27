from __future__ import division

from Box2D import *
import pyglet
from pyglet.gl import *

import math
from operator import attrgetter

class Camera(object):
    min_scale = 10
    max_scale = 50

    def __init__(self, window, level):
        self.window = window
        self.level = level
        
        self.position = 0, 0
        self.scale = 20
        
        self.zooming_in = False
        self.zooming_out = False

    def step(self, dt):
        if self.zooming_in:
            self.scale *= 10 ** dt
        if self.zooming_out:
            self.scale /= 10 ** dt
 
        self.scale = max(self.scale, self.min_scale)
        self.scale = min(self.scale, self.max_scale)

        cannonball = self.level.actors.get('cannonball')
        if cannonball:
            self.position = cannonball.body.position.tuple()

    def draw(self):
        x, y = self.position

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

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(min_x, max_x, min_y, max_y, -1, 1)
        glMatrixMode(GL_MODELVIEW)

        self.draw_background(min_x, min_y, max_x, max_y)

        query_aabb = b2AABB()
        query_aabb.lowerBound = min_x, min_y
        query_aabb.upperBound = max_x, max_y
        count, shapes = self.level.world.Query(query_aabb, 1000)
        actors = set(s.GetBody().userData for s in shapes)
        for actor in sorted(actors, key=attrgetter('z')):
            glNormal3d(0, 0, 1)
            actor.draw()

    def draw_background(self, min_x, min_y, max_x, max_y):
        if self.level.background:
            world_aabb = self.level.world.GetWorldAABB()
            world_width = world_aabb.upperBound.x
            world_height = world_aabb.upperBound.y
            world_ratio = world_width / world_height
            weight = 0.2

            glDisable(GL_LIGHTING)
            glEnable(self.level.background.target)
            glBindTexture(self.level.background.target,
                          self.level.background.id)

            glColor3d(1, 1, 1)
            glBegin(GL_QUADS)
            glTexCoord2d(0, 0)
            glVertex2d(min_x / (weight + 1), min_y / (weight + 1))
            glTexCoord2d(0, min(1, 1 / world_ratio))
            glVertex2d(min_x / (weight + 1),
                       (max_y + weight * world_height) / (weight + 1))
            glTexCoord2d(min(1, world_ratio), min(1, 1 / world_ratio))
            glVertex2d((max_x + weight * world_width) / (weight + 1),
                       (max_y + weight * world_height) / (weight + 1))
            glTexCoord2d(min(1, world_ratio), 0)
            glVertex2d((max_x + weight * world_width) / (weight + 1),
                       min_y / (weight + 1))
            glEnd()
            glDisable(self.level.background.target)
            glEnable(GL_LIGHTING)

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
