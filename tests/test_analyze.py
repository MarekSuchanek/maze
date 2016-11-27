import pytest
import numpy as np
from maze import analyze


mazes_path = "tests/fixtures/mazes/{0}/{1:02d}.csv"


def verify_matrices(maze, analysis):
    maze = np.atleast_2d(maze)
    dir_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    dir_chars = [b'v', b'^',b'>', b'<']
    for x, y in np.ndindex(maze.shape):
        if maze[x][y] < 0:
            assert analysis.distances[x][y] == -1, "Wall with distance"
            assert analysis.directions[x][y] == b'#', "Wall with direction"
            assert not analysis.is_reachable[x][y], "Wall is reachable"
        elif maze[x][y] == 1:
            assert analysis.distances[x][y] == 0, "Goal with wrong distance"
            assert analysis.directions[x][y] == b'X', "Goal with wrong direction"
            assert analysis.is_reachable[x][y], "Goal is unreachable"
        elif analysis.directions[x][y] == b' ':
            assert analysis.distances[x][y] == -1, "Unreachable field with distance"
            assert not analysis.is_reachable[x][y], "Unreachable field is reachable"
            for i in range(4):
                ox, oy = dir_offsets[i]
                new_place = x + ox, y + oy
                if 0 <= new_place[0] < maze.shape[0] and \
                   0 <= new_place[1] < maze.shape[1]:
                    assert analysis.directions[new_place] == b' ' or \
                           analysis.directions[new_place] == b'#', \
                           "Not really unreachable field"
        else:
            direction_correct = False
            distance_correct = False
            for i in range(4):
                ox, oy = dir_offsets[i]
                new_place = x + ox, y + oy
                if 0 <= new_place[0] < maze.shape[0] and \
                   0 <= new_place[1] < maze.shape[1] and \
                   maze[new_place] >= 0:
                    next = analysis.distances[x][y] - 1 == analysis.distances[new_place]
                    prev = analysis.distances[x][y] + 1 == analysis.distances[new_place]
                    same = analysis.distances[x][y] == analysis.distances[new_place]
                    assert next or prev or same, \
                        "Neighboring field differs by more than 1 step"
                    if next:
                        distance_correct = True
                        if not direction_correct:
                            direction_correct = analysis.directions[x][y] == dir_chars[i]
            assert distance_correct or maze[x][y] == 1, "No next step around although not goal yet"
            assert direction_correct, "Direction leading wrong way"
            assert analysis.is_reachable[x][y], "Reachable field is unreachable"


def verify_path(maze, analysis,path):
    length = len(path)
    last = path.pop()
    assert maze[last] >= 0, "Path via wall"
    assert analysis.distances[last] == length, "Path length not corresponding to distance"
    for act in path:
        assert abs(last[0]-act[0]) == 1 ^ abs(last[1]-act[1]) == 1
        assert maze[act] >= 0, "Path via wall"
        length -= 1
        assert analysis.distances[act] == length, "Path length not corresponding to distance"
        last = act
    assert maze[last] == 1, "Does not lead to goal"


def load_maze(type, number):
    fname = mazes_path.format(type, number)
    return np.loadtxt(fname, delimiter=',')


@pytest.mark.parametrize('mtype,number', [
    ('simple', 1), ('simple', 2), ('simple', 3),
    ('bounds', 1), ('bounds', 2), ('bounds', 3), ('bounds', 4),
    ('multigoal', 1), ('multigoal', 2), ('multigoal', 3), ('multigoal', 4)
])
def test_analysis(mtype, number):
    maze = load_maze(mtype, number)
    analysis = analyze(maze)
    verify_matrices(maze, analysis)


def test_paths():
    pass


def test_paths_exception():
    pass

