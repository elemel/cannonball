from Box2D import *
import math
import random
import time
from cannonball.agent import Agent

class GrenadeLauncherUpgrade(Agent):
    def __init__(self, level):
        super(GrenadeLauncherUpgrade, self).__init__()
        self.level = level

    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.cannon_factories.append(GrenadeLauncher)

class GrenadeLauncher(object):
    cooldown = 0.5
    color = 1, 0, 0

    def __init__(self):
        self.min_fire_time = time.time() + self.cooldown

    def fire(self, cannonball, level):
        if self.min_fire_time < time.time():
            a = cannonball.body.angle
            v = b2Vec2(math.cos(a), math.sin(a))
            self.create_grenade(level, cannonball.body.position,
                                cannonball.body.linearVelocity + 15 * v)
            self.min_fire_time = time.time() + self.cooldown

    def create_grenade(self, level, position, velocity):
        grenade_factory = level.agent_factories['Grenade']
        grenade = grenade_factory(level)
        grenade.create_body(position, velocity)
