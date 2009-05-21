from Box2D import *
from pyglet.gl import *
import random
from cannonball.agent import Agent

class GrenadeParticle(Agent):
    color = 1, 0, 0
    radius = 1

    def create_body(self, position):
        self.level.queue_destroy(self, 0.5 + 0.5 * random.random())
        
        body_def = b2BodyDef()
        body_def.position = position
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.body.linearVelocity = (50 * (random.random() - 0.5),
                                    50 * (random.random() - 0.5))
        self.create_shapes()
        self.body.SetMassFromShapes()

    def create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 0.1
        shape_def.density = 1000
        shape_def.restitution = 0.5
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

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
