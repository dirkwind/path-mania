from __future__ import annotations

import random
from typing import TYPE_CHECKING, Callable, Literal, Self

from behaviors import Behavior, ChaseBehavior
from game_objects import pawns
from vec2 import Vec2

if TYPE_CHECKING:
    from game_objects import game

    LevelAction = Callable[[game.Game], int | None]


def add_enemy(
    behavior: Behavior,
    target_player: bool = True,
    shape: str = "square",
    size: int = 5,
    color: str = "red",
    pos: Vec2 | Literal["random"] = Vec2(0, 0),
    speed: int = 5,
    turn_speed: int | None = None,
    *,
    visible: bool = True,
    headingless: bool = False,
    hitbox_radius: int | float | None = None,
) -> LevelAction:
    """Returns a `LevelAction` that spawns an enemy with the provided parameters.

    Args:
        behavior: The added enemy's behavior.
        target_player: whether to set the provided behavior's target to the player
            when adding the enemy.
        shape: The shape of the enemy. Defaults to "square".
        size: The size of the enemy. Defaults to 5.
        color: The color of the enemy. Defaults to "red".
        pos: the starting position of the enemy. If `"random"`, a random valid
            position is chosen. Defaults to Vec2(0, 0).
        speed: The movement speed of the enemy. Defaults to 5.
        turn_speed: The rotation speed of the enemy. Defaults to None.
        visible: Whether the enemy is visible or not. Defaults to True.
        headingless: Whether to skip rotating the enemy in the direction of movement
            before moving. Defaults to False.
        hitbox_radius: The radius of the circular hitbox for the enemy.
    """

    def action(game: game.Game):
        nonlocal pos

        if pos == "random":
            pos = random.choice(list(game.arena.coords))

        if isinstance(behavior, ChaseBehavior) and target_player:
            behavior.target = game.players[0]

        game.add_pawn(
            pawns.Enemy(
                game,
                behavior,
                shape,
                size,
                color,
                pos,
                speed,
                turn_speed,
                visible=visible,
                headingless=headingless,
                hitbox_radius=hitbox_radius,
            )
        )

    return action


def _sentinel(*args, **kwargs):
    return


def default(*args, **kwargs) -> LevelAction:
    """Returns the default `LevelAction`: a functions that does nothing."""
    return _sentinel


class LevelActionManager:

    def __init__(self):
        self._actions: dict[int, LevelAction] = {}
        self._default_action: LevelAction = default

    def add_action(self, level: int, action: LevelAction) -> Self:
        self._actions[level] = action
        return self

    def remove_action(self, level: int) -> Self:
        self._actions.pop(level, None)

        return self

    def set_default_action(self, action: LevelAction) -> Self:
        self._default_action = action
        return self

    def get_action(self, level: int) -> LevelAction:
        return self._actions.get(level, self._default_action)
