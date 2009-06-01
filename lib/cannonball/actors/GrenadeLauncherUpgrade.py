from cannonball.actors.Grenade import Grenade
from cannonball.Actor import Actor

from Box2D import *

from math import *
import random

class GrenadeLauncherUpgrade(Actor):
    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.add_cannon('GrenadeLauncher', GrenadeLauncher(other))

class GrenadeLauncher(object):
    max_cooldown = 0.5
    color = 1, 0, 0

    def __init__(self, cannonball):
        self.cannonball = cannonball
        self.cooldown = 0

    def step(self, dt):
        self.cooldown -= dt
        if self.cannonball.firing and self.cannonball.cannon is self:
            while self.cooldown <= 0:
                self.cooldown += self.max_cooldown
                self.create_grenade()
        self.cooldown = max(self.cooldown, 0)

    def draw(self):
        pass

    def create_grenade(self):
        level = self.cannonball.level
        angle = self.cannonball.body.angle
        unit = b2Vec2(cos(angle), sin(angle))
        position = self.cannonball.body.position + 0.5 * unit
        linear_velocity = self.cannonball.body.linearVelocity
        grenade = Grenade(level, position, linear_velocity)
        impulse = unit * 10
        grenade.body.ApplyImpulse(impulse, grenade.body.position)
        self.cannonball.body.ApplyImpulse(-impulse,
                                          self.cannonball.body.position)
