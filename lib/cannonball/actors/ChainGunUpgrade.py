from cannonball.Actor import Actor
from cannonball.actors.Chain import Chain

from Box2D import *

from math import *
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
        self.chain = None

    def step(self, dt):
        if self.cannonball.firing and self.cannonball.cannon is self:
            if self.chain is None:
                self.create_chain()
        else:
            if self.chain is not None:
                self.destroy_chain()

    def create_chain(self):
        angle = self.cannonball.body.angle
        unit = b2Vec2(cos(angle), sin(angle))
        segment = b2Segment()
        segment.p1 = self.cannonball.body.position
        segment.p2 = segment.p1 + 20 * unit
        world = self.cannonball.level.world
        fraction, normal, shape = world.RaycastOne(segment, False, None)
        if shape:
            anchor = segment.p1 + fraction * (segment.p2 - segment.p1)
            self.chain = Chain(self.cannonball.level, self.cannonball,
                               shape.GetBody().userData,
                               self.cannonball.body.position, anchor)

    def destroy_chain(self):
        self.chain.destroy()
        self.chain = None
