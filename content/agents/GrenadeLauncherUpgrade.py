from Box2D import *
import math
import random
from cannonball.agent import Agent

class GrenadeLauncherUpgrade(Agent):
    def __init__(self, level):
        super(GrenadeLauncherUpgrade, self).__init__()
        self.level = level

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

    def create_grenade(self):
        level = self.cannonball.level
        angle = self.cannonball.body.angle
        unit = b2Vec2(math.cos(angle), math.sin(angle))
        position = self.cannonball.body.position
        linear_velocity = self.cannonball.body.linearVelocity + 15 * unit
        grenade_factory = level.agent_factories['Grenade']
        grenade = grenade_factory(level)
        grenade.create_body(position, linear_velocity)
