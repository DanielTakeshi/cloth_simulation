import gym
from gym import error, spaces, utils
from gym.utils import seeding
from cloth import *
from mouse import *
from circlecloth import *
from simulation import *
import numpy as np

"""
An OpenAI Gym environment for the cloth smoothing experiments.
"""

class ClothEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    NUM_DIRECTIONS = 4 # cardinal directions for now, in order of N/E/S/W
    MAX_ACTIONS_TAKEN = 1000
    TENSIONX = 300
    TENSIONY = 300 # grasp at the corner for now
    MAX_Z_THRESHOLD = 5
    ITERS_PER_PULL = 50
    UPDATES_PER_MOVE = 6

    def __init__(self):
        self.mouse = Mouse(enable_cutting=False)
        self.cloth = CircleCloth(mouse)
        self.simulation = Simulation(cloth)
        self.tensioner = self.cloth.tensioners[0]
        self.num_points = self.cloth.initial_params[0][0] * self.cloth.initial_params[0][1]
        self.num_steps = 0

        # consider executing 1-2 gentle folds on cloth to get the starting state?

        # from Brijen's code for the observation space
        obslow = []
        obshigh = []
        for i in range(self.os_dim/5):
            obslow = obslow + [0, 0, -self.simulation.bounds[2], 0, 0]
            obshigh = obshigh + [self.simulation.bounds[0], self.simulation.bounds[1], self.simulation.bounds[2], 2, 1]

        self.obslow = np.array(obslow + [0, 0, -self.simulation.bounds[0], -self.simulation.bounds[1], -self.simulation.bounds[2]])
        self.obshigh = np.array(obshigh + [self.simulation.bounds[0], self.simulation.bounds[1], self.simulation.bounds[0], self.simulation.bounds[1], self.simulation.bounds[2]])

        self.action_space = spaces.Discrete(NUM_DIRECTIONS) # an action will be a fixed length pull in a cardinal direction
        self.observation_space = spaces.Box(self.obslow, self.obshigh)

        self.simulation.pin_position(TENSIONX, TENSIONY) # pin the corner
        self.corner_points = self.tensioner.grabbed_pts # remember which points constitute the corner

    def pull(self, i, direction):
        if i % 10 == 0:
            if i < 50:
                self.tensioner.tension(x=0.0, y=0.0, z=0.2)
            elif i < 50 + ITERS_PER_PULL:
                if direction == 0: # North
                    self.tensioner.tension(x=0.0, y=0.4, z=0.0)
                elif direction == 1: # East
                    self.tensioner.tension(x=0.4, y=-0.0, z=0.0)
                elif direction == 2: # South
                    self.tensioner.tension(x=0.0, y=-0.4, z=0.0)
                else: # West
                    self.tensioner.tension(x=-0.4, y=0.0, z=0.0)
            else:
                self.tensioner.unpin_position()

    def step(self, action):
        """Execute one grasp + pull. This will tension at the corner and 
        then pull in the chosen direction with ITERS_PER_PULL iterations.
        """
        self.tensioner.pin_points(self.corner_points)
        for i in range(ITERS_PER_PULL + 200): # include iterations for stabilizing before and after pull
            self.pull(i, action)
            for _ in range(UPDATES_PER_MOVE):
                self.cloth.simulate()
        self.num_steps += 1
        return self.state, self.reward(), self.terminal(), {}

    def get_valid_action(self):
        """Retrieves a random action among the actions that can actually be performed.
        """
        def valid(action):
            if action == 0:
                return (self.tensioner.y + ITERS_PER_PULL * UPDATES_PER_MOVE * 0.4) < self.simulation.bounds[1]
            elif action == 1:
                return (self.tensioner.x + ITERS_PER_PULL * UPDATES_PER_MOVE * 0.4) < self.simulation.bounds[0]
            elif action == 2:
                return (self.tensioner.y - ITERS_PER_PULL * UPDATES_PER_MOVE * 0.4) > 0
            else:
                return (self.tensioner.x - ITERS_PER_PULL * UPDATES_PER_MOVE * 0.4) > 0
        a = self.action_space.sample()
        while not valid(a):
            a = self.action_space.sample()
        return a


    def reward(self):
        """Sparse reward function that gives high reward on achieving the goal state.
        For the initial task of smoothness, we can see if the maximum Z is under some threshold.
        For a general configuration, we can sum the Euclidean distance of each cloth point from its goal.
        """
        for i in range(self.num_points):
            pt = self.cloth.pts[i]
            if (pt.z - cloth.min_z) > MAX_Z_THRESHOLD:
                return 0
        return 10000


    def terminal(self):
        return self.reward() > 500 or self.out_of_bounds() or self.num_steps > MAX_ACTIONS_TAKEN

    def reset(self):
        self.num_steps = 0
        self.simulation.reset()
        self.mouse = self.simulation.mouse
        self.cloth = self.simulation.cloth
        self.tensioner = self.simulation.pin_position(TENSIONX, TENSIONY)
        self.corner_points = self.tensioner.grabbed_pts
        return np.array(self.state)


    def render(self, mode='human', close=False):
        self.simulation.render_sim() # TODO: ensure the render method works

    def out_of_bounds(self):
        pts = self.state[:self.num_points * 5]
        ptsx = pts[::5]
        ptsy = pts[1::5]
        ptsz = pts[2::5]
        return (np.max(ptsx) > self.simulation.bounds[0] or np.min(ptsx) < 0 or np.max(ptsy) > self.simulation.bounds[1] or np.min(ptsy) < 0 or np.max(ptsz) > self.simulation.bounds[2] or np.min(ptsz) < -self.simulation.bounds[2])

    @property
    def state(self):
        lst = []
        for i in range(self.num_points):
            pt = self.cloth.pts[i]
            lst.append([pt.x, pt.y, pt.z, len(pt.constraints), pt.shape])
        return np.array(lst + [self.tensioner.x, self.tensioner.y] + list(self.tensioner.displacement))

