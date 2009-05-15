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
        grenade_factory = level.agent_factories['Grenade']
        grenade = grenade_factory(level)
        grenade.create_body(position, velocity)

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
        factory = level.agent_factories['JetParticle']
        agent = factory(level)
        agent.create_body(position, velocity)
