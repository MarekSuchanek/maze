import pytest
import numpy as np
import sys
import os
myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')


mazes_root = "tests/fixtures/mazes/"


def load_mazes(folder):
    result = {}
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and name.endswith('.csv'):
            maze_num = int(name[:-4])
            result[maze_num] = np.loadtxt(path, delimiter=',')
    return result


@pytest.fixture(scope='session')
def mazes():
    maze_db = {}
    for name in os.listdir(mazes_root):
        path = os.path.join(mazes_root, name)
        if os.path.isdir(path) and not name.startswith('.'):
            maze_db[name] = load_mazes(path)
    return maze_db

