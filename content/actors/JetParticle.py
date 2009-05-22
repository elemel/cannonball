from cannonball.Actor import Actor

from Box2D import *
from pyglet.gl import *

import random

class JetParticle(Actor):
    z = 0.1

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

    def create_body(self, position, linear_velocity):
        self.creation_time = self.level.time
        self.destruction_time = self.level.time + 1 + random.random()
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
        shape_def.radius = 0.1
        shape_def.density = 100
        shape_def.restitution = 0.1
        shape_def.filter.groupIndex = -1
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 1, 1)})

    def draw(self):
        super(JetParticle, self).draw()
        self.dirty_display_list = True

    def draw_geometry(self):
        glColor4d(*self.color)
        texture = self.level.textures['particle']
        glEnable(texture.target)
        glBindTexture(texture.target, texture.id)
        glBegin(GL_QUADS)
        for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]:
            glTexCoord2d(x, y)
            glVertex2d(self.radius * (2 * x - 1), self.radius * (2 * y - 1))
        glEnd()
        glDisable(texture.target)
