import matplotlib.pyplot as plt
import numpy as np
import sys
from cloth import *
from circlecloth import *
from mouse import *
from point import *
from constraint import *
from util import *
"""
This script contains a demo that can be run out of the box.
If provided w/the 'manual' argument, the user can control position of the cutting tool.
If this file is modified, you don't need to re-compile/build the cython code.
"""

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        print("Manual cutting")
        auto = False
    else:
        print("Automated cutting")
        auto = True

    # Originally mouse.down = True but I think it's better as False.
    mouse = Mouse()
    mouse.down = False
    mouse.button = 0

    circlex = 300
    circley = 300
    radius = 150 # only used for 'auto' code

    # Careful, changing width/height will add more points but not make it
    # stable; the cloth 'collapses' ... need to investigate code?
    c = CircleCloth(mouse, width=50, height=50)

    # Setting as false, we can run in manual mode and avoid clicking, which
    # means the cloth will update on its own (for gravity).
    run_equilibrium = False
    if run_equilibrium:
        print("Letting the cloth reach equilibrium...")
        for i in range(100):
            c.update()
            if i % 10 == 0:
                print("initial iteration", i)
        print("Done, hopefully at equilibrium, now do simulation...")

    # Simulate grabbing the gauze
    # --------------------------------------------------------------------------
    # Daniel: _this_ is why the (300,300) point by default has z-coordinate of
    # 0, because we asssume we have a tool which pinched it at that point! If
    # you enable this, the cloth animation appears to 'shink' towards (300,300)
    # due to tension pulling stuff there, but if we comment it out, the cloth
    # animation appears constant. (But the center now has the lowest
    # z-coordinate value, it's not zero.) Just the way matplotlib views it.
    # --------------------------------------------------------------------------
    c.pin_position(circlex, circley)
    tensioner = c.tensioners[0]

    plt.ion() # Interactive

    if not auto:
        fig = plt.figure()
        plot = fig.add_subplot(111)
        plot.set_title('manual')
        cid = fig.canvas.mpl_connect('button_press_event', mouse.clicked)
        rid = fig.canvas.mpl_connect('button_release_event', mouse.released)
        mid = fig.canvas.mpl_connect('motion_notify_event', mouse.moved)
   

    for i in range(400):
        # Clear the figure
        if i % 10 == 0:
            print("Iteration", i)
        plt.clf()

        # ---------- Daniel: looks cool :-) ----------
        #if i % 20 == 0:
        #    print("adding tension...")
        #    if i < 200:
        #        tensioner.tension(x=0.5, y=0.5, z=0)
        #    else:
        #        tensioner.tension(x=-0.5, y=-0.5, z=0)

        # ----------------------------------------------------------------------
        # Re-insert the points via scatter, w/potentially different colors.
        pts  = np.array([[p.x, p.y] for p in c.normalpts])
        cpts = np.array([[p.x, p.y] for p in c.shapepts])
        if len(pts) > 0:
            plt.scatter(pts[:,0], pts[:,1], c='g')
        if len(cpts) > 0:
            plt.scatter(cpts[:,0], cpts[:,1], c='b')
        ax = plt.gca()
        plt.axis([0, 600, 0, 600])
        # ax.set_axis_bgcolor('white')
        plt.pause(0.01)
        c.update()
        # Extra updates to allow cloth to respond to environment.
        for j in range(5):
            c.update()
        # ----------------------------------------------------------------------

        # simulate moving the mouse in a circle while cutting, overcut since no perception
        if auto:
            if i < 150:
                theta = 360.0/100.0 * i * np.pi / 180.0
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                mouse.move(x + circlex, y + circley)

    if not auto:
        fig.canvas.mpl_disconnect(cid)
        fig.canvas.mpl_disconnect(mid)
        fig.canvas.mpl_disconnect(rid)
