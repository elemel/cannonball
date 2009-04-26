from __future__ import division

import pyglet, sys, math
from pyglet.gl import *
from Box2D import *

class CannonballWindow(pyglet.window.Window):
    def __init__(self):
        pyglet.window.Window.__init__(self, fullscreen=True,
                                      caption="Cannonball")
        self.set_mouse_visible(False)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.bodies = {}
        self.world = self.create_world()
        self.bodies['goal'] = self.create_goal(self.world, (110, 101))
        self.camera_pos = 0, 0
        self.camera_scale = 50
        self.min_camera_scale = 20
        self.max_camera_scale = 100
        self.left = self.right = False
        self.up = self.down = False
        self.fire = False
        self.win = False

        self.contact_listener = CannonballContactListener(self)
        self.world.SetContactListener(self.contact_listener)

        pyglet.clock.schedule_interval(self.step, 1 / 60)

    def step(self, dt):
        cannonball_body = self.bodies['cannonball']

        torque = 0
        if self.left:
            torque += 1
        if self.right:
            torque -= 1
        if self.up:
            self.camera_scale *= 10 ** dt
        if self.down:
            self.camera_scale /= 10 ** dt
        if self.fire:
            self.fire = False
            a = cannonball_body.angle
            v = b2Vec2(math.cos(a), math.sin(a))
            self.create_shot(self.world, cannonball_body.position,
                             cannonball_body.linearVelocity + 15 * v)
        self.camera_scale = max(self.min_camera_scale, self.camera_scale)
        self.camera_scale = min(self.camera_scale, self.max_camera_scale)

        cannonball_body.ApplyTorque(torque * 2000)
        velocityIterations = 10
        positionIterations = 8
        self.world.Step(dt, velocityIterations, positionIterations)
        self.camera_pos = (cannonball_body.position.x,
                           cannonball_body.position.y)
        if self.win:
            print 'You Win'
            self.on_close()

    def on_draw(self):
        aabb = b2AABB()
        aabb.lowerBound = 0, 0
        aabb.upperBound = 1000, 1000
        count, shapes = self.world.Query(aabb, 100)

        self.clear()
        glPushMatrix()
        glTranslated(self.width / 2, self.height / 2, 0)
        glScaled(self.camera_scale, self.camera_scale, 1)
        camera_x, camera_y = self.camera_pos
        glTranslated(-camera_x, -camera_y, 0)
        for shape in shapes:
            self.draw_shape(shape)
        glPopMatrix()

    def draw_shape(self, shape):
        glPushMatrix()
        p = shape.GetBody().GetPosition()
        a = shape.GetBody().GetAngle()
        glTranslated(p.x, p.y, 0)
        glRotated(a * 180 / math.pi, 0, 0, 1)
        data = shape.GetUserData() or {}
        color = data.get('color', (1, 1, 1))
        glColor3d(*color)
        polygon = shape.asPolygon()
        circle = shape.asCircle()
        if polygon:
            self.draw_polygon(polygon)
        elif circle:
            p = circle.localPosition
            glTranslated(p.x, p.y, 0)
            glScaled(circle.radius, circle.radius, 1)
            self.draw_circle(circle)
        glPopMatrix()

    def draw_polygon(self, polygon):
        glBegin(GL_POLYGON)
        for vertex in polygon.vertices:
            glVertex2d(*vertex)
        glEnd()

    def draw_circle(self, circle):
        triangle_count = 32
        glBegin(GL_POLYGON)
        for i in xrange(triangle_count):
            a = 2 * math.pi * i / triangle_count
            glVertex2d(math.cos(a), math.sin(a))
        glEnd()

    def on_close(self):
        self.close()

    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            self.on_close()
        if symbol == pyglet.window.key.LEFT:
            self.left = True
        if symbol == pyglet.window.key.RIGHT:
            self.right = True
        if symbol == pyglet.window.key.UP:
            self.up = True
        if symbol == pyglet.window.key.DOWN:
            self.down = True
        if symbol == pyglet.window.key.SPACE:
            self.fire = True

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.LEFT:
            self.left = False
        if symbol == pyglet.window.key.RIGHT:
            self.right = False
        if symbol == pyglet.window.key.UP:
            self.up = False
        if symbol == pyglet.window.key.DOWN:
            self.down = False

    def create_world(self):
        worldAABB = b2AABB()
        worldAABB.lowerBound = 0, 0
        worldAABB.upperBound = 1000, 1000
        gravity = 0, -10
        doSleep = True
        world = b2World(worldAABB, gravity, doSleep)

        groundBodyDef = b2BodyDef()
        groundBodyDef.position = 100, 90
        groundBody = world.CreateBody(groundBodyDef)
        groundShapeDef = b2PolygonDef()
        groundShapeDef.SetAsBox(50, 10)
        shape = groundBody.CreateShape(groundShapeDef)
        shape.SetUserData({'color': (0.5, 0.5, 0.5)})
        groundBody.SetUserData({'name': 'ground'})
        self.bodies['ground'] = groundBody

        cannonballBodyDef = b2BodyDef()
        cannonballBodyDef.position = 100, 120
        cannonballBody = world.CreateBody(cannonballBodyDef)
        cannonballShapeDef = b2CircleDef()
        cannonballShapeDef.radius = 1
        cannonballShapeDef.localPosition = 0, 0
        cannonballShapeDef.density = 100
        cannonballShapeDef.filter.groupIndex = -1
        shape = cannonballBody.CreateShape(cannonballShapeDef)
        shape.SetUserData({'color': (0.5, 1, 0)})
        cannonballShapeDef = b2CircleDef()
        cannonballShapeDef.radius = 0.5
        cannonballShapeDef.localPosition = 0.5, 0
        cannonballShapeDef.density = 1
        cannonballShapeDef.filter.groupIndex = -1
        shape = cannonballBody.CreateShape(cannonballShapeDef)
        shape.SetUserData({'color': (1, 0, 0)})
        cannonballBody.SetMassFromShapes()
        cannonballBody.SetUserData({'name': 'cannonball'})
        cannonballBody.angularVelocity = 0
        self.bodies['cannonball'] = cannonballBody

        return world

    def create_shot(self, world, position, velocity):
        body_def = b2BodyDef()
        body_def.position = position
        body = self.world.CreateBody(body_def)
        body.linearVelocity = velocity
        shape_def = b2CircleDef()
        shape_def.radius = 0.5
        shape_def.density = 100
        shape_def.filter.groupIndex = -1
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})
        body.SetMassFromShapes()
        return body

    def create_goal(self, world, position):
        body_def = b2BodyDef()
        body_def.position = position
        body = world.CreateBody(body_def)
        body.SetUserData({'name': 'goal'})
        shape_def = b2CircleDef()
        shape_def.isSensor = True
        shape_def.radius = 0.5
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 1, 0)})
        return body

    def add_contact(self, point):
        body_1 = point.shape1.GetBody()
        body_2 = point.shape2.GetBody()
        name_1 = (body_1.GetUserData() or {}).get('name')
        name_2 = (body_2.GetUserData() or {}).get('name')
        if set([name_1, name_2]) == set(['cannonball', 'goal']):
            self.win = True

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

def main():
    window = CannonballWindow()
    pyglet.app.run()

if __name__ == '__main__':
    main()
