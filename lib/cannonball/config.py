import os

root = os.path.abspath(__file__)
for _ in xrange(3):
    root = os.path.dirname(root)
root = os.environ.get('CANNONBALL_ROOT', root)
