from cannonball.Actor import Actor
from cannonball.actors.Smoke import Smoke

from Box2D import *

from math import *
import random
import time

class JetEngineUpgrade(Actor):
    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            if 'JetEngine' not in other.cannon_dict:
                other.add_cannon('JetEngine', JetEngine(other))

class JetEngine(object):
    max_cooldown = 0.01
    color = 1, 1, 1

    def __init__(self, cannonball):
        self.cannonball = cannonball
        self.cooldown = 0

    def step(self, dt):
        self.cooldown -= dt
        if self.cannonball.firing and self.cannonball.cannon is self:
            while self.cooldown <= 0:
                self.cooldown += self.max_cooldown
                self.create_smoke()
        self.cooldown = max(self.cooldown, 0)

    def draw(self):
        pass

    def create_smoke(self):
        level = self.cannonball.level
        angle = self.cannonball.body.angle
        unit = b2Vec2(cos(angle), sin(angle))
        position = self.cannonball.body.position + 0.5 * unit
        linear_velocity = self.cannonball.body.linearVelocity
        smoke = Smoke(level, position, linear_velocity)
        impulse = 2 * (unit + b2Vec2(random.random() - 0.5,
                                     random.random() - 0.5))
        smoke.body.ApplyImpulse(impulse, smoke.body.position)
        self.cannonball.body.ApplyImpulse(-impulse,
                                          self.cannonball.body.position)
