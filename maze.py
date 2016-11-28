import numpy as np
from collections import deque


class NoPathExistsException(Exception):
    pass


class MazeAnalysis:

    def __init__(self, maze):
        if type(maze).__module__ != np.__name__:  # if not numpy matrix, make it numpy matrix
            maze = np.array(maze)
        maze = np.atleast_2d(maze)
        self.distances = np.full(maze.shape, -1, dtype='int16')
        self.directions = np.full(maze.shape, b' ', dtype=('a', 1))
        np.place(self.directions, maze < 0, b'#')
        indices = np.where(maze == 1)
        goals = list(zip(indices[0], indices[1]))
        stack_open = deque()
        shape = maze.shape
        for goal in goals:
            self.distances[goal] = 0
            self.directions[goal] = b'X'
            stack_open.append((goal, 0))
        dir_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        dir_chars = [b'^', b'v',b'<', b'>']
        while stack_open:
            (x, y), distance = stack_open.popleft()
            distance += 1
            for i in range(4):
                offset_x, offset_y = dir_offsets[i]
                new_place = x + offset_x, y + offset_y
                if 0 <= new_place[0] < shape[0] and 0 <= new_place[1] < shape[1]:
                    if maze[new_place] >= 0 and self.distances[new_place] == -1:
                            self.distances[new_place] = distance
                            self.directions[new_place] = dir_chars[i]
                            stack_open.append((new_place, distance))
        self.is_reachable = not (self.directions == b' ').any()

    def path(self, row, column):
        if self.distances[row][column] < 0:
            raise NoPathExistsException
        dir_offsets = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        dir_chars = [b'v', b'^',b'>', b'<']
        path = []
        path.append((row, column))
        while self.directions[row][column] != b'X':
            x, y = dir_offsets[dir_chars.index(self.directions[row][column])]
            row += x
            column += y
            path.append((row, column))
        return path


def analyze(maze):
    return MazeAnalysis(maze)


if __name__ == '__main__':
    ma = MazeAnalysis(np.array(
        [
            [7,-1,-1,7],
            [7,7,7,-1],
            [7,-1,7,7],
            [7,-1,-1,7],
            [1,7,-1,1],
        ]
    ))
    print(ma.distances)
    print(ma.directions)
    print(ma.is_reachable)
    print(ma.path(0, 0))
    print(ma.path(4, 0))
    print(ma.path(0, 1))
