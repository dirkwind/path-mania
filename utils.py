from __future__ import annotations

import time
from typing import Generator

import config
from vec2 import Vec2


def interpolate_vec2(
    pos: Vec2,
    dest: Vec2,
    speed: int | float,
    cfg: config.Config | None = None,
) -> Generator[Vec2, None, None]:
    """Iterpolates positions from `pos` to `dest` until `dest` is reached.`

    Args:
        pos: The start position.
        dest: The destination position.
        speed: The speed at which to move from `pos` to `dest`.
        cfg: The game configuration settings to follow. If `None`, the default
            configuration is used. Defaults to None.

    Yields:
        Positions as `Vec2`s from `pos` to `dest`. `dest` will always be the
            final value.
    """
    if speed <= 0:
        yield dest
        return

    diff = dest - pos
    speed_vec = diff.unit().scale(speed)
    offset = speed_vec
    distance = diff.magnitude()
    while offset.magnitude() < distance:
        yield pos + offset
        offset += speed_vec
        time.sleep((cfg or config.DEFAULT_CONFIG).tick_interval_s)

    yield dest


def interpolate_deg(
    start: int | float,
    end: int | float,
    speed: int | float,
    cfg: config.Config | None = None,
) -> Generator[int | float, None, None]:
    """Generator yielding degrees from start to end at the provided speed.

    Will take the shortest path from start to end (either clockwise or counterclockwise).

    Args:
        start: The starting degrees. Should be in [0, 360)
        end: The target degrees. Should be in [0, 360)
        speed: The speed of the interpolation.
        cfg: the config to get tick interval. If `None`, the default config is used.
            Defaults to None.

    Yields:
        The current degree step. Always yields the value of `end` upon final iteration.
    """
    if start == end or speed <= 0:
        yield end
        return

    start = start % 360
    end = end % 360

    ccw_dist: int | float = (end - start) % 360  # counterclockwise distance
    cw_dist: int | float = 360 - ccw_dist  # clockwise distance

    # positive is counterclockwise, negative is clockwise
    sign = 1 if (ccw_dist < cw_dist) else -1
    dist = min(ccw_dist, cw_dist)

    distance_traveled: int | float = speed
    while distance_traveled < dist:
        distance_traveled += speed
        yield start + (sign * distance_traveled)
        time.sleep((cfg or config.DEFAULT_CONFIG).tick_interval_s)

    yield end
