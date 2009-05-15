from Box2D import *
import random
from cannonball.agent import Agent

class GrenadeParticle(Agent):
    def __init__(self, level):
        super(GrenadeParticle, self).__init__()
        self.level = level

    def create_body(self, position):
        self.level.queue_destroy(self, 0.5 + 0.5 * random.random())
        
        body_def = b2BodyDef()
        body_def.position = position
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.body.linearVelocity = (100 * (random.random() - 0.5),
                                    100 * (random.random() - 0.5))
        self.create_shapes()
        self.body.SetMassFromShapes()

    def create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 0.1
        shape_def.density = 1000
        shape_def.restitution = 0.5
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})
