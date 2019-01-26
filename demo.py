"""
This script contains a demo that can be run out of the box.
If provided w/the 'manual' argument, the user can control position of the cutting tool.
If this file is modified, you don't need to re-compile/build the cython code.
"""
import matplotlib.pyplot as plt
import numpy as np
import sys, os, argparse
from cloth import *
from circlecloth import *
from mouse import *
from point import *
from constraint import *
from util import *
from mpl_toolkits.mplot3d import Axes3D
from gripper import Gripper

# ------------------------------------------------------------------------------
# From cloth sim tutorial using PyOpenGL, Ian Mallett tutorial.
# ------------------------------------------------------------------------------
from OpenGL.GL import *
from OpenGL.GLU import *
import pygame
from pygame.locals import *
import traceback
if sys.platform == 'win32' or sys.platform == 'win64':
    os.environ['SDL_VIDEO_CENTERED'] = '1'
from math import *

pygame.display.init()
pygame.font.init()
screen_size = [800,600]
multisample = 16
icon = pygame.Surface((1,1)); icon.set_alpha(0); pygame.display.set_icon(icon)
pygame.display.set_caption("Cloth Demo 2 - Ian Mallett - v.2 - 2012")

if multisample:
    pygame.display.gl_set_attribute(GL_MULTISAMPLEBUFFERS,1)
    pygame.display.gl_set_attribute(GL_MULTISAMPLESAMPLES,multisample)
pygame.display.set_mode(screen_size,OPENGL|DOUBLEBUF)

#glEnable(GL_BLEND)
#glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
#glEnable(GL_TEXTURE_2D)
#glTexEnvi(GL_TEXTURE_ENV,GL_TEXTURE_ENV_MODE,GL_MODULATE)
#glTexEnvi(GL_POINT_SPRITE,GL_COORD_REPLACE,GL_TRUE)
glHint(GL_PERSPECTIVE_CORRECTION_HINT,GL_NICEST)
glEnable(GL_DEPTH_TEST)
glPointSize(4)
# ------------------------------------------------------------------------------



camera_rot = [70,23]
camera_radius = 2.5
camera_center = [0.5,0.5,0.5]


def get_input():
    """From tutorial.
    """
    global camera_rot, camera_radius
    keys_pressed = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_rel = pygame.mouse.get_rel()
    for event in pygame.event.get():
        if   event.type == QUIT: return False
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_r: cloth.reset()
        elif event.type == MOUSEBUTTONDOWN:
            if   event.button == 4: camera_radius -= 0.5
            elif event.button == 5: camera_radius += 0.5
    if mouse_buttons[0]:
        camera_rot[0] += mouse_rel[0]
        camera_rot[1] += mouse_rel[1]
    return True


def cloth_draw(circle_cloth):
    glBegin(GL_POINTS)
    #for row in self.particles:
    #    for particle in row:
    #        particle.draw()
    glEnd()


def cloth_draw_wireframe(circle_cloth):
    glBegin(GL_LINES)
    for pt in circle_cloth.pts:
        for constraint in pt.constraints:
            glVertex3fv(constraint.p1.get_scaled())
            glVertex3fv(constraint.p2.get_scaled())
            #print(constraint.p1_pos)
            #print(constraint.p2_pos)
    glEnd()


def draw(c):
    """Directly form tutorial, will comment out stuff I don't need. Changes:

    - Takes in cloth `c` argument, and we get points using our class.
    - Replace `cloth.draw()` and `cloth.draw_wireframe()` with our methods.
    """
    # We can use these to get the points
    #pts  = np.array([[p.x, p.y, p.z] for p in c.pts])
    #npts = np.array([[p.x, p.y, p.z] for p in c.normalpts])
    #cpts = np.array([[p.x, p.y, p.z] for p in c.shapepts])

    # Ian Mallett code
    glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
    glViewport(0,0,screen_size[0],screen_size[1])
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45,float(screen_size[0])/float(screen_size[1]), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    camera_pos = [
        camera_center[0] + camera_radius*cos(radians(camera_rot[0]))*cos(radians(camera_rot[1])),
        camera_center[1] + camera_radius                            *sin(radians(camera_rot[1])),
        camera_center[2] + camera_radius*sin(radians(camera_rot[0]))*cos(radians(camera_rot[1]))
    ]
    gluLookAt(
        camera_pos[0],camera_pos[1],camera_pos[2],
        camera_center[0],camera_center[1],camera_center[2],
        0,1,0
    )
    
    # Need to replace `draw()` and `draw_wireframe()`.
    #cloth.draw()
    cloth_draw(c)
    glColor3f(0,0.2,0)
    #cloth.draw_wireframe()
    cloth_draw_wireframe(c)
    
    glColor3f(1,0,0)
    glBegin(GL_LINES)
    points = []
    for x in [0,1]:
        for y in [0,1]:
            for z in [0,1]:
                points.append([x,y,z])
    for p1 in points:
        for p2 in points:
            unequal = sum([int(p1[i]!=p2[i]) for i in [0,1,2]])
            if unequal == 1:
                glVertex3fv(p1)
                glVertex3fv(p2)
    glEnd()
    glColor3f(1,1,1)
    # https://stackoverflow.com/questions/29314987/
    # difference-between-pygame-display-update-and-pygame-display-flip
    pygame.display.flip()


def circle():
    """simulate moving the mouse in a circle while cutting, overcut since no perception
    (Deprecated, old code...)
    """
    circlex = 300
    circley = 300
    radius = 150
    if i < 150:
        theta = 360.0/100.0 * i * np.pi / 180.0
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        mouse.move(x + circlex, y + circley)


def pull(i, tensioner):
    """Looks cool. Feel free to adjust...
    """
    if i % 10 == 0:
        if i < 120:
            tensioner.tension(x=0.0, y=0.0, z=0.2)
        elif i < 210:
            tensioner.tension(x=-0.4, y=-0.4, z=0.0)
        else:
            tensioner.unpin_position()


def move(c, args):
    """If you want to let the cloth settle, just run `c.update()` beforehand.

    Careful, changing width/height will add more points but not make it stable;
    the cloth 'collapses' ... need to investigate code?

    For tensioning, wherever tension it by default has z-coordinate of 0,
    because we assume a tool has pinched it at that point.
    """
    grip = Gripper(cloth=c)
    start_t = time.time()

    # Will put this in a separate class soon. Need a 'pin' and then we can pull.
    circlex = 300
    circley = 300
    c.pin_position(circlex, circley)
    tensioner = c.tensioners[0]

    if args.viz_tool == 'matplotlib':
        # Use `plt.ion()` for interactive plots, requires `plt.pause(...)` later.
        nrows, ncols = 1, 2
        fig = plt.figure(figsize=(12*ncols,12*nrows))
        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2, projection='3d')
        plt.ion()
        plt.tight_layout()
        cid = fig.canvas.mpl_connect('button_press_event', mouse.clicked)
        rid = fig.canvas.mpl_connect('button_release_event', mouse.released)
        mid = fig.canvas.mpl_connect('motion_notify_event', mouse.moved)

        for i in range(args.num_sim_iters):
            if i % 10 == 0:
                elapsed_time = (time.time() - start_t) / 60.0
                print("Iteration {}, minutes: {:.1f}".format(i, elapsed_time))
                z_vals = [p.z for p in c.shapepts]
                print("  average z: {:.2f}".format(np.mean(z_vals)))
                print("  median z:  {:.2f}".format(np.median(z_vals)))
            ax1.cla()
            ax2.cla()
            pull(i, tensioner)
            # ----------------------------------------------------------------------
            # Re-insert the points, with appropriate colors. 2D AND 3D together.
            # ----------------------------------------------------------------------
            pts  = np.array([[p.x, p.y, p.z] for p in c.normalpts])
            cpts = np.array([[p.x, p.y, p.z] for p in c.shapepts])
            if len(pts) > 0:
                ax1.scatter(pts[:,0], pts[:,1], c='g')
                ax2.scatter(pts[:,0], pts[:,1], pts[:,2], c='g')
            if len(cpts) > 0:
                ax1.scatter(cpts[:,0], cpts[:,1], c='b')
                ax2.scatter(cpts[:,0], cpts[:,1], cpts[:,2], c='b')
            ax2.set_zlim([0, 300]) # only for visualization purposes
            plt.pause(0.001)
            # ----------------------------------------------------------------------
            # Updates (+5 extra) to allow cloth to respond to environment. Think of
            # it as like a 'frame skip' parameter.
            for _ in range(args.updates_per_move):
                c.simulate()

        fig.canvas.mpl_disconnect(cid)
        fig.canvas.mpl_disconnect(mid)
        fig.canvas.mpl_disconnect(rid)

    elif args.viz_tool == 'pyopengl':
        # Note: 1/60 ~ 0.016 so we might as well try this way ...
        target_fps = 60
        clock = pygame.time.Clock()
        dt = 1.0/float(target_fps)

        # Sequence of update then draw commands
        for i in range(args.num_sim_iters):
            if not get_input(): break

            if i % 10 == 0:
                elapsed_time = (time.time() - start_t) / 60.0
                print("Iteration {}, minutes: {:.1f}".format(i, elapsed_time))
            pull(i, tensioner)
            for _ in range(args.updates_per_move):
                c.simulate()

            # Draw
            draw(c)
            clock.tick(target_fps)
        pygame.quit()


if __name__ == "__main__":
    # --------------------------------------------------------------------------
    # Height and width are from a 2D perspective, really length and width...
    # Also those indicate the actual amount of discretized points, then dx,dy
    # the 'real-world spacing'. Put all these in `json` files later.
    # --------------------------------------------------------------------------
    pp = argparse.ArgumentParser()
    # Cloth and relevant parameters
    pp.add_argument('--width', type=int, default=25)
    pp.add_argument('--height', type=int, default=25)
    pp.add_argument('--dx', type=float, default=10.0)
    pp.add_argument('--dy', type=float, default=10.0)
    pp.add_argument('--offset', type=float, default=50.0)
    pp.add_argument('--centerx', type=float, default=250.0)
    pp.add_argument('--centery', type=float, default=250.0)
    pp.add_argument('--radius', type=float, default=50.0)
    pp.add_argument('--gravity', type=float, default=-1000.0)
    pp.add_argument('--elasticity', type=float, default=1.0)
    pp.add_argument('--min_z', type=float, default=0.0)
    pp.add_argument('--time_interval', type=float, default=0.016)
    pp.add_argument('--thickness', type=float, default=4.0)
    # Other stuff
    pp.add_argument('--num_sim_iters', type=int, default=500)
    pp.add_argument('--enable_cutting', action='store_true', default=False)
    pp.add_argument('--updates_per_move', type=int, default=6) # like frame skip
    pp.add_argument('--norender', action='store_true', default=False)
    pp.add_argument('--viz_tool', type=str, default='matplotlib')
    pp.add_argument('--pin_cond', type=str, default='x=0,y=0')
    args = pp.parse_args()
    args.seed = 1

    # Originally mouse.down = True but I think it's better as False.
    mouse = Mouse(enable_cutting=args.enable_cutting)
    mouse.down = False
    mouse.button = 0

    bounds = (args.offset*2 + args.width*args.dx,
              args.offset*2 + args.height*args.dy, 400)
    assert args.pin_cond in ['x=0,y=0', 'y=0', 'y=0,y=height'], args.pin_cond
    assert args.viz_tool in ['matplotlib', 'pyopengl'], args.viz_tool

    c = CircleCloth(mouse,
        width=args.width,
        height=args.height,
        dx=args.dx,
        dy=args.dy,
        offset=args.offset,
        centerx=args.centerx,
        centery=args.centery,
        radius=args.radius,
        gravity=args.gravity,
        elasticity=args.elasticity,
        pin_cond=args.pin_cond,
        bounds=bounds,
        minimum_z=args.min_z,
        time_interval=args.time_interval,
        thickness=args.thickness,
    )
    move(c, args)
