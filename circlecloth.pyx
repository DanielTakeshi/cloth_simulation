from point import *
from cloth import *
from mouse import *

"""
A subclass of cloth, on which a circle pattern is drawn.
It also can be grabbed and tensioned.
"""
class CircleCloth(Cloth):

    def __init__(self, mouse=None, width=50, height=50, dx=10, dy=10,
                 centerx=300, centery=300, radius=150, gravity=-1000.0,
                 elasticity=1.0, pin_cond="default", bounds=(600, 600, 800),
                 minimum_z=None, physics_accuracy=5, time_interval=0.016):
        """A cloth on which a circle can be drawn.
        It can also be grabbed and tensioned at specific coordinates.
        
        Explanation of code (the 'visual' is what demo.py shows us):

        - Create height*width points, store in `self.pts`. Some of these are
          considered to be on the 'shape' (`shapepts`), and others aren't; we
          plot them with different colors.
        - Elasticity and gravity can be tuned.
        - Coordinate ranges bounded over (600x600). Not sure why we have 800
          here ... the visual is clearly 600x600 and we ignore z, all points
          have z=0 at start.
        - Have a fixed circle shape and we check if absolute distance from point
          to the center is close to the radius.
        - When we create points, we use an offset of 50 in the x and y
          direction, for making a gap. The origin is in the bottom left, bottom
          right of the visual, and the x-axis corresponds to the bottom row,
          y-axis corresonds to leftmost column, good. Surprisingly, if I don't
          have these offsets, the cloth isn't stable?
        - Gap of 10 (i.e., `dx`) between each point in vertical and horizontal
          directions.
        - Pinning: only if point is in top row or bottom row. The `y` in the fxn
          is actually the `i` in the for loop over y, not `point.y` which would
          be incorrect due to offsets and dx.
        - For constraints, recall the loop is over height then width, so we get
            (0,0), (1,0), ..., (w-1,0), (0,1), (1,1), ..., (w-1,1), (0,2), ...
          where the tuples represent (j,i), so (width,height), and w=width.
          I.e., create all points in row 0 (bottom), then points in row 1 (just
          above it), etc.
        - For each point, add constraint with itself and point below it.
          Exception: if we're at the first (bottom-most) row.
        - For each point, add constraint with itself and point to its left
          (i.e., `self.pts[-1]`, except if we're at leftmost column.
        - Seems like we do NOT have 'diagonal' or 'bending' constraints.
        - For the above constraints, the original point stores it in its own
          list; not sure about the 'other' point? I think not, which saves 2x
          memory on storing duplicate constraints. I also think each constraint
          is a simple spring mass model with friction.
        - `self.tensioners` has tensions, we add one at the beginning to keep
          the center of the gauze fixed, which is what a surgical robot would do
          (better to keep it fixed than to try and move), and we add more
          `pt.pinned=True` stuff.

        To make this rest on a table-like object, we should enforce a minimum
        z-coordinate limit. The z-coordinate naturally decreases (before
        stabilizing) as simulation proceeds due to gravity.

        Main difference with this and superclass is that we track circle points
        specifically, so we can visualize them later (and also to determine if a
        cutting point is close to the circle).
        """
        self.pts = []
        self.shapepts = []
        self.normalpts = []
        self.tensioners = []
        self.bounds = bounds
        if not mouse:
            mouse = Mouse(bounds=bounds)
        self.mouse = mouse
        self.physics_accuracy = physics_accuracy
        self.time_interval = time_interval

        # Should we multiply sqrt(2) to thresh dist? 100 is normal thresh dist.
        diag_dist = 100 * np.sqrt(2)

        # Use this fxn to simulate cloth pinned along top and bottom.
        if pin_cond == "default":
            pin_cond = lambda x, y, height, width: y == 0
            ##pin_cond = lambda x, y, height, width: y == height - 1 or y == 0

        for i in range(height):
            for j in range(width):
                #print("Adding point, (x,y): ({},{})".format(j,i))
                pt = Point(mouse,
                           x = 50 + dx*j,
                           y = 50 + dy*i,
                           z = 0,
                           min_z=minimum_z,
                           gravity=gravity,
                           elasticity=elasticity,
                           bounds=bounds)

                # Constraint, current pt and pt below it, except for bottom-most row
                if i > 0:
                    idx = width * (i-1) + j
                    pt.add_constraint(self.pts[idx])

                # Constraint, current pt and pt to its left, except for leftmost column
                if j > 0:
                    pt.add_constraint(self.pts[-1])

                # --------------------------------------------------------------
                # Not sure if these are working as intended? Do we actually have
                # a Hooke's law in the constraints? Seems different? At least
                # the resting length makes sense, it's always 10 for structural
                # constraints and 10*sqrt(2) for diagonals, when I print them.
                # --------------------------------------------------------------

                # Diagonal constraint 1, pt and the pt to lower left
                if j > 0 and i > 0:
                    idx = width * (i-1) + j - 1
                    pt.add_constraint(self.pts[idx], tear_dist=diag_dist)

                # Diagonal constraint 2, pt and the pt to lower right
                if j < width-1 and i > 0:
                    idx = width * (i-1) + j + 1
                    pt.add_constraint(self.pts[idx], tear_dist=diag_dist)

                # Pin some points according to `pin_cond`.
                if pin_cond(j, i, height, width):
                    pt.pinned = True

                if abs((pt.x - centerx) **2 + (pt.y - centery) ** 2 - radius **2) < 2000:
                    self.shapepts.append(pt)
                else:
                    self.normalpts.append(pt)
                self.pts.append(pt)

        self.pts, self.normalpts, self.shapepts = \
                set(self.pts), set(self.normalpts), set(self.shapepts)
        self.initial_params = [(width, height), (dx, dy), (centerx, centery, radius),
                               gravity, elasticity, pin_cond]


    def update(self):
        """Update function updates the state of the cloth after a time step.
        Updates ALL points in `self.pts`, via each `pt.update(...)` call.

        REMOVES points if there are no more constraints for it. That's why the
        lower left point is removed, because there aren't constraints the way
        it's set up above. Constraints 'go down' and 'go left', intuitively.
        We made points as sets, so removal should be O(1).

        The `physics_accuracy` term: when resolving a constraint we affect other
        constraints that need to be updated? Probably. Calls to resolve
        constraints may remove items from different `pt.constraints` lists. Note
        call order: call the _point_'s method, which first resolves individual
        constraints before resolving boundary constraints. (In our case we
        really don't need boundary constraints.)

        In CS 184 they computed the forces and then applied the constraints.
        Ordering of those two shouldn't matter.
        """
        physics_accuracy = self.physics_accuracy
        time_interval = self.time_interval

        for pt in self.pts:
            pt.update(time_interval)

        for i in range(physics_accuracy):
            for pt in self.pts:
                pt.resolve_constraints()

        toremoveshape, toremovenorm = [], []
        for pt in self.pts:
            if pt.constraints == []:
                print("removing pt (x, y, z):  ({:.1f}, {:.1f}, {:.1f})".format(
                        pt.x, pt.y, pt.z))
                if pt in self.shapepts:
                    toremoveshape.append(pt)
                else:
                    toremovenorm.append(pt)
        for pt in toremovenorm:
            self.pts.remove(pt)
            self.normalpts.remove(pt)
        for pt in toremoveshape:
            self.pts.remove(pt)
            self.shapepts.remove(pt)


    def reset(self):
        """Resets cloth to its initial state.
        (Daniel: better figure out an easier way to do this than copy a bunch of
        the init code ...)
        """
        self.mouse.reset()
        width, height = self.initial_params[0]
        dx, dy = self.initial_params[1]
        centerx, centery, radius = self.initial_params[2]
        gravity = self.initial_params[3]
        elasticity = self.initial_params[4]
        pin_cond = self.initial_params[5]
        self.pts = []
        self.shapepts = []
        self.normalpts = []
        self.tensioners = []
        for i in range(height):
            for j in range(width):
                pt = Point(self.mouse, 50 + dx * j, 50 + dy * i, gravity=gravity, elasticity=elasticity)
                if i > 0:
                    pt.add_constraint(self.pts[width * (i - 1) + j])
                if j > 0:
                    pt.add_constraint(self.pts[-1])
                if pin_cond(j, i, height, width):
                    pt.pinned = True
                if abs((pt.x - centerx) **2 + (pt.y - centery) ** 2 - radius **2) < 2000:
                    self.shapepts.append(pt)
                else:
                    self.normalpts.append(pt)
                self.pts.append(pt)
        self.pts, self.normalpts, self.shapepts = set(self.pts), set(self.normalpts), set(self.shapepts)
