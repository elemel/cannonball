from Box2D import *
import math, time

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
        body_def.isBullet = True
        body = world.CreateBody(body_def)
        body.linearVelocity = velocity
        body.SetUserData({'type': 'grenade'})

        shape_def = b2CircleDef()
        shape_def.radius = 0.25
        shape_def.density = 100
        shape_def.isSensor = True
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

        body.SetMassFromShapes()
        return body

class JetEngine(Cannon):
    pass
