import turtle

from enums import Direction
from vec2 import Path, Vec2


class Arena:
    """Manages everything to do with the arena (paths and coordinates)."""

    def __init__(self, arena_size: int = 20, path_len: int = 25):
        self._arena_size: int = arena_size
        self._path_len: int = path_len
        self._paths: set[Path] = set()
        self._coords: set[Vec2] = set((Vec2(0, 0),))
        self._path_distance_map: dict[Vec2, dict[Vec2, int]] = dict()
        self._coord_distance_map: dict[Vec2, dict[Vec2, int]] = dict()

        self._turtle: turtle.Turtle = turtle.Turtle(visible=False)
        self._turtle.speed(0)

    def draw_border(self, color: str = "red"):
        corner: int = (self._arena_size * self._path_len) // 2
        self._turtle.pencolor(color)
        self._turtle.penup()
        self._turtle.goto(corner, corner)
        self._turtle.pendown()
        self._turtle.goto(corner, -corner)
        self._turtle.goto(-corner, -corner)
        self._turtle.goto(-corner, corner)
        self._turtle.goto(corner, corner)
        self._turtle.penup()

    def get_destination(self, pos: Vec2, direction: Direction) -> Vec2:
        """Gets the coordinate resulting from moving in the provided direction \
            starting from the provided position moving 1 path_len.

        Args:
            pos (Vec2): The position to start from.
            direction (Direction): The direction to move in.

        Returns:
            Vec2: The coordinate 1 path_len in the provided direction from pos.
        """
        match direction:
            case Direction.NORTH:
                return Vec2(pos.x, pos.y + self._path_len)
            case Direction.SOUTH:
                return Vec2(pos.x, pos.y - self._path_len)
            case Direction.WEST:
                return Vec2(pos.x - self._path_len, pos.y)
            case Direction.EAST:
                return Vec2(pos.x + self._path_len, pos.y)

    def get_destination_greedy(
        self,
        pos: Vec2,
        direction: Direction,
        *,
        max_steps: int = -1,
        path_bound: bool = True,
        coord_bound: bool = False,
    ) -> tuple[Vec2, int]:
        """Like get_destination, but gets the final coord in an unobstructed path \
            starting from pos in the provided direction.
            
        Args:
            pos (Vec2): The position to start from.
            direction (Direction): The direction to move in.

        Returns:
            tuple[Vec2, int]: A pair containing the destination position and the \
                number of path_len-sized steps it took to reach destination, respectively.
        """
        transform: Vec2

        match direction:
            case Direction.NORTH:
                transform = Vec2(0, self._path_len)
            case Direction.SOUTH:
                transform = Vec2(0, -self._path_len)
            case Direction.WEST:
                transform = Vec2(-self._path_len, 0)
            case Direction.EAST:
                transform = Vec2(self._path_len, 0)

        steps: int = 1
        prev_dest: Vec2 = pos
        curr_dest: Vec2 = prev_dest + transform
        while (
            (path_bound and self.path_exists_d(prev_dest, curr_dest))
            or (coord_bound and self.coord_exists_d(curr_dest))
            and self.in_bounds(curr_dest)
            and (max_steps < 0 or steps < max_steps)
        ):
            prev_dest = curr_dest
            curr_dest = curr_dest + transform
            steps += 1

        # trace back one step since it was invalid.
        steps -= 1

        return prev_dest.grid(self._path_len), steps

    def path_exists(self, pos: Vec2, direction: Direction) -> bool:
        return {pos, self.get_destination(pos, direction)} in self._paths

    def path_exists_d(self, pos: Vec2, destination: Vec2) -> bool:
        """
        Alternate to path_exists for when destination has already been calculated.
        """
        return {pos, destination} in self._paths

    def coord_exists(self, pos: Vec2, direction: Direction) -> bool:
        return self.get_destination(pos, direction) in self._coords

    def coord_exists_d(self, destination: Vec2) -> bool:
        return destination in self._coords

    def in_bounds(self, coord: Vec2) -> bool:
        """Checks if coord is in bounds"""

        # I did NOT with ORs instead of a bunch of ANDs because I think
        # the ORs would short-circuit faster
        size = self.border_len // 2
        return not (
            coord.x > size or coord.x < -size or coord.y > size or coord.x < -size
        )

    def clear_distances(self):
        self._path_distance_map.clear()
        self._coord_distance_map.clear()

    def chart_all_distances(self):
        """Charts distances to every valid coordinate."""
        for coord in self._coords:
            self.chart_distances(coord)
            self.chart_distances(coord, ignore_paths=True)

    def chart_distances(self, pos: Vec2, *, ignore_paths: bool = False):
        """Charts the distance to the provided position, caching the results for later use.
        
        This function calculates the distances from pos to every other coordinate on the arena. 

        Args:
            pos (Vec2): The position to chart distances from.
            ignore_paths (bool, optional): Whether to ignore paths when pathfinding. \
                If True, then all adjacent coordinates are considered connected rather \
                than only those connected explicitly by paths. Defaults to False.
        """
        self._chart_distances(
            pos,
            self._coord_distance_map if ignore_paths else self._path_distance_map,
            ignore_paths,
        )

    def _chart_distances(
        self,
        to_pos: Vec2,
        distance_map: dict[Vec2, dict[Vec2, int]],
        ignore_paths: bool,
    ):
        """Internal version of chart_distances that takes in the dictionary to save results to.

        Args:
            to_pos (Vec2): The position to chart distances to.
            ignore_paths (bool, optional): Whether to ignore paths when pathfinding. \
                If True, then all adjacent coordinates are considered connected rather \
                than only those connected explicitly by paths. Defaults to False.
            distance_arena (dict[Vec2, dict[Vec2, int]]): The distance arena to use; \
                a dictionary arenaping end destination with another dictionary relating \
                coordinates to their distance away from the end destination.
        """
        if to_pos not in distance_map:
            distance_map[to_pos] = dict()
        else:
            distance_map[to_pos].clear()

        distance_map[to_pos][to_pos] = 0
        queue: list[Vec2] = []
        self._pathfind(to_pos, queue, distance_map[to_pos], ignore_paths)

    def _pathfind(
        self,
        pos: Vec2,
        queue: list[Vec2],
        distances: dict[Vec2, int],
        ignore_paths: bool = False,
    ):
        """Recursive pathfinding algorithm.
        
        This algorithm works as follows:
        1. start with the position we want to pathfind to
            the distance to this position should be marked 0 already.
        2. find every valid move from pos, getting the destination coordinates
            ignore coordinates we've already visited
        3. add each destination to queue
        4. set the distance for each destination to the distance to the current position + 1
        5. if there are items in the queue, pop it, and run _pathfind again 

        Args:
            pos (Vec2): The position to pathfind from. If this is the start position, \
                ensure distances[pos] = 0.
            queue (list[Vec2]): The pathfinding queue.
            distances (dict[Vec2, int]): The distance arena (pos: distance) to modify.
            ignore_paths (bool, optional): Whether to ignore paths when considering if a move \
                is possible. A move is always invalid if it doesn't go to an existing coordinate. \
                Defaults to False.
        """

        for direction in Direction:

            dest: Vec2 = self.get_destination(pos, direction)
            if dest not in distances and (
                (ignore_paths and self.coord_exists_d(dest))
                or self.path_exists_d(pos, dest)
            ):
                queue.append(dest)
                distances[dest] = distances[pos] + 1

        if len(queue) != 0:
            self._pathfind(queue.pop(0), queue, distances, ignore_paths)

    def get_charted_distance(
        self, start: Vec2, goal: Vec2, *, ignore_paths: bool = False
    ) -> int:
        """Gets the distance between start and goal (in terms of arena traversal).

        This function attemps to use cached distances; if none are available, then \
            arena.chart_distances is used.

        Args:
            start (Vec2): The starting position of the distance calculation.
            goal (Vec2): The ending position of the distance calculation.
            ignore_paths (bool, optional): Whether to follow or ignore paths. \
                If paths are ignored, then all adjacent coordinates are considered connected \
                as if a path bridged them. Defaults to False.

        Returns:
            int: The number of single moves between start and goal.
        """
        goal = goal.grid(self._path_len)
        distance_arena = (
            self._coord_distance_map if ignore_paths else self._path_distance_map
        )
        if goal not in distance_arena:
            self.chart_distances(goal, ignore_paths=ignore_paths)

        return distance_arena[goal][start]

    def get_movement_options(
        self, start: Vec2, target: Vec2, *, ignore_paths: bool = False
    ) -> list[tuple[Direction, int]]:
        """Gets all movement options ordered from closest to goal to furthest.
        
        This function relies on cached distance maps that are obtain from using \
            chart_distances. chart_distances is used automatically if distances \
            are not mapped for the target position.

        Args:
            start (Vec2): The start position or position to move from.
            target (Vec2): The target position; does not have to be adjacent \
                to start since the distance_maps are used.
            ignore_paths (bool, optional): Whether to ignore paths when determining \
                possible moves. Defaults to False.

        Returns:
            Direction: List of possible moves, formated as (direction, distance_to_target), \
                ordered from lowest to highest distance_to_target. (i.e., the "best" move \
                is result[0].)
        """
        start = start.grid(self._path_len)
        target = target.grid(self._path_len)
        if target not in self._path_distance_map:
            self.chart_distances(target, ignore_paths=ignore_paths)

        goal_map: dict[Vec2, int] = self._path_distance_map[target]

        options: list[tuple[Direction, int]] = []
        for direction in Direction:
            dest = self.get_destination(start, direction)
            if self.path_exists_d(start, dest) or (
                ignore_paths and self.coord_exists_d(dest)
            ):
                options.append((direction, goal_map[dest]))

        # key just gets the distance part of the option
        return sorted(options, key=lambda op: op[1])

    @property
    def path_capacity(self) -> int:
        return 2 * self.arena_size * (self.arena_size + 1)

    @property
    def num_available_paths(self) -> int:
        return self.path_capacity - len(self.paths)

    @property
    def border_len(self) -> int:
        return self._arena_size * self._path_len

    @property
    def path_len(self) -> int:
        return self._path_len

    @path_len.setter
    def path_len(self, new: int):
        if new <= 0:
            return ValueError("path_len must be positive")
        self._path_len = new

    @property
    def arena_size(self) -> int:
        return self._arena_size

    @arena_size.setter
    def arena_size(self, new: int):
        if new <= 0:
            return ValueError("arena_size must be positive")
        self._arena_size = new

    @property
    def paths(self) -> set[Path]:
        return self._paths

    @property
    def coords(self) -> set[Vec2]:
        return self._coords
