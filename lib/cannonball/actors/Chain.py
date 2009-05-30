from cannonball.Actor import Actor
from cannonball.actors.Link import *

from Box2D import *

class Chain(Actor):
    def __init__(self, level, actor_1, actor_2, anchor_1, anchor_2):
        self.level = level
        self.actor_1 = actor_1
        self.actor_2 = actor_2
        self.links = [Link(level, anchor_1, anchor_2)]
        joint_def = b2RevoluteJointDef()
        joint_def.Initialize(actor_1.body, self.links[0].body, anchor_1)
        level.world.CreateJoint(joint_def)
        joint_def = b2RevoluteJointDef()
        joint_def.Initialize(self.links[-1].body, actor_2.body, anchor_2)
        level.world.CreateJoint(joint_def)

    def destroy(self):
        while self.links:
            self.links.pop().destroy()
