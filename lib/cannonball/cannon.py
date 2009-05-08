from Box2D import *
import math, time, random
from agent import *

class Cannon(object):
    pass

class GrenadeLauncher(Cannon):
    cooldown = 0.5
    color = 1, 0, 0

    def __init__(self):
        self.min_fire_time = time.time() + self.cooldown

    def fire(self, cannonball, level):
        if self.min_fire_time < time.time():
            a = cannonball.body.angle
            v = b2Vec2(math.cos(a), math.sin(a))
            self.create_grenade(level, cannonball.body.position,
                                cannonball.body.linearVelocity + 15 * v)
            self.min_fire_time = time.time() + self.cooldown

    def create_grenade(self, level, position, velocity):
        grenade = Grenade(level)
        
        body_def = b2BodyDef()
        body_def.position = position
        grenade.body = level.world.CreateBody(body_def)
        grenade.body.userData = grenade
        grenade.body.linearVelocity = velocity

        shape_def = b2CircleDef()
        shape_def.radius = 0.25
        shape_def.density = 200
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = grenade.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

        grenade.body.SetMassFromShapes()

class JetEngine(Cannon):
    color = 1, 1, 1
    cooldown = 0.01

    def __init__(self):
        self.min_fire_time = time.time() + self.cooldown

    def fire(self, cannonball, level):
        while self.min_fire_time < time.time():
            a = cannonball.body.angle
            v = b2Vec2(math.cos(a), math.sin(a))
            cannonball.body.ApplyImpulse(-v * 200,
                                         cannonball.body.GetWorldCenter())
            v += b2Vec2(random.random() - 0.5, random.random() - 0.5)
            v = cannonball.body.linearVelocity + 5 * v
            self.create_jet_particle(level, cannonball.body.position, v)
            self.min_fire_time = time.time() + self.cooldown

    def create_jet_particle(self, level, position, velocity):
        agent = Agent()
        level.queue_destroy(agent, 0.5 + 0.5 * random.random())

        body_def = b2BodyDef()
        body_def.position = position
        agent.body = level.world.CreateBody(body_def)
        agent.body.userData = agent
        agent.body.linearVelocity = velocity

        shape_def = b2CircleDef()
        shape_def.radius = 0.1
        shape_def.density = 100
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = agent.body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 1, 1)})

        agent.body.SetMassFromShapes()
