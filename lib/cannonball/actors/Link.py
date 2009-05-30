from cannonball.Actor import Actor

from Box2D import *

from math import *

class Link(Actor):
    def __init__(self, level, p1, p2):
        super(Link, self).__init__(level)
        body_def = b2BodyDef()
        body_def.angle = atan2(p2.y - p1.y, p2.x - p1.x)
        body_def.position = (p1 + p2) / 2
        self.body = level.world.CreateBody(body_def)
        self.body.userData = self
        shape_def = b2PolygonDef()
        shape_def.density = 1
        shape_def.SetAsBox((p2 - p1).Length() / 2, 0.05)
        self.body.CreateShape(shape_def)
        self.body.SetMassFromShapes()

    def destroy(self):
        self.level.world.DestroyBody(self.body)
        self.body = None
