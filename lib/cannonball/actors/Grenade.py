from cannonball.actors.GrenadeParticle import GrenadeParticle
from cannonball.actors.Smoke import Smoke
from cannonball.Actor import Actor

from Box2D import *

import random

class Grenade(Actor):
    z = 0.1
    
    def __init__(self, level, position, linear_velocity):
        super(Grenade, self).__init__(level)
        self._create_body(position, linear_velocity)

    def collide(self, other):
        if not self in self.level.destroying:
            self.level.destroying.add(self)
            for _ in xrange(20):
                self.create_grenade_particle()
            for _ in xrange(10):
                self.create_smoke()

    def _create_body(self, position, linear_velocity):
        body_def = b2BodyDef()
        body_def.position = position
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.body.linearVelocity = linear_velocity
        self.create_shapes()
        self.body.SetMassFromShapes()

    def create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 0.3
        shape_def.density = 2
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

    def create_grenade_particle(self):
        actor = GrenadeParticle(self.level)
        actor.create_body(self.body.position, self.body.linearVelocity)

    def create_smoke(self):
        linear_velocity = b2Vec2(random.random() - 0.5,
                                 random.random() - 0.5)
        actor = Smoke(self.level, self.body.position, linear_velocity)
