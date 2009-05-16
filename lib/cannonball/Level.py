from cannonball.material import *

import pyglet

class Level(object):
    def __init__(self, world):
        self.world = world
        self.agents = {}
        self.agent_factories = {}
        self.background_color = 0, 0, 0
        self.materials = dict(stone=Stone(), metal=Metal())
        self.destroying = set()

    def queue_destroy(self, agent, delay):
        def destroy(dt):
            self.destroying.add(agent)
        pyglet.clock.schedule_once(destroy, delay)
