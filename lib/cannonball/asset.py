import os, pyglet
from cannonball import config

def load_textures():
    names = ['petrified-seabed', 'rust-peel']
    return dict((name, load_texture(name)) for name in names)

def load_texture(name):
    path = os.path.join(config.root, 'data', 'textures', name + '.jpg')
    image = pyglet.image.load(path)
    return image.get_texture()
