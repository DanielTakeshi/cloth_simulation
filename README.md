# cloth_simulation

This repository contains scripts used to simulate cloth physics in 3D under various conditions and interactions.

Questions to consider and possible TODOs:

- Why is elasticity implemented the way it is, and why does it work?
- Gravity constant seems very arbitrary, not sure how accurate it has to be for
  physics modeling if we're using the z coordinate?
- Why not diagonal constraints? I thought that would cause a collapse? Update:
  it does, if you only pin one side, it makes the cloth collapse! Will need to
  add diagonal constraints.
- How can we support actions like grasping and pulling? How can we adapt the
  tension code so that it correctly lifts the points and then pulls, so we have
  overlap?
- Better 3D viewer? That would help the above.

Resolved:

- What's with vx, vy, vz? Seems like that contains the acceleration term needed
  for Verlet integration? (Update: looks like it's a naming error, it's clearly
  acceleration.)
- The constant of 0.016 for `pt.update(0.016)` was simply hand-tuned.


## Files, Scripts, and Directories:

### point.py
Contains the Point class, which represents a point mass.

### constraint.py
Contains the Constraint class, which represents a relationship between two points that the points try to maintain.

### cloth.py
Contains the Cloth class, which represents a collection of points structured into a rectangular grid in 3D along with perpendicular constraints for each point. The cloth is pinned along the top and bottom by default. It can also be grabbed and tensioned by a tensioner object.

### circlecloth.py
Contains the CircleCloth class which extends the Cloth class. It is similar, but also has a circular pattern drawn on it with specified dimensions/location, and can be grabbed and tensioned as well. The cloth is pinned along the top and bottom by default as well.

### shapecloth.py
Contains a ShapeCloth class which extends the Cloth class. Similar to the CircleCloth class, it has a pattern drawn on it. It takes in a function that specifies whether or not a point is on the outline.

### tensioner.py
Contains the Tensioner class which can be used to grab a position on the cloth, and tug it in a direction.

### mouse.py
Contains the Mouse class, which can be used as a medium through which a physical or virtual mouse can interact with a cloth.

### util.py
Contains utility functions relating to the scripts and objects in the repository.

### demo.py
Contains a main method that can be run out of the box to view a demo of the code in action.

#### To run:

Run python setup.py build_ext --inplace

To run an trial that cuts a predefined trajectory on a Cloth object, run "python demo.py" in the terminal from within the directory containing the scripts.
To run a trial that takes in the physical mouse's location on the canvas as the location of the scissors, run "python demo.py manual" in the terminal from within the directory containing the scripts.

### simulation.py
Contains a simulation object class that can be used for running simulations with different cloth objects. See the main method for example usage.

#### To run:

Run python setup.py build_ext --inplace

To run a trial that cuts a predefined trajectory on a CircleCloth object, run "python simulation.py" in the terminal from within the directory containing the scripts.

### environment_rep

A package containing environments defined for various experiments with various frameworks such as RLPy or rllab.

### config_files

A folder containing configuration files that can be used to generate simulation objects. An example is default.json.

### Dependencies

* Python 2.7
* Matplotlib
* Numpy
* Scipy 0.18.0 or newer
* Cython
* IPython

### Optional Dependencies

Dependencies that are only required for specific scripts in the repository, but not for core functionality.

* rllab
* RLPy
* OpenAI Gym
* ROS
* dvrk_utils




## Figures


Brijen used elasticity of 1.0 by default. If you do 0.0, the structure appears
very rigid with and without diagonal constraints (assuming diagonal constraints
were implemented correctly...):

![](figs/cloth-elasticity-0.0.png)

and if it's 2.0 it collapses, with and without the same diagonal constraints.


![](figs/cloth-elasticity-2.0.png)
