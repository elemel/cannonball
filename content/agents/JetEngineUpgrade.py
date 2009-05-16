from Box2D import *
import random
from cannonball.agent import Agent

class JetEngineUpgrade(Agent):
    def __init__(self, level):
        super(JetEngineUpgrade, self).__init__()
        self.level = level

    def collide(self, other):
        if not self in self.level.destroying and other.id == 'cannonball':
            self.level.destroying.add(self)
            other.cannon_factories.append(JetEngine)

class JetEngine(object):
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
