import asyncio
import contextlib
import time
import random

random.seed(time.monotonic())
# TODO: move description of actors to README


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
        self.task = asyncio.ensure_future(self.behavior())
        self.in_goal = False

    async def behavior(self):
        """Coroutine containing the actor's behavior
        The base implementation follows directions the actor is standing on.
        If there is no directions (e.g. standing on a wall, unreachable space,
        or on the goal), the actor jumps repeatedly.
        To be reimplemented in subclasses..
        """
        while True:
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
        start = time.monotonic()
        while True:
            now = time.monotonic()
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
        while True:
            shape = self.grid.analysis.directions.shape
            row = int(self.row)
            column = int(self.column)
            if 0 <= row < shape[0] and 0 <= column < shape[1]:
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


# Rychlík
# Rychlík má stabilně o 75 % vyšší rychlost než základní aktor.
#
# Speedy
# Speedy is constantly 75% faster than basic actor.
class SpeedyActor(ActorWithSpeed):
    def __init__(self, grid, row, column, kind):
        super().__init__(grid, row, column, kind)
        self.speed_factor = 0.25


# Zrychlovač
# Zrychlovač může po každém kroku s určitou pravděpodobností trvale
# zvýšit svou rychlost. Čím déle chodí, tím rychlejší může být. Pravděpodobnost
# nastavte tak, aby hra byla hratelná; zrychlení tak, aby bylo znatelné (např. o
# čtvrt políčka za sekundu). Doporučujeme nastavit i rychlostní strop, případně
# zrychlovat stále o menší a menší hodnotu.
#
# Accelerator
# Accelerator can speed-up (with probability p) to increase his speed. Maximal
# speed is four times faster than basic actor.
class AcceleratorActor(ActorWithSpeed):
    MIN_SPEED_FACTOR = 0.2
    ACCELERATE_PROB = 0.25
    ACCELERATE_STEP = 0.1

    def speed_for_step(self):
        if self.MIN_SPEED_FACTOR < self.speed_factor and \
           random.random() < self.ACCELERATE_PROB:
            self.speed_factor -= self.ACCELERATE_STEP
        return self.speed_factor * self.default_speed


# Skokan*
# Pokud je za jedním políčkem zdi průchozí políčko, odkud je cesta do cíle alespoň
# o 5 políček kratší, než z místa, kde se Skokan nachází, Skokan touto zdí projde
# (přeskočí ji). Kvůli hratelnosti doporučujeme nastavit limity na to, jak často se
# toto může dít, případně zakázat projít zdí přímo na cíl apod.
#
# Jumper
# Jumper will jump over the wall if cell behind is accessible and closer to some
# goal at least by 5 steps and more than 5 steps from goal. Jumper must walk at
# least 10 steps before jumping.
class JumperActor(Actor):
    pass  # TODO: implement


# Teleportér*
# Teleportér se místo kroku může s určitou pravděpodobností teleportovat na náhodné
# průchozí a dostupné místo bludiště. Při teleportu se postavička na malou chvíli rozechvěje,
# pak se přemístí a po chvilce se přestane chvět. Celá akce by měla trvat méně než sekundu.
# Doporučujeme zakázat teleport na políčka příliš blízko cíli.
#
# Teleporter*
# Teleporter can (with probability p) teleport to random accessible place in grid.
# During the teleportation process the actor shivers a lot. Destination must be more than
# 5 steps from goal.
class TeleporterActor(Actor):
    pass  # TODO: implement


# Zmatkář
# Zmatkář s určitou pravděpodobností místo kroku směrem k cíli provede krok náhodným průchozím
# směrem (pokud to je možné, tak jiným, než ze kterého přišel).
#
# Scatterbrain
# Scatterbrain can (with probability p) lost his mind and go to random direction (if possible,
# no turning back).
class ScatterbrainActor(Actor):
    MESS_UP_PROB = 0.25
    DIRS_VECTORS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
    DIRS_CHARS = [b'v', b'>', b'^', b'<']
    ANTI_DIRS_CHARS = [b'^', b'<', b'v', b'>']

    def mess_up(self, row, col, direction):
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
        while True:
            shape = self.grid.analysis.directions.shape
            row = int(self.row)
            column = int(self.column)
            if 0 <= row < shape[0] and 0 <= column < shape[1]:
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
