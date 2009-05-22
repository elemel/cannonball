from Box2D import *
from pyglet.gl import *
import random
from cannonball.agent import Agent

class GrenadeParticle(Agent):
    z = 0.1

    @property
    def progress(self):
        return ((self.level.time - self.creation_time) /
                (self.destruction_time - self.creation_time))

    @property
    def radius(self):
        return 0.5 + 2 * self.progress

    @property
    def color(self):
        return 1, 0, 0, 1 - self.progress

    def create_body(self, position, linear_velocity):
        self.creation_time = self.level.time
        self.destruction_time = self.level.time + 0.5 + 0.5 * random.random()
        self.level.queue_destroy(self, self.destruction_time -
                                 self.creation_time)
        
        body_def = b2BodyDef()
        body_def.position = position
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.body.linearVelocity = (linear_velocity +
                                    100 * b2Vec2(random.random() - 0.5,
                                                 random.random() - 0.5))
        self.create_shapes()
        self.body.SetMassFromShapes()

    def create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 0.1
        shape_def.density = 500
        shape_def.restitution = 0.5
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

    def draw(self):
        super(GrenadeParticle, self).draw()
        if random.random() < 0.1:
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
