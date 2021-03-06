import pytest
import numpy as np
from maze import analyze, NoPathExistsException


def inside(coords, matrix):
    return 0 <= coords[0] < matrix.shape[0] and \
           0 <= coords[1] < matrix.shape[1]


def verify_matrices(maze, analysis):
    maze = np.atleast_2d(maze)
    dir_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    dir_chars = [b'v', b'^', b'>', b'<']
    is_reachable = True
    for x, y in np.ndindex(maze.shape):
        if maze[x][y] < 0:
            assert analysis.distances[x][y] == -1, "Wall with distance"
            assert analysis.directions[x][y] == b'#', "Wall with direction"
        elif maze[x][y] == 1:
            assert analysis.distances[x][y] == 0, "Goal with wrong distance"
            assert analysis.directions[x][y] == b'X', "Goal with wrong direction"
        elif analysis.directions[x][y] == b' ':
            is_reachable = False
            assert analysis.distances[x][y] == -1, "Unreachable field with distance"
            for i in range(4):
                ox, oy = dir_offsets[i]
                new_place = x + ox, y + oy
                if inside(new_place, maze):
                    assert analysis.directions[new_place] == b' ' or \
                           analysis.directions[new_place] == b'#', \
                           "Not really unreachable field"
            assert not analysis.is_reachable, "False is_reachable (witness found)"
        else:
            direction_correct = False
            distance_correct = False
            for i in range(4):
                ox, oy = dir_offsets[i]
                new_place = x + ox, y + oy
                if inside(new_place, maze) and maze[new_place] >= 0:
                    nxt = analysis.distances[x][y] - 1 == analysis.distances[new_place]
                    prv = analysis.distances[x][y] + 1 == analysis.distances[new_place]
                    eql = analysis.distances[x][y] == analysis.distances[new_place]
                    assert nxt or prv or eql, \
                        "Neighboring field differs by more than 1 step"
                    if next:
                        distance_correct = True
                        if not direction_correct:
                            direction_correct = analysis.directions[x][y] == dir_chars[i]
            assert distance_correct or maze[x][y] == 1, "No next step around although not goal yet"
            assert direction_correct, "Direction leading wrong way"
    assert is_reachable == analysis.is_reachable, "False is_reachable (no witness found)"


def verify_path(maze, analysis, row, column):
    path = analysis.path(row, column)
    last = path.pop(0)
    assert analysis.distances[last] == len(path), "Path length not corresponding to distance"
    assert maze[last] >= 0, "Path via wall"
    assert last[0] == row, "Wrong start row coord"
    assert last[1] == column, "Wrong start column coord"
    while len(path) > 0:
        act = path.pop(0)
        assert (abs(last[0]-act[0]) == 1) ^ (abs(last[1]-act[1])) == 1, "Path contains too big or too small step"
        assert maze[act] >= 0, "Path via wall"
        assert analysis.distances[act] == len(path), "Path length not corresponding to distance"
        last = act
    assert maze[last] == 1, "Does not lead to goal"


@pytest.mark.parametrize('mtype,number', [
    ('simple', 1), ('simple', 2), ('simple', 3), ('simple', 4),
    ('bounds', 1), ('bounds', 2), ('bounds', 3), ('bounds', 4),
    ('multigoal', 1), ('multigoal', 2), ('multigoal', 3), ('multigoal', 4),
    ('unreachable', 1), ('unreachable', 2)
])
def test_analysis(mazes, mtype, number):
    maze = mazes[mtype][number]
    analysis = analyze(maze)
    verify_matrices(maze, analysis)


@pytest.mark.parametrize('mtype,number,row,column', [
    ('simple', 1, 1, 0), ('simple', 1, 1, 4), ('simple', 1, 3, 1),
    ('multigoal', 4, 0, 0), ('multigoal', 4, 3, 0)
])
def test_paths(mazes, mtype, number, row, column):
    maze = mazes[mtype][number]
    analysis = analyze(maze)
    verify_path(maze, analysis, row, column)


@pytest.mark.parametrize('mtype,number,row,column', [
    ('simple', 1, 0, 0), ('multigoal', 4, 4, 0),
    ('unreachable', 1, 0, 0), ('unreachable', 2, 1, 1),
])
def test_paths_exception(mazes, mtype, number, row, column):
    maze = mazes[mtype][number]
    analysis = analyze(maze)
    with pytest.raises(NoPathExistsException):
        analysis.path(row, column)
