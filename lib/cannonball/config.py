import os

root = os.path.abspath(__file__)
for _ in xrange(3):
    root = os.path.dirname(root)

cannonball_max_angular_velocity = 15
cannonball_max_angular_acceleration = 10
