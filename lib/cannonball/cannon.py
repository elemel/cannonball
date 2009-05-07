from Box2D import *
import math, time, random

class Cannon(object):
    pass

class GrenadeLauncher(Cannon):
    cooldown = 0.5
    color = 1, 0, 0

    def __init__(self):
        self.min_fire_time = time.time() + self.cooldown

    def fire(self, cannonball_body, world):
        if self.min_fire_time < time.time():
            a = cannonball_body.angle
            v = b2Vec2(math.cos(a), math.sin(a))
            self.create_grenade(world, cannonball_body.position,
                                cannonball_body.linearVelocity + 15 * v)
            self.min_fire_time = time.time() + self.cooldown

    def create_grenade(self, world, position, velocity):
        body_def = b2BodyDef()
        body_def.position = position
        body = world.CreateBody(body_def)
        body.linearVelocity = velocity
        body.SetUserData({'type': 'grenade'})

        shape_def = b2CircleDef()
        shape_def.radius = 0.25
        shape_def.density = 200
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

        body.SetMassFromShapes()
        return body

class JetEngine(Cannon):
    color = 1, 1, 1
    cooldown = 0.05

    def __init__(self):
        self.min_fire_time = time.time() + self.cooldown

    def fire(self, cannonball_body, world):
        while self.min_fire_time < time.time():
            a = cannonball_body.angle
            v = b2Vec2(math.cos(a), math.sin(a))
            cannonball_body.ApplyImpulse(-v * 500,
                                         cannonball_body.GetWorldCenter())
            v += b2Vec2(random.random() - 0.5, random.random() - 0.5)
            v = cannonball_body.linearVelocity + 15 * v
            self.create_jet_particle(world, cannonball_body.position, v)
            self.min_fire_time = time.time() + self.cooldown

    def create_jet_particle(self, world, position, velocity):
        body_def = b2BodyDef()
        body_def.position = position
        body = world.CreateBody(body_def)
        body.linearVelocity = velocity
        body.SetUserData({'type': 'jet-particle'})

        shape_def = b2CircleDef()
        shape_def.radius = 0.1
        shape_def.density = 100
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 1, 1)})

        body.SetMassFromShapes()
        return body
