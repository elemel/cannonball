from cannonball.Actor import Actor

from Box2D import *

import math
import random

class ChainGunUpgrade(Actor):
    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.add_cannon('ChainGun', ChainGun(other))

class ChainGun(object):
    color = 1, 0.5, 0

    def __init__(self, cannonball):
        self.cannonball = cannonball

    def step(self, dt):
        if self.cannonball.firing and self.cannonball.cannon is self:
            self.cannonball.firing = False
            self.toggle_chain()

    def toggle_chain(self):
        pass
