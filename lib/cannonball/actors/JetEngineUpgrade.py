from cannonball.actors.JetParticle import JetParticle
from cannonball.Actor import Actor

from Box2D import *

import math
import random
import time

class JetEngineUpgrade(Actor):
    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.add_cannon('JetEngine', JetEngine(other))

class JetEngine(object):
    max_cooldown = 0.02
    color = 1, 1, 1

    def __init__(self, cannonball):
        self.cannonball = cannonball
        self.cooldown = 0

    def step(self, dt):
        self.cooldown -= dt
        if self.cannonball.firing and self.cannonball.cannon is self:
            while self.cooldown <= 0:
                self.cooldown += self.max_cooldown
                self.create_jet_particle()
        self.cooldown = max(self.cooldown, 0)

    def create_jet_particle(self):
        level = self.cannonball.level
        angle = self.cannonball.body.angle
        unit = b2Vec2(math.cos(angle), math.sin(angle))
        position = self.cannonball.body.position + 0.5 * unit
        linear_velocity = self.cannonball.body.linearVelocity + 10 * unit
        linear_velocity += 10 * b2Vec2(random.random() - 0.5,
                                       random.random() - 0.5)
        actor = JetParticle(level)
        actor.create_body(position, linear_velocity)

        self.cannonball.body.ApplyImpulse(-unit * 200,
                                          self.cannonball.body.GetWorldCenter())
