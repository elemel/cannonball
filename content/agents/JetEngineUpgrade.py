from Box2D import *
import random
from cannonball.agent import Agent
from cannonball.cannon import *

class JetEngineUpgrade(Agent):
    def __init__(self, level):
        super(JetEngineUpgrade, self).__init__()
        self.level = level

    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.cannon_factories.append(JetEngine)
