from __future__ import division

from cannonball.actors.Cannonball import *
from cannonball.Camera import *
from cannonball.Level import *
from cannonball.svg import *

from Box2D import *
import pyglet
from pyglet.gl import *

import ctypes
import os
import random
import sys

class CannonballWindow(pyglet.window.Window):
    def __init__(self, level):
        self.level = level
        pyglet.window.Window.__init__(self, fullscreen=True,
                                      caption="Cannonball")
        self.set_mouse_visible(False)

        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glEnable(GL_LIGHTING)
        glEnable(GL_NORMALIZE)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        Float3 = ctypes.c_float * 3
        Float4 = ctypes.c_float * 4

        # Set up key light.
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, Float4(-1, 1, 1, 0))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, Float3(1, 1, 1))

        # Set up fill light.
        glEnable(GL_LIGHT1)
        glLightfv(GL_LIGHT1, GL_POSITION, Float4(1, 0, 1, 0))
        glLightfv(GL_LIGHT1, GL_DIFFUSE, Float3(0.2, 0.2, 0.2))

        start = self.level.actors['start']
        start_shapes = start.body.shapeList
        start_position = b2Vec2()
        for shape in start_shapes:
            start_position += shape.GetCentroid()
        start_position *= 1 / len(start_shapes)
        self.create_cannonball(start_position)

        self.camera = Camera(self, self.level)

        self.time = 0
        self.physics_time = 0
        self.physics_dt = 1 / 60 
        pyglet.clock.schedule_interval(self.step, self.physics_dt)

    def step(self, dt):
        self.time += dt
        while self.physics_time + self.physics_dt <= self.time:
            self.physics_time += self.physics_dt
            self.camera.step(self.physics_dt)
            self.level.step(self.physics_dt)
 
            cannonball = self.level.actors.get('cannonball')
            if cannonball and cannonball.won:
                print 'You Win'
                self.on_close()
                break
            elif not cannonball:
                print 'Game Over'
                self.on_close()
                break

    def on_draw(self):
        r, g, b = self.level.background_color
        glClearColor(r, g, b, 1)
        self.clear()
        self.camera.draw()

    def on_close(self):
        self.close()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.on_close()
        self.camera.on_key_press(symbol, modifiers)
        cannonball = self.level.actors.get('cannonball')
        if cannonball:
            cannonball.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.camera.on_key_release(symbol, modifiers)
        cannonball = self.level.actors.get('cannonball')
        if cannonball:
            cannonball.on_key_release(symbol, modifiers)

    def create_cannonball(self, position):
        actor = Cannonball(self.level)
        actor.create_body(position)
 
def main():
    if len(sys.argv) != 2:
        print 'Usage: cannonball <level>'
        sys.exit(1)
    level = Level(sys.argv[1])
    window = CannonballWindow(level)
    pyglet.app.run()

if __name__ == '__main__':
    main()
