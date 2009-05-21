from Box2D import *
from pyglet.gl import *
import random
from cannonball.agent import Agent

class JetParticle(Agent):
    color = 1, 1, 1
    radius = 3

    def create_body(self, position, linear_velocity):
        self.level.queue_destroy(self, 0.5 + 0.5 * random.random())
        
        body_def = b2BodyDef()
        body_def.position = position
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.body.linearVelocity = linear_velocity
        self.create_shapes()
        self.body.SetMassFromShapes()

    def create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 0.1
        shape_def.density = 100
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 1, 1)})

    def draw_geometry(self):
        glColor3d(*self.color)
        texture = self.level.textures['particle']
        glEnable(texture.target)
        glBindTexture(texture.target, texture.id)
        glBegin(GL_QUADS)
        for x, y in [(0, 0), (1, 0), (1, 1), (0, 1)]:
            glTexCoord2d(x, y)
            glVertex2d(self.radius * (x - 0.5), self.radius * (y - 0.5))
        glEnd()
        glDisable(texture.target)
