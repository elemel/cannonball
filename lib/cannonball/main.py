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

        self.world = self.create_world()
        self.bodies = {}
        self.destroying = set()
        self.bodies['ground'] = self.create_ground(self.world)
        self.bodies['goal'] = self.create_goal(self.world, (110, 101))
        self.bodies['cannonball'] = self.create_cannonball(self.world,
                                                           (100, 101))
        self.create_brick(self.world, (105, 101))
        self.create_brick(self.world, (105, 102))
        self.create_brick(self.world, (105, 103))
        self.create_brick(self.world, (105, 104))
        self.create_brick(self.world, (105, 105))
        self.create_brick(self.world, (105, 106))
        self.create_brick(self.world, (105, 107))
        self.create_brick(self.world, (105, 108))
        self.create_brick(self.world, (105, 109))
        self.create_brick(self.world, (105, 110))

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
            self.create_bullet(self.world, cannonball_body.position,
                               cannonball_body.linearVelocity + 15 * v)
        self.camera_scale = max(self.min_camera_scale, self.camera_scale)
        self.camera_scale = min(self.camera_scale, self.max_camera_scale)

        cannonball_body.ApplyTorque(torque * 2000)
        velocityIterations = 10
        positionIterations = 8
        self.world.Step(dt, velocityIterations, positionIterations)
        self.camera_pos = (cannonball_body.position.x,
                           cannonball_body.position.y)
        for body in self.destroying:
            data = body.GetUserData() or {}
            if 'name' in data:
                del self.bodies['name']
            self.world.DestroyBody(body)
        self.destroying.clear()
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
        aabb = b2AABB()
        aabb.lowerBound = 0, 0
        aabb.upperBound = 1000, 1000
        gravity = 0, -10
        doSleep = True
        return b2World(aabb, gravity, doSleep)

    def create_ground(self, world):
        body_def = b2BodyDef()
        body_def.position = 100, 90
        body = world.CreateBody(body_def)
        body.SetUserData({'name': 'ground'})

        shape_def = b2PolygonDef()
        shape_def.SetAsBox(50, 10)
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (0.5, 0.5, 0.5)})

        return body

    def create_cannonball(self, world, position):
        body_def = b2BodyDef()
        body_def.position = position
        body = world.CreateBody(body_def)
        body.SetUserData({'name': 'cannonball'})

        shape_def = b2CircleDef()
        shape_def.radius = 1
        shape_def.localPosition = 0, 0
        shape_def.density = 100
        shape = body.CreateShape(shape_def)

        shape.SetUserData({'color': (0.5, 1, 0)})
        shape_def = b2CircleDef()
        shape_def.radius = 0.5
        shape_def.localPosition = 0.5, 0
        shape_def.density = 1
        shape_def.filter.groupIndex = -1
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (1, 0, 0)})

        body.SetMassFromShapes()
        return body

    def create_brick(self, world, position):
        body_def = b2BodyDef()
        body_def.position = position
        body = world.CreateBody(body_def)
        body.SetUserData({'type': 'brick'})

        shape_def = b2PolygonDef()
        shape_def.SetAsBox(1, 0.5)
        shape_def.density = 100
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (0, 0.5, 1)})

        body.SetMassFromShapes()
        return body

    def create_bullet(self, world, position, velocity):
        body_def = b2BodyDef()
        body_def.position = position
        body_def.isBullet = True
        body = world.CreateBody(body_def)
        body.linearVelocity = velocity
        body.SetUserData({'type': 'bullet'})

        shape_def = b2CircleDef()
        shape_def.radius = 0.25
        shape_def.density = 100
        shape_def.isSensor = True
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
        data_1 = body_1.GetUserData() or {}
        data_2 = body_2.GetUserData() or {}
        name_1 = data_1.get('name')
        name_2 = data_2.get('name')
        type_1 = data_1.get('type')
        type_2 = data_2.get('type')
        if set([name_1, name_2]) == set(['cannonball', 'goal']):
            self.win = True
        if (type_1 == 'bullet' and not point.shape2.isSensor and
            name_2 != 'cannonball'):
            self.handle_bullet_collision(point, body_1, body_2, point.normal)
        if (type_2 == 'bullet' and not point.shape1.isSensor and
            name_1 != 'cannonball'):
            self.handle_bullet_collision(point, body_2, body_1, -point.normal)

    def handle_bullet_collision(self, point, bullet_body, other_body, normal):
        self.destroying.add(bullet_body)
        other_data = other_body.GetUserData() or {}
        other_type = other_data.get('type')
        if other_type == 'brick':
            other_body.ApplyImpulse(2000 * normal, point.position)

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
