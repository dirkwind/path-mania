from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import behaviors
import level_actions

if TYPE_CHECKING:
    from os import PathLike

_default_action_manager = (
    level_actions.LevelActionManager()
    .add_action(
        1,
        level_actions.add_enemy(
            behaviors.ChaseBehavior(),
            True,
            size=1,
            speed=0,
            turn_speed=0,
            headingless=True,
        ),
    )
    .add_action(
        3,
        level_actions.add_enemy(
            behaviors.ChargeBehavior(),
            True,
            size=1,
            color="blue",
            shape="triangle",
            speed=10,
            turn_speed=1.5,
        ),
    )
)


@dataclass
class Config:
    tps: int | float = 200

    # score = (elapsed_time * (score_per_sec + ((level - 1) * level_score_modifier)))
    score_update_interval: int | float = 0.2  # unit: seconds
    score_per_sec: int | float = 50
    # with each increase in level, increase the score_per_sec by this amount
    level_score_modifier: int | float = 1

    # levelup_bonus = levelup_score_bonus + ((level - 1) * levelup_score_modifier)))
    levelup_score_bonus: int | float = 200  # score player gets on levelup
    # with each increase in level, increase the levelup_score_bonus by this amount
    levelup_score_modifier: int | float = 150

    # all in seconds
    level_duration: int | float = 30
    # each successive level lasts level_duration_modifier seconds longer than the previous
    level_duration_modifier: int | float = 5  # can be negative
    level_duration_min: int | float = 20
    level_duration_max: int | float = 120

    # note: paths will never exceed the number of possible paths to place
    paths: int = 25
    level_path_modifier: int = -3
    paths_max: int = 50
    paths_min: int = 1

    levels: level_actions.LevelActionManager = _default_action_manager

    @property
    def tick_interval_ms(self) -> int:
        return 1000 // self.tps

    @property
    def tick_interval_s(self) -> float:
        return 1 / self.tps

    def calculate_score_per_second(self, level: int = 1) -> int | float:
        return self.score_per_sec + ((level - 1) * self.level_score_modifier)

    def calculate_level_duration(self, level: int = 1) -> int | float:
        """Calculates the duration of the level provided.

        Args:
            level (int, optional): The current level. Defaults to 1.

        Returns:
            int | float: The level duration for the level provided.
        """
        duration = self.level_duration + ((level - 1) * self.level_duration_modifier)

        if duration < self.level_duration_min:
            return self.level_duration_min
        elif duration > self.level_duration_max:
            return self.level_duration_max

        return duration

    def calculate_level_paths(self, level: int = 1) -> int:
        """Calculates the number of paths a player gets for the provided level.

        Args:
            level (int, optional): The current level. Defaults to 1.

        Returns:
            int: The number of paths the player gets for the provided `level`.
        """
        paths = int(self.paths + ((level - 1) * self.level_path_modifier))

        if paths < self.paths_min:
            return self.paths_min
        elif paths > self.paths_max:
            return self.paths_max

        return paths

    def calculate_levelup_score_bonus(self, level: int) -> float | int:
        return self.levelup_score_bonus + ((level - 1) * self.levelup_score_modifier)

    @classmethod
    def from_json(cls, path: str | Path | PathLike):
        with open(path, "r") as file:
            data = json.load(file)

        return cls(**data)


DEFAULT_CONFIG = Config()
