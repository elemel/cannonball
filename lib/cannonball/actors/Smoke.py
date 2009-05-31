from cannonball.Actor import Actor

from Box2D import *
from pyglet.gl import *

import random

class Smoke(Actor):
    z = 0.1

    def __init__(self, level, position, linear_velocity):
        super(Smoke, self).__init__(level)
        self._create_body(position, linear_velocity)
    
    @property
    def progress(self):
        return ((self.level.time - self.creation_time) /
                (self.destruction_time - self.creation_time))

    @property
    def radius(self):
        return 1 + 5 * self.progress

    @property
    def color(self):
        return 1, 1, 1, 1 - self.progress

    def _create_body(self, position, linear_velocity):
        self.creation_time = self.level.time
        self.destruction_time = self.level.time + 0.5 + 0.5 * random.random()
        self.level.queue_destroy(self, self.destruction_time -
                                 self.creation_time)
        
        body_def = b2BodyDef()
        body_def.position = position
        body_def.linearDamping = 2
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.body.linearVelocity = linear_velocity
        self.create_shapes()
        self.body.SetMassFromShapes()

    def create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 0.2
        shape_def.density = 1
        shape_def.restitution = 0.1
        shape_def.filter.groupIndex = -1
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 1, 1)})

    def draw(self):
        super(Smoke, self).draw()
        self.dirty_display_list = True

    def draw_geometry(self):
        glColor4d(*self.color)
        texture = self.level.get_texture('../textures/particle.png')
        glEnable(texture.target)
        glBindTexture(texture.target, texture.id)
        glBegin(GL_QUADS)
        for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]:
            glTexCoord2d(x, y)
            glVertex2d(self.radius * (2 * x - 1), self.radius * (2 * y - 1))
        glEnd()
        glDisable(texture.target)
