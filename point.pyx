from math import sqrt
from constraint import *
from mouse import *
import numpy as np

"""
A class that simulates a point mass.
A cloth is made up of a collection of these interacting with each other.
"""
class Point(object):

    def __init__(self, mouse, x=0, y=0, z=0, bounds=(600, 600, 800),
                 gravity=-1000.0, elasticity=1.0, friction=0.99,
                 shape=0, identity=-1, noise=0, debug=False, min_z=None):
        """Initializes an instance of a particle.
        """
        self.mouse = mouse
        self.x,  self.y,  self.z  = x, y, z
        self.px, self.py, self.pz = x, y, z
        self.vx, self.vy, self.vz = 0, 0, 0
        self.bounds = bounds
        self.pinned = False
        self.gravity = gravity
        self.elasticity = elasticity
        self.friction = friction
        self.shape = shape
        self.identity = identity
        self.noise = noise
        self.debug = debug
        self.min_z = min_z
        self.constraints = []


    def get_scaled(self, size=300.0):
        """For rendering with PyOpenGL, requires points in range [-1,1].
        """
        scaled = [(self.x-150.0) / size,
                  (self.y-150.0) / size,
                  (self.z) / size]
        return scaled


    def __str__(self):
        str = "({:.3f}, {:.3f}, {:.3f})".format(self.x, self.y, self.z)
        return str

    def __repr__(self):
        return str(self)


    def add_constraint(self, pt, tear_dist=100):
        """Adds a constraint between this point and another point.
        """
        self.constraints.append(
            Constraint(self, pt, tear_dist=tear_dist, elasticity=self.elasticity)
        )


    def add_force(self, x, y, z=0):
        """Applies a force to itself, simply add to current vx, vy, vz.
        If point is pinned, we cannot change its spot. Hence velocities are 0.
        """
        if not self.pinned:
            self.vx, self.vy, self.vz = self.vx + x, self.vy + y, self.vz + z


    def resolve_constraints(self):
        """Resolve constraints wrt this point.
        """
        for constraint in self.constraints:
            constraint.resolve()
        

    def update(self, delta):
        """ APPLY VERLET INTEGRATION. Updates the point, takes in mouse input.
        Applies gravitational force; parameter can be tuned for varying results.
        The 0.99 here is friction, same as (1-damping) with damping = 0.01.

        Difference with some cloth sim code online is that we have to consider
        input from the mouse. Here, `self.{x,y,z}` is the CURRENT point, and
        `mouse.{x,y,z}` is where the mouse is pressed. For a given mouse, we
        need to update ALL points.
        
        Intuitively, points very far from the mouse are not affected, hence
        `mouse.influence` parameter (not used because I don't see button=1?) and
        `mouse.cut` (used!). If we're close enough to mouse, we simply remove
        constraints. Then, resolving constraints during next cloth update will
        remove the points.

        The delta is the time step. Brijen selected as 0.016? Ah, he informally
        tuned it.
        """
        if self.mouse.down:
            dx = self.x - self.mouse.x
            dy = self.y - self.mouse.y
            dz = self.z - self.mouse.z
            dist = sqrt(dx ** 2 + dy ** 2)
            if self.mouse.button == 1:
                print("  self.mouse.button == 1")
                if dist < self.mouse.influence:
                    self.px = self.x - (self.mouse.x - self.mouse.px) * 1.8
                    self.py = self.y - (self.mouse.y - self.mouse.py) * 1.8
            elif dist < self.mouse.cut and abs(dz) < self.mouse.height_limit:
                #print("  dist = {:.1f} < mouse.cut !!".format(dist))
                self.constraints = []

        # The only uniform external force we'll model is gravity. The other
        # external force is from the gripper/tensioner.
        self.add_force(0, 0, self.gravity)

        # ----------------------------------------------------------------------
        # Verlet integration (note the delta^2). Here, f=friction and is 1-d, or
        # 1-damping, where damping is a percentage between (0,1) that's usually
        # very small. Lowering `f` here means its harder to move the sheet.
        # ----------------------------------------------------------------------
        f = self.friction
        delta *= delta
        nx = self.x + (self.x - self.px) * f + ((self.vx / 2.0) * delta)
        ny = self.y + (self.y - self.py) * f + ((self.vy / 2.0) * delta)
        nz = self.z + (self.z - self.pz) * f + ((self.vz / 2.0) * delta)
        self.px, self.py, self.pz = self.x, self.y, self.z
        self.x,  self.y,  self.z  = nx, ny, nz

        # ----------------------------------------------------------------------
        # The CS 184 class says to reset forces. I think that's what this does.
        # https://cs184.eecs.berkeley.edu/sp18/article/35
        # ----------------------------------------------------------------------
        self.vx, self.vy, self.vz = 0, 0, 0

        if self.noise:
            self.x += (np.random.randn() * self.noise)
            self.y += (np.random.randn() * self.noise)
            self.z += (np.random.randn() * self.noise)

        # Makes sense to do this after Verlet, mirroring CS 184.
        if self.min_z is not None:
            self.z = max(self.min_z, self.z)
