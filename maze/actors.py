import asyncio
import contextlib
import time
import random

random.seed(time.monotonic())


class Actor:
    """
    Maze game actor
    Public domain: https://github.com/cvut/MI-PYT/blob/master/tutorials/10-async/actor.py
    Authors: @hroncok, @encukou (GitHub)
    """
    def __init__(self, grid, row, column, kind):
        """Coroutine-based actor on a grid
        :param grid:
            The grid this actor moves on. Must have the following attributes:
            * ``update_actor(actor)``: Called to mark the space currently
                occupied by the actor as "dirty" (needs redrawing)
            * ``cell_size``: size of a grid cell, in pixels (used to optimize
                animations)
            * ``directions``: a NumPy array of directions (ASCII bytes),
                containing ``b'v'``, ``b'<'``, ``b'>'``, ``b'^'`` depending
                on where the actor should move to from a particular cell.
                Only used in the default implementation of ``behavior``.
            This is stored in an attribute with the same name.
        :param row:
        :param column:
            The initial position of the actor.
            These are stored in attributes with the same names, and are updated
            regularly.
            When the actor is currently moving, the values are floats.
        :param kind:
            Any data for use by the grid drawing code.
            This is stored in an attribute with the same name.
        The attribute ``task`` will hold an ``asyncio.Task`` object
        corresponding to the actor's behavior. Cancel it when done.
        """
        self.row = row
        self.column = column
        self.kind = kind
        self.grid = grid
        self.score = 0
        self.task = asyncio.ensure_future(self.behavior())
        self.in_goal = False

    async def behavior(self):
        """Coroutine containing the actor's behavior
        The base implementation follows directions the actor is standing on.
        If there is no directions (e.g. standing on a wall, unreachable space,
        or on the goal), the actor jumps repeatedly.
        To be reimplemented in subclasses..
        """
        while not self.grid.game_over:
            shape = self.grid.analysis.directions.shape
            row = int(self.row)
            column = int(self.column)
            if 0 <= row < shape[0] and 0 <= column < shape[1]:
                direction = self.grid.analysis.directions[row, column]
            else:
                direction = b'?'

            self.in_goal = direction == b'X'

            if direction == b'v':
                await self.step(1, 0)
            elif direction == b'>':
                await self.step(0, 1)
            elif direction == b'^':
                await self.step(-1, 0)
            elif direction == b'<':
                await self.step(0, -1)
            else:
                await self.jump()

    def _progress(self, duration):
        """Iterator that yields progress from 0 to 1 based on time
        In each iteration, yields a number based on the current time:
        * 0.0 at the time the generator was started;
        * 1.0 at start time plus ``duration`` seconds (end time)
        * for the time in between, a linearly interpolated number between 0...1
        It is not guaranteed that 1.0 will be yielded on the last iteration.
        When using this with a for-loop, you probably need to put
        a sleep/delay into each iteration.
        """
        last = start = time.monotonic()
        while True:
            now = time.monotonic()
            self.score += (now - last)
            last = now
            p = (now - start) / duration
            if p > 1:
                return
            yield p

    @contextlib.contextmanager
    def _update_context(self):
        """Context manager for updating the actor's position
        Updates the grid widget before and after the contextis entered.
        Wrapping any coordinate updates in this context wil ensure the actor
        is drawn correctly.
        """
        self._update_self_on_grid()
        yield
        self._update_self_on_grid()

    def _update_self_on_grid(self):
        try:
            if not self.grid.game_over: #  no more updated when game over
                self.grid.update_actor(self)
        except RuntimeError:
            pass  # Grid has been already deleted by Qt (task wasn't canceled in time)

    async def step(self, dr, dc, duration=1.0):
        """Coroutine for a step in a given direction
        Smoothly moves ``dr`` tiles in the row-direction and ``dc`` tiles in
        the column-direction in ``duration`` seconds.
        """
        start_row = self.row
        start_col = self.column

        for p in self._progress(duration):
            with self._update_context():
                self.row = start_row + dr * p
                self.column = start_col + dc * p

            # Sleep amount is based on zoom level: we want to sleep for
            # about one pixel's worth of movement.
            await asyncio.sleep(duration/self.grid.cell_size)

        # Final update to the exact ending position (this should use integer
        # arithmetic, so it avoids rounding errors)
        with self._update_context():
            self.row = start_row + dr
            self.column = start_col + dc

    async def jump(self, duration=0.2):
        """Coroutine for a small jump
        Smoothly moves a bit up and down in ``duration`` seconds.
        """
        start_row = self.row

        for p in self._progress(duration):
            with self._update_context():
                # jump along a parabola
                self.row = start_row - p * (1-p)

            await asyncio.sleep(duration/self.grid.cell_size * 2)

        with self._update_context():
            self.row = start_row


class ActorWithSpeed(Actor):
    def __init__(self, grid, row, column, kind):
        super().__init__(grid, row, column, kind)
        self.default_speed = 1 # seconds per cell
        self.speed_factor = 1

    def speed_for_step(self):
        return self.speed_factor * self.default_speed

    async def behavior(self):
        while not self.grid.game_over:
            row = int(self.row)
            column = int(self.column)
            if self.grid.inside_array(row, column):
                direction = self.grid.analysis.directions[row, column]
            else:
                direction = b'?'

            self.in_goal = direction == b'X'

            if direction == b'v':
                await self.step(1, 0, self.speed_for_step())
            elif direction == b'>':
                await self.step(0, 1, self.speed_for_step())
            elif direction == b'^':
                await self.step(-1, 0, self.speed_for_step())
            elif direction == b'<':
                await self.step(0, -1, self.speed_for_step())
            else:
                await self.jump()


# Speedy (75% faster actor)
class SpeedyActor(ActorWithSpeed):
    def __init__(self, grid, row, column, kind):
        super().__init__(grid, row, column, kind)
        self.speed_factor = 0.25


# Accelerator (can accelerate, up to 80% faster)
class AcceleratorActor(ActorWithSpeed):
    MIN_SPEED_FACTOR = 0.2
    ACCELERATE_PROB = 0.1
    ACCELERATE_STEP = 0.2

    def speed_for_step(self):
        if self.MIN_SPEED_FACTOR < self.speed_factor and \
           random.random() < self.ACCELERATE_PROB:
            self.speed_factor -= self.ACCELERATE_STEP
        return self.speed_factor * self.default_speed


# Jumper (jumping over wall)
class JumperActor(Actor):
    JUMP_PROB = 1.0
    STEPS_TO_JUMP = 0
    MIN_DIST_GOAL = 5
    JUMP_DURATION = 1
    D2 = [(-2, 0), (2, 0), (0, 2), (0, -2)]
    D1 = [(-1, 0), (1, 0), (0, 1), (0, -1)]

    def __init__(self, grid, row, column, kind):
        super().__init__(grid, row, column, kind)
        self.steps_without_jump = 0

    async def behavior(self):
        while not self.grid.game_over:
            self.steps_without_jump += 1
            row = int(self.row)
            column = int(self.column)
            if self.grid.inside_array(row, column):
                direction = self.grid.analysis.directions[row, column]
            else:
                direction = b'?'

            self.in_goal = direction == b'X'

            jump_diff = self.pick_jump_target()
            if self.can_jump_over(*jump_diff):
                await self.jump_over(*jump_diff, self.JUMP_DURATION)
            elif direction == b'v':
                await self.step(1, 0)
            elif direction == b'>':
                await self.step(0, 1)
            elif direction == b'^':
                await self.step(-1, 0)
            elif direction == b'<':
                await self.step(0, -1)
            else:
                await self.jump()

    def pick_jump_target(self):
        row = int(self.row)
        col = int(self.column)

        for i in range(4):
            if self.grid.inside_array(row+self.D2[i][0], col+self.D2[i][1]):
                target_dist = self.grid.analysis.distances[row+self.D2[i][0], col+self.D2[i][1]]
                between_dist = self.grid.analysis.distances[row+self.D1[i][0], col+self.D1[i][1]]
                act_dist = self.grid.analysis.distances[row, col]
                if act_dist > target_dist > self.MIN_DIST_GOAL and between_dist < 0:
                    return self.D2[i]
        return 0, 0

    def can_jump_over(self, x, y):
        return self.steps_without_jump > self.STEPS_TO_JUMP and \
               ((x + y == -2) or (x + y == 2)) and \
               random.random() < self.JUMP_PROB

    async def jump_over(self, dr, dc, duration):
        self.steps_without_jump = 0
        start_row = self.row
        start_col = self.column

        if dc == 0:
            for p in self._progress(duration):
                with self._update_context():
                    self.row = start_row + dr * p
                    self.column = start_col - p * (1 - p)

                await asyncio.sleep(duration / self.grid.cell_size)
        else:
            for p in self._progress(duration):
                with self._update_context():
                    self.row = start_row - p * (1 - p)
                    self.column = start_col + dc * p

                await asyncio.sleep(duration / self.grid.cell_size)

        # Final update to the exact ending position (this should use integer
        # arithmetic, so it avoids rounding errors)
        with self._update_context():
            self.row = start_row + dr
            self.column = start_col + dc


# Teleporter (tp to random place)
class TeleporterActor(Actor):
    TELEPORT_PROB = 0.2
    MIN_DIST_GOAL = 5
    MIN_DIST_ACTOR = 5
    SHIVER_DURATION = 0.5

    async def behavior(self):
        while not self.grid.game_over:
            row = int(self.row)
            column = int(self.column)
            if self.grid.inside_array(row, column):
                direction = self.grid.analysis.directions[row, column]
            else:
                direction = b'?'

            self.in_goal = direction == b'X'

            if self.can_teleport():
                await self.teleport(*self.pick_teleport_target())
            elif direction == b'v':
                await self.step(1, 0)
            elif direction == b'>':
                await self.step(0, 1)
            elif direction == b'^':
                await self.step(-1, 0)
            elif direction == b'<':
                await self.step(0, -1)
            else:
                await self.jump()

    def can_teleport(self):
        return not self.in_goal and random.random() < self.TELEPORT_PROB

    async def teleport(self, row, col):
        await self.shiver(self.SHIVER_DURATION)

        with self._update_context():
            self.row = row
            self.column = col

        await self.shiver(self.SHIVER_DURATION)

    async def shiver(self, duration):
        start_row = self.row
        start_column = self.column

        for p in self._progress(duration):
            with self._update_context():
                self.column = start_column - p * (random.random()-0.5) * 0.25
                self.row = start_row - p * (random.random()-0.5) * 0.25

            await asyncio.sleep(2*duration / self.grid.cell_size)

        with self._update_context():
            self.row = start_row
            self.column = start_column

    def pick_teleport_target(self):
        shape = self.grid.analysis.directions.shape
        row = int(self.row)
        col = int(self.column)
        while not self.good_teleport_target(row, col):
            row = random.randrange(0, shape[0])
            col = random.randrange(0, shape[1])
        return row, col

    def good_teleport_target(self, row, col):
        return self.grid.analysis.distances[row, col] > self.MIN_DIST_GOAL and \
               ((int(self.row) - row)**2 + (int(self.column) - col)**2) > self.MIN_DIST_GOAL**2


# Scatterbrain (can messup direction)
class ScatterbrainActor(Actor):
    MESS_UP_PROB = 0.25
    DIRS_VECTORS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    DIRS_CHARS = [b'v', b'>', b'^', b'<']
    ANTI_DIRS_CHARS = [b'^', b'<', b'v', b'>']

    def mess_up(self, row, col, direction):
        if direction not in self.DIRS_CHARS:
            return direction
        possible_dirs = []
        shape = self.grid.analysis.directions.shape
        for i in range(4):
            di = self.DIRS_CHARS.index(direction)
            if i == di or self.DIRS_CHARS[i] == self.ANTI_DIRS_CHARS[di]:
                continue
            nrow = row + self.DIRS_VECTORS[i][0]
            ncol = col + self.DIRS_VECTORS[i][1]
            if 0 <= nrow < shape[0] and 0 <= ncol < shape[1] and \
               self.grid.analysis.distances[nrow, ncol] > 0:
                possible_dirs.append(self.DIRS_CHARS[i])
        if len(possible_dirs) == 0:
            return self.ANTI_DIRS_CHARS[self.DIRS_CHARS.index(direction)]
        else:
            return random.choice(possible_dirs)

    async def behavior(self):
        while not self.grid.game_over:
            row = int(self.row)
            column = int(self.column)
            if self.grid.inside_array(row, column):
                direction = self.grid.analysis.directions[row, column]
            else:
                direction = b'?'

            self.in_goal = direction == b'X'

            if random.random() < self.MESS_UP_PROB:
                direction = self.mess_up(row, column, direction)

            if direction == b'v':
                await self.step(1, 0)
            elif direction == b'>':
                await self.step(0, 1)
            elif direction == b'^':
                await self.step(-1, 0)
            elif direction == b'<':
                await self.step(0, -1)
            else:
                await self.jump()


actor_types = {
    'basic': Actor,
    'speedy': SpeedyActor,
    'accelerator': AcceleratorActor,
    'jumper': JumperActor,
    'teleporter': TeleporterActor,
    'scatterbrain': ScatterbrainActor,
}
