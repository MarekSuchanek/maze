import numpy as np
from collections import deque


class NoPathExistsException(Exception):
    pass

class MazeAnalysis:

    def __init__(self, maze):
        maze = np.atleast_2d(maze)
        self.distances = np.full(maze.shape, -1, dtype='int16')
        self.directions = np.full(maze.shape, b' ', dtype=('a', 1))
        np.place(self.directions, maze < 0, b'#')
        goals = np.asarray(np.where(maze == 1)).T
        stack_open = deque()
        shape = maze.shape
        for goal in goals:
            g = tuple(goal)
            self.distances[g] = 0
            self.directions[g] = b'X'
            stack_open.append((g, 0))
        dir_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        dir_chars = [b'^', b'v', b'<', b'>']
        while stack_open:
            (x, y), distance = stack_open.popleft()
            distance += 1
            for i in range(4):
                offset_x, offset_y = dir_offsets[i]
                neighbor = x + offset_x, y + offset_y
                if 0 <= neighbor[0] < shape[0] and 0 <= neighbor[1] < shape[1]:
                    if maze[neighbor] >= 0 and self.distances[neighbor] == -1:
                            self.distances[neighbor] = distance
                            self.directions[neighbor] = dir_chars[i]
                            stack_open.append((neighbor, distance))
        self.is_reachable = b' ' not in self.directions

    def path(self, row, column):
        if self.distances[row][column] < 0:
            raise NoPathExistsException
        dirs = {
            b'v': (1, 0),
            b'^': (-1, 0),
            b'>': (0, 1),
            b'<': (0, -1)
        }
        path = [(row, column)]
        while self.directions[row][column] != b'X':
            x, y = dirs[self.directions[row][column]]
            row += x
            column += y
            path.append((row, column))
        return path


def analyze(maze):
    return MazeAnalysis(maze)