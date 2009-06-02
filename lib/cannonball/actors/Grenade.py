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
            self._create_shock_wave(1, 50)
            self._create_shock_wave(2, 50)
            for _ in xrange(10):
                self._create_smoke()

    def _create_body(self, position, linear_velocity):
        body_def = b2BodyDef()
        body_def.position = position
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.body.linearVelocity = linear_velocity
        self._create_shapes()
        self.body.SetMassFromShapes()

    def _create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 0.3
        shape_def.density = 2
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

    def _create_shock_wave(self, radius, impulse):
        aabb = b2AABB()
        aabb.lowerBound = self.body.position - b2Vec2(radius, radius)
        aabb.upperBound = self.body.position + b2Vec2(radius, radius)
        count, shapes = self.level.world.Query(aabb, 1000)
        bodies = set(s.GetBody() for s in shapes)
        for body in bodies:
            unit = body.GetWorldCenter() - self.body.position
            unit.Normalize()
            body.ApplyImpulse(unit * impulse, body.GetWorldCenter())

    def _create_smoke(self):
        smoke = Smoke(self.level, self.body.position, self.body.linearVelocity)
        impulse = 3 * b2Vec2(random.random() - 0.5, random.random() - 0.5)
        smoke.body.ApplyImpulse(impulse, smoke.body.position)
