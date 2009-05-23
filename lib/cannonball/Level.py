import pyglet
from pyglet.gl import *
from Box2D import *
from math import cos, pi, sin

class Level(object):
    def __init__(self, world):
        self.world = world
        self.time = 0
        self.actors = {}        
        self.actor_factories = {}
        self.background_color = 0, 0, 0
        self.textures = {}
        self.destroying = set()

        self.contacts = set()
        self.contact_listener = CannonballContactListener(self)
        self.world.SetContactListener(self.contact_listener)

        self.boundary_listener = CannonballBoundaryListener(self)
        self.world.SetBoundaryListener(self.boundary_listener)

        self.circle_display_list = glGenLists(1)
        glNewList(self.circle_display_list, GL_COMPILE)
        self._draw_circle()
        glEndList()

    def step(self, dt):
        self.time += dt
        cannonball = self.actors.get('cannonball')
        if cannonball:
            cannonball.step(dt)

        velocityIterations = 10
        positionIterations = 8
        self.contacts.clear()
        self.world.Step(dt, velocityIterations, positionIterations)
        for actor_1, actor_2 in self.contacts:
            actor_1.collide(actor_2)
            actor_2.collide(actor_1)
        for actor in self.destroying:
            if actor.body:
                self.world.DestroyBody(actor.body)
                actor.body = None
                if actor.id:
                    del self.actors[actor.id]
            if actor.display_list is not None:
                glDeleteLists(actor.display_list, 1)
                actor.display_list = None
        self.destroying.clear()

    def queue_destroy(self, actor, delay):
        def destroy(dt):
            self.destroying.add(actor)
        pyglet.clock.schedule_once(destroy, delay)

    def add_contact(self, point):
        actor_1 = point.shape1.GetBody().GetUserData()
        actor_2 = point.shape2.GetBody().GetUserData()
        if actor_1 and actor_2:
            self.contacts.add((actor_1, actor_2))

    def draw_circle(self):
        glCallList(self.circle_display_list)

    def _draw_circle(self):
        triangle_count = 256
        glBegin(GL_TRIANGLE_FAN)
        glNormal3d(0, 0, 1)
        glVertex2d(0, 0)
        for i in xrange(triangle_count + 1):
            angle = 2 * pi * i / triangle_count
            glNormal3d(cos(angle), sin(angle), 0)
            glVertex2d(cos(angle), sin(angle))
        glEnd()
        glBegin(GL_LINE_STRIP)
        for i in xrange(triangle_count + 1):
            angle = 2 * pi * i / triangle_count
            glNormal3d(cos(angle), sin(angle), 0)
            glVertex2d(cos(angle), sin(angle))
        glEnd()

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
        actor = body.userData
        self.level.destroying.add(actor)
