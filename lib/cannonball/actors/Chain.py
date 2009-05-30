from cannonball.Actor import Actor

from Box2D import *

class Chain(Actor):
    def __init__(self, level, body_1, body_2, anchor_1, anchor_2):
        self.level = level
        self.body_1 = body_1
        joint_def = b2DistanceJointDef()
        joint_def.Initialize(body_1, body_2, anchor_1, anchor_2)
        joint_def.collideConnected = True
        level.world.CreateJoint(joint_def)

    def destroy(self):
        joint_edge = self.body_1.GetJointList()
        if joint_edge is not None:
            self.level.world.DestroyJoint(joint_edge.joint)
        self.body_1 = None

