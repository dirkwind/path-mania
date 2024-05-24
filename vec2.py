from __future__ import annotations

import math
from typing import Callable


class Vec2(tuple):
    """Immutable 2-dimentional vector."""

    def __new__(cls, x: int | float, y: int | float):
        return tuple.__new__(cls, (x, y))

    # dispite having these properties, internal functions use indexes to
    # reduce the number of function calls
    @property
    def x(self):
        return self[0]

    @property
    def y(self):
        return self[1]

    def map_(self, func: Callable[[int | float], int | float]) -> Vec2:
        return Vec2(func(self[0]), func(self[1]))

    def magnitude(self) -> float:
        return math.sqrt((self[0] ** 2) + (self[1] ** 2))

    def unit(self) -> Vec2:
        mag = self.magnitude()
        return Vec2(self[0] / mag, self[1] / mag)

    def scale(self, x: int | float, y: int | float | None = None) -> Vec2:
        """Scale the vector.

        Args:
            x (int | float): The value to scale x by. If y is None, then this value also scales y.
            y (int | float | None, optional): The value to scale y by. Defaults to None.

        Returns:
            Vec2: The scaled vector.
        """
        return Vec2(self[0] * x, self[1] * (y or x))

    def distance(self, other: Vec2) -> float:
        return (self - other).magnitude()

    def grid(self, x_size: int, y_size: int | None = None) -> Vec2:
        """Creates the closest Vec2 that fits on a grid of with tiles of size x_size * y_size.

        Can be thought of "snapping" this Vec2 to the closest point on a grid \
            where each tile is sized x_size by y_size. Inherently, this is most \
            useful for vectors that represent position.
        
        Args:
            x_size (int): The x-dimension (width) of the grid tile.
            y_size (int, optional): The y-dimension (height) of the grid tile. If None, then \
                y_size = x_size. Defaults to None.

        Returns:
            Vec2: The point on a grid with tile size x_size * y_size of closest to this Vec2.
        
        Examples:
        >>> Vec2(13, 25).grid(10, 10)
        ... (10, 30)
        """
        if y_size is None:
            y_size = x_size

        # didn't use .x and .y to reduce number of calls
        return Vec2(round(self[0] / x_size) * x_size, round(self[1] / y_size) * y_size)

    def __add__(self, other: Vec2) -> Vec2:
        if not isinstance(other, Vec2):
            raise TypeError(f"Cannot add Vec2 and {type(other)}")

        # didn't use .x and .y to reduce number of calls
        return Vec2(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other: Vec2) -> Vec2:
        if not isinstance(other, Vec2):
            raise TypeError(f"Cannot add Vec2 and {type(other)}")

        # didn't use .x and .y to reduce number of calls
        return Vec2(self[0] - other[0], self[1] - other[1])

    def __abs__(self):
        return Vec2(abs(self[0]), abs(self[1]))


Path = frozenset[Vec2]
