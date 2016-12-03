import numpy as np
cimport numpy as np
import cython
from libcpp.queue cimport queue
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp.map cimport map

cdef struct coords:
    int x
    int y

cdef struct qitem:
    int x
    int y
    int distance


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef flood(maze):
    cdef int x, y, i, w, h
    cdef queue[qitem] q
    cdef np.ndarray[np.int16_t, ndim=2] distances
    cdef np.ndarray[np.int8_t, ndim=2] directions
    maze = np.atleast_2d(maze)
    w = maze.shape[0]
    h = maze.shape[1]
    distances = np.full((w, h), -1, dtype='int16')
    directions = np.full((w, h), b' ', dtype=('a', 1))
    np.place(directions, maze < 0, b'#')
    goals = np.asarray(np.where(maze == 1)).T
    for goal in goals:
        g = tuple(goal)
        distances[g] = 0
        directions[g] = b'X'
        q.push(qitem(g[0],g[1],0))
    cdef coords *dir_offsets = [coords(1, 0), coords(-1, 0), coords(0, 1), coords(0, -1)]
    cdef np.int8_t *dir_chars = [b'^', b'v', b'<', b'>']
    while not q.empty():
        item = q.front()
        q.pop()
        for i in range(4):
            offset = dir_offsets[i]
            x = item.x + offset.x
            y = item.y + offset.y
            if 0 <= x < w and 0 <= y < h:
                if maze[x, y] >= 0 and distances[x, y] == -1:
                    distances[x, y] = item.distance+1
                    directions[x, y] = dir_chars[i]
                    q.push(qitem(x, y, item.distance+1))
    return distances, directions


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef build_path(np.ndarray[np.int8_t, ndim=2] directions, int row, int column):
    if directions[row, column] == b'#' or directions[row, column] == b' ':
        raise NoPathExistsException
    cdef vector[pair[int,int]] path
    cdef map[char,coords] dirs
    dirs.insert(pair[char,coords](b'v', coords(1, 0)))
    dirs.insert(pair[char,coords](b'^', coords(-1, 0)))
    dirs.insert(pair[char,coords](b'>', coords(0, 1)))
    dirs.insert(pair[char,coords](b'<', coords(0, -1)))
    path.push_back(pair[int,int](row, column))
    while directions[row, column] != b'X':
        d = dirs[directions[row, column]]
        row += d.x
        column += d.y
        path.push_back(pair[int,int](row, column))
    return path


cdef class NoPathExistsException(Exception):
    pass


class MazeAnalysis:

    def __init__(self, maze):
        self.distances, self.directions = flood(maze)
        self.is_reachable = b' ' not in self.directions

    def path(self, row, column):
        return build_path(self.directions, row, column)


cpdef analyze(maze):
    return MazeAnalysis(maze)
