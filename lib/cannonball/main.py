from __future__ import division

import pyglet, sys, math, random, os
from pyglet.gl import *
from Box2D import *
from cannonball.svg import Document, Transform
from cannonball.material import *
from cannonball.cannon import *

root = os.path.abspath(__file__)
for _ in xrange(3):
    root = os.path.dirname(root)

def parse_color(s):
    return int(s[1:3], 16) / 255, int(s[3:5], 16) / 255, int(s[5:7], 16) / 255

class CannonballWindow(pyglet.window.Window):
    def __init__(self, document):
        pyglet.window.Window.__init__(self, fullscreen=True,
                                      caption="Cannonball")
        self.set_mouse_visible(False)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        namedview = document.element.getElementsByTagName('sodipodi:namedview')[0]
        self.clear_color = parse_color(namedview.getAttribute('pagecolor') or
                                       '#000000') + (0,)

        self.textures = self._load_textures()
        self.materials = dict(stone=Stone(), metal=Metal())

        self.world = self.create_world()
        self.bodies = {}
        self.destroying = set()
        self.cannon_factories = [GrenadeLauncher, JetEngine]
        self.cannon_index = 0
        self.cannon = self.cannon_factories[self.cannon_index]()

        start_position = 0, 0
        transform = Transform('scale(0.2) translate(0 %g) scale(1 -1)' %
                              float(document.element.getAttribute('height')))
        for layer in document.layers:
            for group in layer.groups:
                if group.id == 'start':
                    body = self._create_body(self.world, group, transform, 1)
                    start_position = body.GetWorldCenter().tuple()
                    self.world.DestroyBody(body)
                body = self._create_body(self.world, group, transform)
                self.bodies[group.id] = body

        self.bodies['cannonball'] = self.create_cannonball(self.world,
                                                           start_position)

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
        self.world.SetContactListener(self.contact_listener)

        self.circle_display_list = glGenLists(1)
        glNewList(self.circle_display_list, GL_COMPILE)
        self.draw_circle(256)
        glEndList()

        pyglet.clock.schedule_interval(self.step, 1 / 60)

    def _create_body(self, world, group, transform, min_density=0):
        group_transform = transform * group.transform
        body_def = b2BodyDef()
        body = world.CreateBody(body_def)
        body.SetUserData({'id': group.id})
        for path in group.paths:
            path_transform = group_transform * path.transform
            color = parse_color(path.data.get('fill', '#ffffff'))
            material = path.data.get('material')
            for c in path.path.convexify():
                shape_def = b2PolygonDef()
                shape_def.vertices = [path_transform * (x, y)
                                      for x, y in reversed(c.points)]
                if path.data.get('sensor') == 'true':
                    shape_def.isSensor = True
                if group.data.get('static') != 'false':
                    density = 0
                elif material:
                    density = self.materials[material].density
                else:
                    density = 100
                shape_def.density = max(density, min_density)
                shape = body.CreateShape(shape_def)
                shape.SetUserData({'color': color, 'material': material})
        body.SetMassFromShapes()
        return body

    def _load_textures(self):
        names = ['petrified-seabed', 'rust-peel']
        return dict((name, self._load_texture(name)) for name in names)
        return textures

    def _load_texture(self, name):
        path = os.path.join(root, 'data', 'textures', name + '.jpg')
        image = pyglet.image.load(path)
        return image.get_texture()

    def step(self, dt):
        cannonball_body = self.bodies['cannonball']

        torque = 0
        if self.left:
            torque += 1
        if self.right:
            torque -= 1
        if self.left and self.right:
            cannonball_body.angularVelocity = 0
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
            self.cannon.fire(cannonball_body, self.world)
        self.camera_scale = max(self.min_camera_scale, self.camera_scale)
        self.camera_scale = min(self.camera_scale, self.max_camera_scale)
        cannonball_body.angularVelocity = max(cannonball_body.angularVelocity,
                                              -self.max_angular_velocity)
        cannonball_body.angularVelocity = min(cannonball_body.angularVelocity,
                                              self.max_angular_velocity)

        cannonball_body.ApplyTorque(torque * 10000)
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

        glClearColor(*self.clear_color)
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
            material_obj = self.materials[material]
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
            if shape.GetBody() == self.bodies['cannonball']:
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

    def create_world(self):
        aabb = b2AABB()
        aabb.lowerBound = 0, 0
        aabb.upperBound = 1000, 1000
        gravity = 0, -10
        doSleep = True
        return b2World(aabb, gravity, doSleep)

    def create_cannonball(self, world, position):
        body_def = b2BodyDef()
        body_def.position = position
        body = world.CreateBody(body_def)
        body.SetUserData({'id': 'cannonball'})

        shape_def = b2CircleDef()
        shape_def.radius = 1
        shape_def.localPosition = 0, 0
        shape_def.density = 100
        shape_def.friction = 10
        shape_def.filter.groupIndex = -1
        shape = body.CreateShape(shape_def)
        shape.SetUserData({'color': (0, 0, 0)})

        body.SetMassFromShapes()
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
        count, shapes = self.world.Query(aabb, 100)
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
    document = Document(sys.argv[1])
    window = CannonballWindow(document)
    pyglet.app.run()

if __name__ == '__main__':
    main()
