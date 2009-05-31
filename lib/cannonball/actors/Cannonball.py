from cannonball.Actor import Actor

from Box2D import *
import pyglet
from pyglet.gl import *

import random

def sign(x):
    return x / abs(x) if x else 0

class Cannonball(Actor):
    max_angular_velocity = 15
    max_angular_acceleration = 10

    def __init__(self, level):
        super(Cannonball, self).__init__(level)
        self.id = 'cannonball'
        self.level.actors[self.id] = self
        self.won = False
        self.lost = False

        self.cannon_dict = {}
        self.cannon_list = []
        self.cannon_index = 0

        self.rolling_left = False
        self.rolling_right = False
        self.switching_cannon = False
        self.firing = False

    def step(self, dt):
        av = self.body.angularVelocity
        roll = self.rolling_left - self.rolling_right
        if roll:
            av += roll * self.max_angular_acceleration * dt
            av = sign(av) * min(abs(av), self.max_angular_velocity)
        elif av:
            av = sign(av) * max(abs(av) - self.max_angular_acceleration * dt,
                                0)
        self.body.angularVelocity = av
        self.body.WakeUp()

        if self.switching_cannon:
            self.switching_cannon = False
            self.switch_cannon()
        for cannon in self.cannon_list:
            cannon.step(dt)

    def draw(self):
        for cannon in self.cannon_list:
            cannon.draw()
        super(Cannonball, self).draw()

    def draw_geometry(self):
        super(Cannonball, self).draw_geometry()
        glPushMatrix()
        if self.cannon:
            color = self.cannon.color
        else:
            color = 0.5, 0.5, 0.5
        glColor3d(*color)
        glTranslated(0.5, 0, 0)
        glScaled(0.5, 0.5, 1)
        self.level.draw_circle()
        glPopMatrix()

    @property
    def cannon(self):
        if self.cannon_list:
            return self.cannon_list[self.cannon_index]
        else:
            return None

    def add_cannon(self, name, cannon):
        self.cannon_dict[name] = cannon
        self.cannon_list.append(cannon)
        self.dirty_display_list = True

    def switch_cannon(self):
        if self.cannon_list:
            self.cannon_index = (self.cannon_index + 1) % len(self.cannon_list)
            self.dirty_display_list = True

    def create_body(self, position):
        body_def = b2BodyDef()
        body_def.position = position
        self.body = self.level.world.CreateBody(body_def)
        self.body.userData = self
        self.create_shapes()
        self.body.SetMassFromShapes()
        massData = self.body.massData
        massData.I = 1e9
        self.body.massData = massData

    def create_shapes(self):
        shape_def = b2CircleDef()
        shape_def.radius = 1
        shape_def.density = 2
        shape_def.friction = 5
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = self.body.CreateShape(shape_def)
        shape.SetUserData({'color': (0.3, 0.3, 0.3)})

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.LEFT:
            self.rolling_left = True
        if symbol == pyglet.window.key.RIGHT:
            self.rolling_right = True
        if symbol == pyglet.window.key.TAB:
            self.switching_cannon = True
        if symbol == pyglet.window.key.SPACE:
            self.firing = True

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.LEFT:
            self.rolling_left = False
        if symbol == pyglet.window.key.RIGHT:
            self.rolling_right = False
        if symbol == pyglet.window.key.SPACE:
            self.firing = False
