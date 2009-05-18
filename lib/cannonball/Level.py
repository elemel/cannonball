from cannonball.material import *

import pyglet
from pyglet.gl import *
from Box2D import *

class Level(object):
    def __init__(self, world):
        self.world = world
        self.agents = {}
        self.agent_factories = {}
        self.background_color = 0, 0, 0
        self.materials = dict(stone=Stone(), metal=Metal())
        self.destroying = set()

        self.contacts = set()
        self.contact_listener = CannonballContactListener(self)
        self.world.SetContactListener(self.contact_listener)

        self.boundary_listener = CannonballBoundaryListener(self)
        self.world.SetBoundaryListener(self.boundary_listener)
    
    def step(self, dt):
        cannonball = self.agents.get('cannonball')
        if cannonball:
            cannonball.step(dt)

        velocityIterations = 10
        positionIterations = 8
        self.contacts.clear()
        self.world.Step(dt, velocityIterations, positionIterations)
        for agent_1, agent_2 in self.contacts:
            agent_1.collide(agent_2)
            agent_2.collide(agent_1)
        for agent in self.destroying:
            if agent.body:
                self.world.DestroyBody(agent.body)
                agent.body = None
                if agent.id:
                    del self.agents[agent.id]
            if agent.display_list is not None:
                glDeleteLists(agent.display_list, 1)
                agent.display_list = None
        self.destroying.clear()

    def queue_destroy(self, agent, delay):
        def destroy(dt):
            self.destroying.add(agent)
        pyglet.clock.schedule_once(destroy, delay)

    def add_contact(self, point):
        agent_1 = point.shape1.GetBody().GetUserData()
        agent_2 = point.shape2.GetBody().GetUserData()
        if agent_1 and agent_2:
            self.contacts.add((agent_1, agent_2))

class CannonballContactListener(b2ContactListener):
    def __init__(self, level):
        super(CannonballContactListener, self).__init__() 
        self.level = level

    def Add(self, point):
        self.level.add_contact(point)

    def Persist(self, point):
        pass

    def Remove(self, point):
        pass

    def Result(self, point):
        pass

class CannonballBoundaryListener(b2BoundaryListener):
    def __init__(self, level):
        super(CannonballBoundaryListener, self).__init__()
        self.level = level

    def Violation(self, body):
        agent = body.userData
        self.level.destroying.add(agent)
