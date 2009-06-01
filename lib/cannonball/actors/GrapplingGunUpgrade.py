from cannonball.Actor import Actor

from Box2D import *
from pyglet.gl import *

from math import *
import random

class GrapplingGunUpgrade(Actor):
    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            if 'GrapplingGun' in other.cannon_dict:
                other.cannon_dict['GrapplingGun'].max_distance += 10
            else:
                other.add_cannon('GrapplingGun', GrapplingGun(other))

class GrapplingGun(object):
    color = 0, 1, 0
    min_distance = 2
    max_distance = 15
    spring_constant = 1000
    linear_damping = 100
    reel_radius = 1

    def __init__(self, cannonball):
        self.cannonball = cannonball
        self.anchor = None
        self.distance = 0
        self.angle = 0

    def step(self, dt):
        if self.cannonball.firing and self.cannonball.cannon is self:
            if self.anchor is None:
                self.create_chain()
        else:
            self.anchor = None
        if self.anchor:
            body = self.cannonball.body
            delta_angle = body.GetAngle() - self.angle
            if delta_angle < -pi:
                delta_angle += 2 * pi
            elif delta_angle > pi:
                delta_angle -= 2 * pi
            self.distance += self.reel_radius * delta_angle
            self.distance = max(self.distance, self.min_distance)
            self.distance = min(self.distance, self.max_distance)
            self.angle = body.GetAngle()
            local_anchor = body.position
            v = self.anchor - local_anchor
            distance = v.Normalize() - self.distance
            if distance > 0:
                body.ApplyForce(v * distance * self.spring_constant -
                                v * b2Dot(v, body.GetLinearVelocity()) *
                                self.linear_damping,
                                local_anchor)

    def draw(self):
        if self.anchor is not None:
            glColor3d(0, 1, 0)
            glNormal3d(0, 0, 1)
            glBegin(GL_LINES)
            glVertex2d(*self.cannonball.body.position.tuple())
            glVertex2d(*self.anchor.tuple())
            glEnd()

    def create_chain(self):
        angle = self.cannonball.body.angle
        unit = b2Vec2(cos(angle), sin(angle))
        segment = b2Segment()
        segment.p1 = self.cannonball.body.position
        segment.p2 = segment.p1 + self.max_distance * unit
        world = self.cannonball.level.world
        fraction, normal, shape = world.RaycastOne(segment, False, None)
        if (shape is not None and not shape.IsSensor() and
            shape.GetBody().IsStatic()):
            self.anchor = segment.p1 + fraction * (segment.p2 - segment.p1)
            self.distance = (self.anchor - segment.p1).Length()
            self.angle = angle
