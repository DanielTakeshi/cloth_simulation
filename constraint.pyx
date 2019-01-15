from math import sqrt
from point import *

"""
A class to represent interactions between Points.
"""

class Constraint(object):

    def __init__(self, p1=None, p2=None, tear_dist=100, elasticity=1.0):
        """
        Constraint between two points that attempts to maintain a fixed distance
        between points and tears if a threshold is passed. AH, `self.length` is
        the distance originally set ... I _think_ this will still work with
        diagonal constraints because self.length will be longer. But, should we
        multiply the tear distance by a factor of sqrt(2)?

        In demo code, p1 is either below p2 (lower y value) or to the left of p2
        (lower x value). It's only one of these; we don't have diagonal
        constraints.

        Daniel: when tensioning from the center of the (600,600) grid, I can't
        get a cut. But if I tension from a lower left corner and pull towards
        the upper right, then there are some cuts. :-) For our case, we probably
        don't want cuts, so set `tear_dist` to be super high.
        """
        self.p1, self.p2 = p1, p2
        self.length = sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2)
        self.tear_dist = tear_dist
        self.elasticity = elasticity


    def resolve(self):
        """
        Updates the points in the constraint based on how much the constraint
        has been violated. Elasticity is a parameter that can be tuned that
        affects the response of a constraint.
        
        If a point is NOT pinned, then we change its current (x,y,z). Note, p1
        gets added, p2 gets subtracted because of the way we defined delta. In
        both cases the math is: (pt)*(1+diff) - other_pt. (But, I don't get why
        this formula works...)

        In a cloth, we iterate through all points (multiple times!) and for each
        point, we call its method to resolve constraints, which call this. THEN
        we do another iteration over all points to *update* via Verlet Int.
        """
        cdef double delta[3]
        delta[0] = self.p1.x - self.p2.x
        delta[1] = self.p1.y - self.p2.y
        delta[2] = self.p1.z - self.p2.z
        cdef double dist = sqrt(delta[0] ** 2 + delta[1] ** 2 + delta[2] ** 2)
        cdef double diff = (self.length - dist) / float(dist) * 0.5 * self.elasticity

        if dist > self.tear_dist:
            self.p1.constraints.remove(self)

        # Elasticity, usually pick something between 0.01 and 1.5
        cdef double px = diff * delta[0]
        cdef double py = diff * delta[1]
        cdef double pz = diff * delta[2]

        if not self.p1.pinned:
            self.p1.x, self.p1.y, self.p1.z = self.p1.x + px, self.p1.y + py, self.p1.z + pz

        if not self.p2.pinned:
            self.p2.x, self.p2.y, self.p2.z = self.p2.x - px, self.p2.y - py, self.p2.z - pz
