from __future__ import division

from cannonball.svg import *
from cannonball.cannon import *
from cannonball.content import *
from cannonball import config
from cannonball.Camera import *

import pyglet
import sys
import random
import os
from pyglet.gl import *
from Box2D import *

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

        start = self.level.agents['start']
        start_shapes = start.body.shapeList
        start_position = b2Vec2()
        for shape in start_shapes:
            start_position += shape.GetCentroid()
        start_position *= 1 / len(start_shapes)
        self.create_cannonball(start_position)

        texture_root = os.path.join(config.root, 'content', 'textures')
        textures = load_textures(texture_root)
        self.camera = Camera(self, self.level, textures)

        self.contacts = set()
        self.contact_listener = CannonballContactListener(self)
        self.level.world.SetContactListener(self.contact_listener)

        self.boundary_listener = CannonballBoundaryListener(self)
        self.level.world.SetBoundaryListener(self.boundary_listener)

        self.time = 0
        self.physics_time = 0
        self.physics_dt = 1 / 60 
        pyglet.clock.schedule_interval(self.step, self.physics_dt)

    def step(self, dt):
        self.time += dt
        while self.physics_time + self.physics_dt <= self.time:
            self.physics_time += self.physics_dt
            self.step_physics(self.physics_dt)
    
    def step_physics(self, dt):
        cannonball = self.level.agents.get('cannonball')
        if cannonball:
            cannonball.step(dt)
        self.camera.step(dt)

        velocityIterations = 10
        positionIterations = 8
        self.contacts.clear()
        self.level.world.Step(dt, velocityIterations, positionIterations)
        for agent_1, agent_2 in self.contacts:
            agent_1.collide(agent_2)
            agent_2.collide(agent_1)
        for agent in self.level.destroying:
            if agent.body:
                self.level.world.DestroyBody(agent.body)
                agent.body = None
                if agent.id:
                    del self.level.agents[agent.id]
        self.level.destroying.clear()
        if cannonball and cannonball.won:
            print 'You Win'
            self.on_close()
        elif not cannonball:
            print 'Game Over'
            self.on_close()

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
        cannonball = self.level.agents.get('cannonball')
        if cannonball:
            cannonball.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self.camera.on_key_release(symbol, modifiers)
        cannonball = self.level.agents.get('cannonball')
        if cannonball:
            cannonball.on_key_release(symbol, modifiers)

    def create_cannonball(self, position):
        factory = self.level.agent_factories['Cannonball']
        agent = factory(self.level)
        agent.create_body(position)

    def add_contact(self, point):
        agent_1 = point.shape1.GetBody().GetUserData()
        agent_2 = point.shape2.GetBody().GetUserData()
        if agent_1 and agent_2:
            self.contacts.add((agent_1, agent_2))

class CannonballContactListener(b2ContactListener):
    def __init__(self, window):
        super(CannonballContactListener, self).__init__() 
        self.window = window

    def Add(self, point):
        self.window.add_contact(point)

    def Persist(self, point):
        pass

    def Remove(self, point):
        pass

    def Result(self, point):
        pass

class CannonballBoundaryListener(b2BoundaryListener):
    def __init__(self, window):
        super(CannonballBoundaryListener, self).__init__()
        self.window = window

    def Violation(self, body):
        agent = body.userData
        self.window.level.destroying.add(agent)
 
def main():
    if len(sys.argv) != 2:
        print 'Usage: cannonball <level>'
        sys.exit(1)
    agent_root = os.path.join(config.root, 'content', 'agents')
    agent_factories = load_agent_factories(agent_root)
    level = load_level(sys.argv[1], agent_factories)
    window = CannonballWindow(level)
    pyglet.app.run()

if __name__ == '__main__':
    main()
