import numpy as np
import matplotlib.pyplot as plt
import pickle, copy, sys
import json
from cloth import *
from circlecloth import *
from tensioner import *
from mouse import *
import IPython
from mpl_toolkits.mplot3d import Axes3D


"""
A Simulation object that can be used to represent an ongoing experiment. It can be rendered by setting render=True on construction. See the main method for an example.
"""
class Simulation(object):

    def __init__(self, cloth, init=200, render=False, update_iterations=1, trajectory=None, multi_part=False):
        """
        Constructor takes in a cloth object and optionally, a nonnegative integer representing the amount of time to spend allowing
        the cloth to settle initially. Setting render=True will render the simulation. However, rendering will slow down iterations 
        by approximately 5x.
        """
        self.cloth = cloth
        self.mouse = self.cloth.mouse
        self.tensioners = self.cloth.tensioners
        self.render = render
        self.init = init
        self.bounds = cloth.bounds
        self.stored = False
        self.update_iterations = update_iterations
        self.trajectory = trajectory
        self.lastx, self.lasty, self.lastvec = None, None, None
        if not trajectory:
            self.trajectory = [(np.cos(deg) * 150 + 300, np.sin(deg) * 150 + 300) for deg in [3.6 * np.pi * i / 180.0 for i in range(100)]]
        self.multi_part = multi_part
        traj = []
        if multi_part:
            for i in range(len(trajectory)):
                for j in range(len(trajectory[i])):
                    traj.append(trajectory[i][j])
            self.trajectory = traj
        self.lastvec = None
        self.timer = 5
        self.fig = None

    def update(self, iterations=-1):
        """
        Updates the state of the cloth. Iterations signifies the amount of time to spend to allow the cloth to equilibrate.
        """
        if iterations < 0:
            iterations = self.update_iterations
        ret = sum([self.cloth.update() for _ in range(iterations)])
        if self.render:
            self.render_sim()
        return ret

    def render_sim(self):
        """ now matches demo.py matplotlib """
        if self.fig:
            plt.close(self.fig)
        nrows, ncols = 1, 2
        self.fig = plt.figure(figsize=(12*ncols,12*nrows))
        ax1 = self.fig.add_subplot(1, 2, 1)
        ax2 = self.fig.add_subplot(1, 2, 2, projection='3d')
        plt.tight_layout()
        ax1.cla()
        ax2.cla()
        pts  = np.array([[p.x, p.y, p.z] for p in self.cloth.normalpts])
        cpts = np.array([[p.x, p.y, p.z] for p in self.cloth.shapepts])
        if len(pts) > 0:
            ax1.scatter(pts[:,0], pts[:,1], c='g')
            ax2.scatter(pts[:,0], pts[:,1], pts[:,2], c='g')
        if len(cpts) > 0:
            ax1.scatter(cpts[:,0], cpts[:,1], c='b')
            ax2.scatter(cpts[:,0], cpts[:,1], cpts[:,2], c='b')
        ax2.set_zlim([0, 300]) # only for visualization purposes
        plt.show()

    def pin_position(self, x, y, max_displacement=False):
        """
        Pins a position on the cloth.
        """
        return self.cloth.pin_position(x, y, max_displacement)

    def unpin_position(self, x, y):
        """
        Unpins a previously pinned position on the cloth.
        """
        self.cloth.unpin_position(x, y)

    def move_mouse(self, x, y):
        """
        Moves the mouse object.
        """
        self.mouse.move(x, y)

    def reset(self):
        """
        Resets the simulation object.
        """
        print("Resetting simulation.")
        if not self.stored:
            self.cloth.reset()
            self.mouse = self.cloth.mouse
            self.tensioners = self.cloth.tensioners
            print("Initializing cloth")
            for i in range(self.init):
                self.cloth.simulate()
                if i % 10 == 0:
                    print(str(i) + '/' + str(self.init))
            self.stored = copy.deepcopy(self.cloth)
            self.update(0)
        else:
            self.cloth = copy.deepcopy(self.stored)
            self.mouse = self.cloth.mouse
            self.tensioners = self.cloth.tensioners
            self.bounds = self.cloth.bounds
            self.update(0)

    def write_to_file(self, fname):
        """
        Writes a simulation object to file.
        """
        f = open(fname, "w+")
        pickle.dump(self, f)
        f.close()

    def read_from_file(fname):
        """
        Load a simuation object from file.
        """
        f = open(fname, "rb")
        try:
            return pickle.load(f)
        except EOFError:
            print('Nothing written to file.')

    @property
    def score(self):
        return self.cloth.evaluate()
    


    # def __deepcopy__(self):
    #     """
    #     Returns a deep copy of self.
    #     """
    #     return copy.deepcopy(self)

def load_simulation_from_config(fname="config_files/default.json", shape_fn=None, trajectory=None, multipart=False, gravity=None, elasticity=False, noise=0):
    """
    Creates a Simulation object from a configuration file FNAME, and can optionally take in a SHAPE_FN or create one from discrete points saved to file. MULTIPART indicates whether or not the input trajectory consists of multiple subtrajectories.
    """
    with open(fname) as data_file:    
        data = json.load(data_file)
    mouse = data["mouse"]
    bounds = data["bounds"]
    bounds = (bounds["x"], bounds["y"], bounds["z"])
    mouse = Mouse(mouse["x"], mouse["y"], mouse["z"], mouse["height_limit"], mouse["down"], mouse["button"], bounds, mouse["influence"], mouse["cut"])
    cloth = data["shapecloth"]
    corners, blobs = None, None
    if "blobs" in data["options"].keys():
        corners = load_robot_points(data["options"]["blobs"][0])
        blobs = load_points(data["options"]["blobs"][1])
    if not shape_fn:
        corners = load_robot_points(cloth["shape_fn"][0])
        pts = load_robot_points(cloth["shape_fn"][1])
        shape_fn = get_shape_fn(corners, pts, True)
        if not trajectory:
            trajectory = load_trajectory_from_config(fname)
    if gravity == None:
        gravity = cloth["gravity"]
    if not elasticity:
        elasticity = cloth["elasticity"]
    cloth = ShapeCloth(shape_fn, mouse, cloth["width"], cloth["height"], cloth["dx"], cloth["dy"], 
        gravity, elasticity, cloth["pin_cond"], bounds, blobs, corners, noise=noise)
    simulation = data["simulation"]
    return Simulation(cloth, simulation["init"], simulation["render"], simulation["update_iterations"], trajectory, multipart)
