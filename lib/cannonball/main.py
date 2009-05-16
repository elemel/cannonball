from __future__ import division

import pyglet, sys, math, random, os
from pyglet.gl import *
from Box2D import *
from cannonball.svg import *
from cannonball.cannon import *
from cannonball.content import *
from cannonball import config

class CannonballWindow(pyglet.window.Window):
    def __init__(self, level):
        self.level = level
        pyglet.window.Window.__init__(self, fullscreen=True,
                                      caption="Cannonball")
        self.set_mouse_visible(False)
        glEnable(GL_BLEND)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.textures = load_textures(os.path.join(config.root, 'content',
                                                   'textures'))

        start = self.level.agents['start']
        start_shapes = start.body.shapeList
        start_position = b2Vec2()
        for shape in start_shapes:
            start_position += shape.GetCentroid()
        start_position *= 1 / len(start_shapes)
        self.create_cannonball(start_position)

        self.camera_pos = 0, 0
        self.camera_scale = 20
        self.min_camera_scale = 10
        self.max_camera_scale = 50
        self.zoom_in = self.zoom_out = False
        self.contacts = set()

        self.contact_listener = CannonballContactListener(self)
        self.level.world.SetContactListener(self.contact_listener)

        self.boundary_listener = CannonballBoundaryListener(self)
        self.level.world.SetBoundaryListener(self.boundary_listener)

        self.circle_display_list = glGenLists(1)
        glNewList(self.circle_display_list, GL_COMPILE)
        self.draw_circle(256)
        glEndList()

        self.time = 0
        self.physics_time = 0
        self.physics_dt = 1 / 60 
        pyglet.clock.schedule_interval(self.step, self.physics_dt)

    def step(self, dt):
        self.time += dt
        while self.physics_time + self.physics_dt <= self.time:
            self.physics_time += self.physics_dt
            self.step_physics(self.physics_dt)
    
    def step_physics(self, dt):
        cannonball = self.level.agents.get('cannonball')

        if cannonball:
            cannonball.step(dt)

        if self.zoom_in:
            self.camera_scale *= 10 ** dt
        if self.zoom_out:
            self.camera_scale /= 10 ** dt
 
        self.camera_scale = max(self.min_camera_scale, self.camera_scale)
        self.camera_scale = min(self.camera_scale, self.max_camera_scale)
        velocityIterations = 10
        positionIterations = 8
        self.contacts.clear()
        self.level.world.Step(dt, velocityIterations, positionIterations)
        for agent_1, agent_2 in self.contacts:
            agent_1.collide(agent_2)
            agent_2.collide(agent_1)
        if cannonball:
            self.camera_pos = (cannonball.body.position.x,
                               cannonball.body.position.y)
        for agent in self.level.destroying:
            if agent.body:
                self.level.world.DestroyBody(agent.body)
                agent.body = None
                if agent.id:
                    del self.level.agents[agent.id]
        self.level.destroying.clear()
        if cannonball and cannonball.won:
            print 'You Win'
            self.on_close()
        elif not cannonball:
            print 'Game Over'
            self.on_close()

    def on_draw(self):
        r, g, b = self.level.background_color
        glClearColor(r, g, b, 1)
        self.clear()

        camera_x, camera_y = self.camera_pos

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect_ratio = self.width / self.height
        height = 30
        width = aspect_ratio * height
        min_x = camera_x - width / 2
        min_y = camera_y - height / 2
        max_x = camera_x + width / 2
        max_y = camera_y + height / 2
        glOrtho(min_x, max_x, min_y, max_y, -1, 1)
        glMatrixMode(GL_MODELVIEW)

        aabb = b2AABB()
        aabb.lowerBound = min_x, min_y
        aabb.upperBound = max_x, max_y
        count, shapes = self.level.world.Query(aabb, 1000)

        def key(shape):
            return id(shape.GetBody())

        glPushMatrix()
        for shape in sorted(shapes, key=key):
            self.draw_shape(shape)
        glPopMatrix()

    def draw_shape(self, shape):
        glPushMatrix()
        p = shape.GetBody().GetPosition()
        a = shape.GetBody().GetAngle()
        glTranslated(p.x, p.y, 0)
        glRotated(a * 180 / math.pi, 0, 0, 1)
        data = shape.GetUserData() or {}
        material = shape.GetUserData().get('material')
        if material:
            material_obj = self.level.materials[material]
            texture = self.textures[material_obj.texture]
            glColor3d(1, 1, 1)
        else:
            texture = None
            color = data.get('color', (1, 1, 1))
            glColor3d(*color)
        polygon = shape.asPolygon()
        circle = shape.asCircle()
        if polygon:
            self.draw_polygon(polygon, texture)
        elif circle:
            p = circle.localPosition
            glTranslated(p.x, p.y, 0)
            glScaled(circle.radius, circle.radius, 1)
            glCallList(self.circle_display_list)
            if shape.GetBody().userData.id == 'cannonball':
                cannonball = shape.GetBody().userData
                glColor3d(*cannonball.cannon.color)
                glTranslated(0.5, 0, 0)
                glScaled(0.5, 0.5, 1)
                glCallList(self.circle_display_list)
        glPopMatrix()

    def draw_polygon(self, polygon, texture):
        if texture:
            glEnable(texture.target)
            glBindTexture(texture.target, texture.id)
        vertices = list(polygon.vertices)
        vertices.append(vertices[0])
        glBegin(GL_POLYGON)
        for x, y in vertices:
            if texture:
                glTexCoord2d(x * 0.1, y * 0.1)
            glVertex2d(x, y)
        glEnd()
        glBegin(GL_LINE_STRIP)
        for x, y in vertices:
            if texture:
                glTexCoord2d(x * 0.1, y * 0.1)
            glVertex2d(x, y)
        glEnd()
        if texture:
            glDisable(texture.target)

    def draw_circle(self, triangle_count):
        glBegin(GL_POLYGON)
        for i in xrange(triangle_count + 1):
            a = 2 * math.pi * i / triangle_count
            glVertex2d(math.cos(a), math.sin(a))
        glEnd()
        glBegin(GL_LINE_STRIP)
        for i in xrange(triangle_count + 1):
            a = 2 * math.pi * i / triangle_count
            glVertex2d(math.cos(a), math.sin(a))
        glEnd()

    def on_close(self):
        self.close()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.on_close()
        cannonball = self.level.agents.get('cannonball')
        if cannonball:
            if symbol == pyglet.window.key.LEFT:
                cannonball.rolling_left = True
            if symbol == pyglet.window.key.RIGHT:
                cannonball.rolling_right = True
            if symbol == pyglet.window.key.TAB:
                cannonball.switching_cannon = True
            if symbol == pyglet.window.key.SPACE:
                cannonball.firing = True
        if symbol == pyglet.window.key.PLUS:
            self.zoom_in = True
        if symbol == pyglet.window.key.MINUS:
            self.zoom_out = True

    def on_key_release(self, symbol, modifiers):
        cannonball = self.level.agents.get('cannonball')
        if cannonball:
            if symbol == pyglet.window.key.LEFT:
                cannonball.rolling_left = False
            if symbol == pyglet.window.key.RIGHT:
                cannonball.rolling_right = False
            if symbol == pyglet.window.key.SPACE:
                cannonball.firing = False
        if symbol == pyglet.window.key.PLUS:
            self.zoom_in = False
        if symbol == pyglet.window.key.MINUS:
            self.zoom_out = False

    def create_cannonball(self, position):
        factory = self.level.agent_factories['Cannonball']
        agent = factory(self.level)
        agent.create_body(position)

    def add_contact(self, point):
        agent_1 = point.shape1.GetBody().GetUserData()
        agent_2 = point.shape2.GetBody().GetUserData()
        if agent_1 and agent_2:
            self.contacts.add((agent_1, agent_2))

class CannonballContactListener(b2ContactListener):
    def __init__(self, window):
        super(CannonballContactListener, self).__init__() 
        self.window = window

    def Add(self, point):
        self.window.add_contact(point)

    def Persist(self, point):
        pass

    def Remove(self, point):
        pass

    def Result(self, point):
        pass

class CannonballBoundaryListener(b2BoundaryListener):
    def __init__(self, window):
        super(CannonballBoundaryListener, self).__init__()
        self.window = window

    def Violation(self, body):
        agent = body.userData
        self.window.level.destroying.add(agent)
 
def main():
    if len(sys.argv) != 2:
        print 'Usage: cannonball <level>'
        sys.exit(1)
    agent_root = os.path.join(config.root, 'content', 'agents')
    agent_factories = load_agent_factories(agent_root)
    level = load_level(sys.argv[1], agent_factories)
    window = CannonballWindow(level)
    pyglet.app.run()

if __name__ == '__main__':
    main()
