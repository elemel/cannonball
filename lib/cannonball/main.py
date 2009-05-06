from __future__ import division

import pyglet, sys, math, random, os
from pyglet.gl import *
from Box2D import *
from cannonball.svg import *
from cannonball.cannon import *
from cannonball.asset import *
from cannonball import config

class CannonballWindow(pyglet.window.Window):
    def __init__(self, level):
        self.level = level
        pyglet.window.Window.__init__(self, fullscreen=True,
                                      caption="Cannonball")
        self.set_mouse_visible(False)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.textures = load_textures(os.path.join(config.root, 'data',
                                                   'textures'))

        self.destroying = set()
        self.cannon_factories = [GrenadeLauncher, JetEngine]
        self.cannon_index = 0
        self.cannon = self.cannon_factories[self.cannon_index]()

        start_body = self.level.bodies['start']
        start_shapes = start_body.shapeList
        start_pos = b2Vec2()
        for shape in start_shapes:
            start_pos += shape.GetCentroid()
        start_pos *= 1 / len(start_shapes)
        self.level.bodies['cannonball'] = self.create_cannonball(self.level.world,
                                                                 start_pos)

        self.camera_pos = 0, 0
        self.camera_scale = 20
        self.min_camera_scale = 10
        self.max_camera_scale = 50
        self.max_angular_velocity = 20
        self.left = self.right = False
        self.switch_cannon = False
        self.firing = False
        self.zoom_in = self.zoom_out = False
        self.win = False

        self.contact_listener = CannonballContactListener(self)
        self.level.world.SetContactListener(self.contact_listener)

        self.circle_display_list = glGenLists(1)
        glNewList(self.circle_display_list, GL_COMPILE)
        self.draw_circle(256)
        glEndList()

        pyglet.clock.schedule_interval(self.step, 1 / 60)

    def step(self, dt):
        cannonball_body = self.level.bodies['cannonball']

        def sign(x):
            return x / abs(x) if x else 0

        av = cannonball_body.angularVelocity
        max_av = config.cannonball_max_angular_velocity
        max_aa = config.cannonball_max_angular_acceleration
        roll = self.left - self.right
        if roll:
            av += roll * max_aa * dt
            av = sign(av) * min(abs(av), max_av)
        elif av:
            av = sign(av) * max(abs(av) - max_aa * dt, 0)

        cannonball_body.angularVelocity = av
        cannonball_body.WakeUp()
        
        if self.switch_cannon:
            self.switch_cannon = False
            self.cannon_index += 1
            self.cannon_index %= len(self.cannon_factories)
            self.cannon = self.cannon_factories[self.cannon_index]()
        if self.zoom_in:
            self.camera_scale *= 10 ** dt
        if self.zoom_out:
            self.camera_scale /= 10 ** dt
        if self.firing:
            self.cannon.fire(cannonball_body, self.level.world)
        self.camera_scale = max(self.min_camera_scale, self.camera_scale)
        self.camera_scale = min(self.camera_scale, self.max_camera_scale)
        velocityIterations = 10
        positionIterations = 8
        self.level.world.Step(dt, velocityIterations, positionIterations)
        self.camera_pos = (cannonball_body.position.x,
                           cannonball_body.position.y)
        for body in self.destroying:
            data = body.GetUserData() or {}
            if 'name' in data:
                del self.bodies['name']
            self.level.world.DestroyBody(body)
        self.destroying.clear()
        if self.win:
            print 'You Win'
            self.on_close()

    def on_draw(self):
        aabb = b2AABB()
        aabb.lowerBound = 0, 0
        aabb.upperBound = 1000, 1000
        count, shapes = self.level.world.Query(aabb, 100)

        r, g, b = self.level.background_color
        glClearColor(r, g, b, 1)
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
            if shape.GetBody() == self.level.bodies['cannonball']:
                glColor3d(*self.cannon.color)
                glTranslated(0.5, 0, 0)
                glScaled(0.5, 0.5, 1)
                glCallList(self.circle_display_list)
        glPopMatrix()

    def draw_polygon(self, polygon, texture):
        if texture:
            glEnable(texture.target)
            glBindTexture(texture.target, texture.id)
        glBegin(GL_POLYGON)
        for x, y in polygon.vertices:
            if texture:
                glTexCoord2d(x * 0.1, y * 0.1)
            glVertex2d(x, y)
        glEnd()
        if texture:
            glDisable(texture.target)

    def draw_circle(self, triangle_count):
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
        if symbol == pyglet.window.key.TAB:
            self.switch_cannon = True
        if symbol == pyglet.window.key.SPACE:
            self.firing = True
        if symbol == pyglet.window.key.PLUS:
            self.zoom_in = True
        if symbol == pyglet.window.key.MINUS:
            self.zoom_out = True

    def on_key_release(self, symbol, modifiers):
        if symbol == pyglet.window.key.LEFT:
            self.left = False
        if symbol == pyglet.window.key.RIGHT:
            self.right = False
        if symbol == pyglet.window.key.SPACE:
            self.firing = False
        if symbol == pyglet.window.key.PLUS:
            self.zoom_in = False
        if symbol == pyglet.window.key.MINUS:
            self.zoom_out = False

    def create_cannonball(self, world, position):
        body_def = b2BodyDef()
        body_def.position = position
        body = world.CreateBody(body_def)
        body.SetUserData({'id': 'cannonball'})

        shape_def = b2CircleDef()
        shape_def.radius = 1
        shape_def.localPosition = 0, 0
        shape_def.density = 100
        shape_def.friction = 5
        shape_def.restitution = 0.5
        shape_def.filter.groupIndex = -1
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (0, 0, 0)})

        body.SetMassFromShapes()
        massData = body.massData
        massData.I = 1e9
        body.massData = massData
        return body

    def add_contact(self, point):
        body_1 = point.shape1.GetBody()
        body_2 = point.shape2.GetBody()
        data_1 = body_1.GetUserData() or {}
        data_2 = body_2.GetUserData() or {}
        id_1 = data_1.get('id')
        id_2 = data_2.get('id')
        type_1 = data_1.get('type')
        type_2 = data_2.get('type')
        if set([id_1, id_2]) == set(['cannonball', 'goal']):
            self.win = True
        if (type_1 == 'grenade' and not point.shape2.isSensor and
            id_2 != 'cannonball'):
            self.handle_grenade_collision(point, body_1, body_2, point.normal)
        if (type_2 == 'grenade' and not point.shape1.isSensor and
            id_1 != 'cannonball'):
            self.handle_grenade_collision(point, body_2, body_1, -point.normal)
        if type_1 == 'jet-particle' and not point.shape2.isSensor:
            self.destroying.add(body_1)
        if type_2 == 'jet-particle' and not point.shape1.isSensor:
            self.destroying.add(body_2)

    def handle_grenade_collision(self, point, grenade_body, other_body,
                                 normal):
        self.destroying.add(grenade_body)
        x, y = point.position.tuple()
        aabb = b2AABB()
        aabb.lowerBound = x - 1, y - 1
        aabb.upperBound = x + 1, y + 1
        count, shapes = self.level.world.Query(aabb, 100)
        bodies = set(s.GetBody() for s in shapes)
        for body in bodies:
            offset = point.position - body.GetWorldCenter()
            offset.Normalize()
            body.ApplyImpulse(-offset * 5000, body.GetWorldCenter())

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
    if len(sys.argv) != 2:
        print 'Usage: cannonball <level>'
        sys.exit(1)
    level = load_level(sys.argv[1])
    window = CannonballWindow(level)
    pyglet.app.run()

if __name__ == '__main__':
    main()
