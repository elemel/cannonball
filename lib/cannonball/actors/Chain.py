from cannonball.Actor import Actor

from Box2D import *

class Chain(Actor):
    def __init__(self, level, actor_1, actor_2, anchor_1, anchor_2):
        self.level = level
        self.actor_1 = actor_1
        self.actor_2 = actor_2
        joint_def = b2DistanceJointDef()
        joint_def.Initialize(actor_1.body, actor_2.body, anchor_1, anchor_2)
        joint_def.collideConnected = True
        level.world.CreateJoint(joint_def)

    def destroy(self):
        joint_edge = self.actor_1.body.GetJointList()
        if joint_edge is not None:
            self.level.world.DestroyJoint(joint_edge.joint)
        self.body_1 = None

