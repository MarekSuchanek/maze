# The Maze

*Maze analyzer, editor and game.*

[![License](https://img.shields.io/badge/license-GNU GPL v3-blue.svg)](LICENSE)
[![Build Status](https://travis-ci.com/MarekSuchanek/maze.svg?token=XD73y3snHDycemSiHx3H&branch=master)](https://travis-ci.com/MarekSuchanek/maze)
[![Version](https://img.shields.io/badge/release-v0.4-orange.svg)](setup.py)


This project is series of tasks for [MI-PYT](https://github.com/cvut/MI-PYT) 
subject from [FIT CTU in Prague](https://fit.cvut.cz).

**Analysis** takes a maze (matrix of numbers), where:

* wall (impassable cell) -> `number < 0`
* accessible cell -> `number >= 0`
* goal cell -> `number == 1` (one or more)

Analysis of maze produces an object with ([original task formulation](https://github.com/cvut/MI-PYT/blob/master/tutorials/07_numpy.md)):

* attribute `distances` = each cell contains shortest path len to (some)
  goal (goal contains 0). If it is not possible to get to any goal from
  the cell or the cell is a wall, then value is -1.
* attribute `directions` = visualizes the path to goal via `'<'`, `'>'`,
  `'v'`, `'^'` characters, `'X'` for goal cell, `'#'` for wall and `' '` 
  (space) for cells without path to any goal.
* attribute `is_reachable` = single truth value if any goal is reachable
  from all non-wall cells.
* method `path(row, column)` = build array of coords representing the 
  shorest path (or one of shortests paths if there are more). If no path
  exists from specified start, then `NoPathExistsException` is raised.

**Maze GUI** is PyQt simple user interface for creating, browsing, 
storing and loading mazes.

## Installation

Module is developed for Python 3.5 (update or use `venv` if you don't 
have this version of Python). Then you can install dependencies via:

```
pip install -r requirements.txt
```

For speedup is analysis written in Cython so you need to compile it with
via:

```
python setup.py develop
```

or

```
python setup.py install
```

## Usage

### Maze analysis

```
>>> from maze import analyze
>>> a = analyze([[5,-1,1,],[7,-1,7],[3,3,3]])
>>> a
<maze.MazeAnalysis object at 0x7f44dbd99e10>
>>> a.distances
array([[ 6, -1,  0],
       [ 5, -1,  1],
       [ 4,  3,  2]], dtype=int16)
>>> a.directions
array([[b'v', b'#', b'X'],
       [b'v', b'#', b'^'],
       [b'>', b'>', b'^']], 
      dtype='|S1')
>>> a.is_reachable
True
>>> a.path(0,0)
[(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2)]
>>> a.path(1,1)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/sushi/Projects/CVUT/PYT-Maze/maze.py", line 43, in path
    raise NoPathExistsException
maze.NoPathExistsException
```

### Maze GUI

```
python -m maze
```

Within GUI you can:
* create new maze (with specified width, height and fill type)
* load/save maze to/from file
* add elements to the maze (grass, walls, goals, dudes)
  * elements can be dragged by holding mouse button, moving and
    then releasing the button
  * removing element by putting grass on that field
* zoom in/out (via toolbar actions and/or `Ctrl + <wheel>`)
* there is some info with credits and info in _About_ (`F1`)
  * based on [MI-PYT](https://github.com/cvut/MI-PYT) tutorial by [@hroncok](https://github.com/hroncok) and [@encukou](https://github.com/encukou)
  * graphics by [Kenney](http://kenney.nl/) (available at [OpenGameArt.org](http://opengameart.org/users/kenney))
* shortest path show up (if exists) for each dude in maze
* there is some useful basic information in the status bar (position, 
  size, ...)

### Game mode

You can switch from _edit_ mode to _game_ mode (Ctrl+SPACE) where is your task to protect 
the castle (or more castles) against dudes by building and destroying simple walls (not 
strong walls). When any dude reaches any goal game end. By the way, you cannot cut dude from 
goal - it would be too simple!

Types of dudes (enemies):
* **Speedy** - In free time Speedy exercise a lot and thanks to that he is constantly 75% 
  faster than other dudes (except Accel'e'rator).
* **Acccel'e'rator** - His only desire is to reach the castle first. At start it might doesn't
  look that way, but beware - he can speed up a lot! At each step he can increase his speed by 
  20% of default speed with probability 10%. His maximal speed is 80% faster then other dudes 
  (except Speedy).
* **Le Parkour** - Usually hangs out in big cities so walls are not and obstacle for him. He 
  can simply jump over 1 wall after walking at least 5 steps if place behind the wall is 
  accessible and closer to the goal. But can't jump to place closer to goal by more than 5 
  steps.
* **Tele del Porto** - He has incalculable abilty to teleport himself just by the force of 
  his own will to random accessible place with probability 20%. His will is usually kinda weak so 
  the place can be closer and also farther to the goal but never closer than 5 steps. Minimal 
  distance of the teleportation is 5. Teleportation can fail if Tele is unable to pick suitable
  target within 100 random picks, then he will only shiver.
* **Scatterbrain** - Total lunetic who escaped asylum. His best friend is chaos so he can choose 
  other direction than is the shortest one with probability 25%.

## Testing

After installing dependencies and compilation you can run (analysis) 
tests with `pytest`:

```
python -m pytest
```

## License

This project is licensed under the GNU GPL v3 License - see the [LICENSE](LICENSE)
file for more details.
