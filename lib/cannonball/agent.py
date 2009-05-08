from Box2D import *
import random

class Agent(object):
    def __init__(self):
        self.id = None
        self.body = None
        
    def collide(self, other):
        pass

class Grenade(Agent):
    def __init__(self, level):
        super(Grenade, self).__init__()
        self.level = level

    def collide(self, other):
        if not self in self.level.destroying:
            self.level.destroying.add(self)
            for _ in xrange(20):
                self.create_shrapnel()

    def create_shrapnel(self):
        agent = Agent()
        self.level.queue_destroy(agent, 0.5 + 0.5 * random.random())
        
        body_def = b2BodyDef()
        body_def.position = self.body.position
        agent.body = self.level.world.CreateBody(body_def)
        agent.body.userData = agent
        agent.body.linearVelocity = (100 * (random.random() - 0.5),
                                     100 * (random.random() - 0.5))
                                     
        shape_def = b2CircleDef()
        shape_def.radius = 0.1
        shape_def.density = 1000
        shape_def.restitution = 0.5
        shape = agent.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

        agent.body.SetMassFromShapes()
