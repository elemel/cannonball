from cannonball.Actor import Actor
from cannonball.svg import *

class RevoluteJoint(Actor):
    def load(self, element, transform):
        transform = transform * Transform(element.getAttribute('transform'))
        center = (float(element.getAttribute('sodipodi:cx')),
                  float(element.getAttribute('sodipodi:cy')))
        self.level.joints.append(transform * center)
