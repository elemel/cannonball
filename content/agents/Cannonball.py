from Box2D import *
import random
from cannonball.agent import Agent
from cannonball.cannon import *

def sign(x):
    return x / abs(x) if x else 0

class Cannonball(Agent):
    max_angular_velocity = 15
    max_angular_acceleration = 10

    def __init__(self, level):
        super(Cannonball, self).__init__()
        self.level = level
        self.id = 'cannonball'
        self.level.agents[self.id] = self
        self.won = False
        self.lost = False

        self.cannon_factories = [GrenadeLauncher]
        self.cannon_index = 0
        self.cannon = self.cannon_factories[self.cannon_index]()

        self.rolling_left = False
        self.rolling_right = False
        self.switching_cannon = False
        self.firing = False

    def step(self, dt):
        av = self.body.angularVelocity
        roll = self.rolling_left - self.rolling_right
        if roll:
            av += roll * self.max_angular_acceleration * dt
            av = sign(av) * min(abs(av), self.max_angular_velocity)
        elif av:
            av = sign(av) * max(abs(av) - self.max_angular_acceleration * dt,
                                0)
        self.body.angularVelocity = av
        self.body.WakeUp()

        if self.switching_cannon:
            self.switching_cannon = False
            self.switch_cannon()
        if self.firing:
            self.cannon.fire(self, self.level)

    def switch_cannon(self):
        if len(self.cannon_factories) >= 2:
            self.cannon_index += 1
            self.cannon_index %= len(self.cannon_factories)
            self.cannon = self.cannon_factories[self.cannon_index]()

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
