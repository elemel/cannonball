from cannonball.Actor import Actor

from Box2D import *

import random

class Goal(Actor):
    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.won = True
