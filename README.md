# Maze analyzer

[![License](https://img.shields.io/badge/license-GNU GPL v3-blue.svg)](LICENSE)
[![Build Status](https://travis-ci.com/MarekSuchanek/maze.svg?token=XD73y3snHDycemSiHx3H&branch=master)](https://travis-ci.com/MarekSuchanek/maze)
[![Version](https://img.shields.io/badge/release-v0.3-orange.svg)](setup.py)


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

## Testing

After installing dependencies and compilation you can run (analysis) 
tests with `pytest`:

```
python -m pytest
```

## License

This project is licensed under the GNU GPL v3 License - see the [LICENSE](LICENSE)
file for more details.
