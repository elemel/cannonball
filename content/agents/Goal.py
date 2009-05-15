from Box2D import *
import random
from cannonball.agent import Agent

class Goal(Agent):
    def __init__(self, level):
        super(Goal, self).__init__()
        self.level = level

    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.won = True
