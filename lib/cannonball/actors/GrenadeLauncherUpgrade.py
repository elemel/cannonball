from cannonball.actors.Grenade import Grenade
from cannonball.Actor import Actor

from Box2D import *

from math import *
import random

class GrenadeLauncherUpgrade(Actor):
    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            if 'GrenadeLauncher' in other.cannon_dict:
                other.cannon_dict['GrenadeLauncher'].max_duration += 1
            else:
                other.add_cannon('GrenadeLauncher', GrenadeLauncher(other))

class GrenadeLauncher(object):
    color = 1, 0, 0
    min_duration = 1
    max_duration = 2

    def __init__(self, cannonball):
        self.cannonball = cannonball
        self.firing = False
        self.fire_time = 0

    def step(self, dt):
        if self.cannonball.cannon is self and self.cannonball.firing:
            if not self.firing:
                self.firing = True
                self.fire_time = self.cannonball.level.time
        elif self.firing:
            self.firing = False
            self.create_grenade(self.cannonball.level.time - self.fire_time)

    def draw(self):
        pass

    def create_grenade(self, duration):
        level = self.cannonball.level
        angle = self.cannonball.body.angle
        unit = b2Vec2(cos(angle), sin(angle))
        position = self.cannonball.body.position + 0.5 * unit
        linear_velocity = self.cannonball.body.linearVelocity
        grenade = Grenade(level, position, linear_velocity)
        impulse = unit * 5 * min(duration + self.min_duration,
                                 self.max_duration)
        grenade.body.ApplyImpulse(impulse, grenade.body.position)
        self.cannonball.body.ApplyImpulse(-impulse,
                                          self.cannonball.body.position)
