"""
This script contains a demo that can be run out of the box.
If provided w/the 'manual' argument, the user can control position of the cutting tool.
If this file is modified, you don't need to re-compile/build the cython code.
"""
import matplotlib.pyplot as plt
import numpy as np
import sys
from cloth import *
from circlecloth import *
from mouse import *
from point import *
from constraint import *
from util import *
from mpl_toolkits.mplot3d import Axes3D
from gripper import Gripper


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
        if i < 50:
            tensioner.tension(x=0.0, y=0.0, z=0.1)
        elif i < 200:
            tensioner.tension(x=-0.5, y=-0.5, z=0.0)
        else:
            tensioner.unpin_position()


def cut(mouse):
    """If you want to let the cloth settle, just run `c.update()` beforehand.

    Careful, changing width/height will add more points but not make it stable;
    the cloth 'collapses' ... need to investigate code?

    For tensioning, wherever tension it by default has z-coordinate of 0,
    because we assume a tool has pinched it at that point.
    """
    c = CircleCloth(mouse, width=50, height=50, elasticity=0.1, minimum_z=-20.0,
                    gravity=-1000, physics_accuracy=5, time_interval=0.016)
    grip = Gripper(cloth=c)
    circlex = 540
    circley = 540
    c.pin_position(circlex, circley)
    tensioner = c.tensioners[0]

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

    for i in range(500):
        if i % 10 == 0:
            print("Iteration", i)
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
        ax2.set_zlim([-50, 50]) # only for visualization purposes
        plt.pause(0.001)
        # ----------------------------------------------------------------------

        # Updates (+5 extra) to allow cloth to respond to environment.
        c.update()
        for j in range(5):
            c.update()

    fig.canvas.mpl_disconnect(cid)
    fig.canvas.mpl_disconnect(mid)
    fig.canvas.mpl_disconnect(rid)


if __name__ == "__main__":
    # Originally mouse.down = True but I think it's better as False.
    mouse = Mouse()
    mouse.down = False
    mouse.button = 0

    cut(mouse)
