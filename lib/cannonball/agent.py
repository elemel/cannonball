from Box2D import *
import random

class Agent(object):
    def __init__(self):
        self.id = None
        self.body = None
        self.display_list = None
        
    def collide(self, other):
        pass
