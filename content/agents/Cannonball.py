from Box2D import *
import random
from cannonball.agent import Agent

class Cannonball(Agent):
    def __init__(self, level):
        super(Cannonball, self).__init__()
        self.level = level
        self.id = 'cannonball'
        self.level.agents[self.id] = self

    def create_body(self, position):
        body_def = b2BodyDef()
        body_def.position = position
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.create_shapes()
        self.body.SetMassFromShapes()
        massData = self.body.massData
        massData.I = 1e9
        self.body.massData = massData

    def create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 1
        shape_def.density = 100
        shape_def.friction = 5
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (0, 0, 0)})
