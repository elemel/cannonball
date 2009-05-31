from cannonball.Actor import Actor

from Box2D import *
from pyglet.gl import *

from math import *
import random

class GrapplingGunUpgrade(Actor):
    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.add_cannon('GrapplingGun', GrapplingGun(other))

class GrapplingGun(object):
    color = 0, 1, 0

    def __init__(self, cannonball):
        self.cannonball = cannonball
        self.anchor = None
        self.distance = 0

    def step(self, dt):
        if self.cannonball.firing and self.cannonball.cannon is self:
            if self.anchor is None:
                self.create_chain()
        else:
            self.anchor = None
        if self.anchor:
            body = self.cannonball.body
            unit = b2Vec2(cos(body.angle), sin(body.angle))
            local_anchor = body.position + 0.5 * unit
            v = self.anchor - local_anchor
            distance = v.Normalize() - self.distance
            if distance > 0:
                body.ApplyForce(v * distance * 10000 -
                                v * b2Dot(v, body.GetLinearVelocity()) * 1000,
                                local_anchor)

    def draw(self):
        if self.anchor is not None:
            glColor3d(0, 1, 0)
            glNormal3d(0, 0, 1)
            glBegin(GL_LINES)
            angle = self.cannonball.body.angle
            unit = b2Vec2(cos(angle), sin(angle))
            glVertex2d(*(self.cannonball.body.position + 0.5 * unit).tuple())
            glVertex2d(*self.anchor.tuple())
            glEnd()

    def create_chain(self):
        angle = self.cannonball.body.angle
        unit = b2Vec2(cos(angle), sin(angle))
        segment = b2Segment()
        segment.p1 = self.cannonball.body.position + 0.5 * unit
        segment.p2 = segment.p1 + 30 * unit
        world = self.cannonball.level.world
        fraction, normal, shape = world.RaycastOne(segment, False, None)
        if (shape is not None and not shape.IsSensor() and
            shape.GetBody().IsStatic()):
            self.anchor = segment.p1 + fraction * (segment.p2 - segment.p1)
            self.distance = (self.anchor - segment.p1).Length()
