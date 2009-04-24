from __future__ import division

import pyglet, sys
from pyglet.gl import *

class CannonballWindow(pyglet.window.Window):
    def __init__(self):
        pyglet.window.Window.__init__(self, fullscreen=True,
                                      caption="Cannonball")
        self.set_mouse_visible(False)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def on_draw(self):
        glColor3d(1, 0, 0)
        glBegin(GL_POLYGON)
        glVertex2d(0, 0)
        glVertex2d(self.width / 2, self.height)
        glVertex2d(self.width, 0)
        glEnd()

    def on_close(self):
        self.close()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.on_close()

    def on_key_release(self, symbol, modifiers):
        pass

def main():
    window = CannonballWindow()
    pyglet.app.run()

if __name__ == '__main__':
    main()
