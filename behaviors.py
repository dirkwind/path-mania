from __future__ import annotations

import abc
import random
from typing import TYPE_CHECKING

from enums import AbilityState, Direction

if TYPE_CHECKING:
    from game_objects.pawns import Pawn


class Behavior(abc.ABC):
    """Behavior defines how an enemy AI works."""

    behaviors: dict[str, type[Behavior]] = {}
    """A dictionary mapping Behavior subclass names to the classes themselves."""

    def __init_subclass__(cls, *args, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        cls.behaviors[cls.__name__] = cls

    def __init__(self):
        self._owner: Pawn | None = None

    @abc.abstractmethod
    def enact(self):
        """Performs the `Behavior`'s action."""
        raise NotImplementedError

    def register_owner(self, owner: Pawn) -> None:
        """Sets the `Pawn` the `Behavior` affects when it's `enact`ed."""
        self._owner = owner


class RandomBehavior(Behavior):
    """Moves randomly (only when a move is possible)."""

    def enact(self):
        if not self._owner.game.is_evade_mode:
            return

        possible_directions: list[Direction] = [
            direction
            for direction in Direction
            if self._owner.game.arena.path_exists(self._owner.pos, direction)
        ]

        self._owner.threaded_move(
            random.choice(possible_directions),
            change_heading=not self._owner.headingless,
            turn_speed=self._owner.turn_speed,
        )
        if self._owner.intersects(self._target):
            self._owner.game.gameover()


class AbilityBehavior(Behavior):
    """Abstract Behavior that defines an interface for time-based abilities.

    Subclasses define how the ability works.
    """

    def __init__(
        self,
        charge_time: int = 100,
        initial_state: str | int | AbilityState = AbilityState.READY,
    ):
        """Initialized an AbilityBehavior.

        Args:
            charge_time (int, optional): The time (in ms) it takes for the ability to charge. \
                Defaults to 100.
            initial_state (str | int | AbilityState, optional): The ability's initial status. CHARGING \
                is an invalid initial_state. Defaults to AbilityState.READY.
        """
        super().__init__()

        self.charge_time = charge_time
        self._charge_state: AbilityState

        if isinstance(initial_state, AbilityState):
            self._charge_state = initial_state
        elif isinstance(initial_state, str):
            self._charge_state = AbilityState[initial_state]
        else:
            self._charge_state = AbilityState(initial_state)

        if initial_state is AbilityState.CHARGING:
            raise ValueError(
                "Cannot initialize AbilityBehaviour with the CHARGING state!"
            )

    def use_ability(self):
        self._charge_state = AbilityState.USED

    def charge_ability(self):
        if self._owner is None:
            raise ValueError("Cannot charge ability before owner is registered!")

        self._charge_state = AbilityState.CHARGING
        self._owner.game.screen.ontimer(self.ready_ability, self.charge_time)

    def ready_ability(self):
        self._charge_state = AbilityState.READY

    @property
    def ability_is_ready(self):
        return self._charge_state is AbilityState.READY

    @property
    def ability_is_charging(self):
        return self._charge_state is AbilityState.CHARGING

    @property
    def ability_is_used(self):
        return self._charge_state is AbilityState.USED


class ColoredAbilityBehavior(AbilityBehavior):
    """Extension of `AbilityBehavior` that changes the owner's color based on
    the charge state of the ability.
    """

    def __init__(
        self,
        ready_color: str,
        used_color: str,
        charging_color: str | None = None,
        charge_time: int = 1000,
        initial_state: str | int | AbilityState = AbilityState.READY,
    ):
        """Initialized a ColoredAbilityBehavior.
        
        Differs from the standard AbilityBehavior by changing the owner's color \
            depending on the charge state.

        Args:
            ready_color (str): The owner turtle's color when the ability is ready.
            used_color (str): The owner turtle's color when the ability has been used.
            charging_color (str | None, optional): The owner turtle's color when \
                the ability is charging. If None, charging_color = used_color. Defaults to None.
            charge_time (int, optional): The time (in ms) it takes for the ability to charge. \
                Defaults to 100.
            initial_state (str | int | AbilityState, optional): The ability's initial status. CHARGING \
                is an invalid initial_state. Defaults to AbilityState.READY.
        """
        super().__init__(charge_time, initial_state)
        self._ready_color: str = ready_color
        self._used_color: str = used_color
        self._charging_color: str = charging_color or used_color

    def use_ability(self):
        super().use_ability()
        self._owner._turtle.color(self._used_color)

    def charge_ability(self):
        super().charge_ability()
        self._owner._turtle.color(self._charging_color)

    def ready_ability(self):
        super().ready_ability()
        self._owner._turtle.color(self._ready_color)


class ChaseBehavior(Behavior):
    """Behavior that makes the owner chase its provided target, taking the
    shortest route possible.
    """

    def __init__(self, target: Pawn | None = None):
        self._target: Pawn | None = target
        # TODO: when adding logging, perhaps have a warning if target is None?

    def enact(self):
        if not self._owner.game.is_evade_mode or self._target is None:
            return

        best_dir: Direction = self._owner.game.arena.get_movement_options(
            self._owner.pos, self._target.pos
        )[0][0]

        self._owner.threaded_move(
            best_dir,
            change_heading=not self._owner.headingless,
            turn_speed=self._owner.turn_speed,
        )
        if self._owner.intersects(self._target):
            self._owner.game.gameover()

    @property
    def target(self) -> Pawn:
        return self._target

    @target.setter
    def target(self, new: Pawn | None):
        self._target = new


class ChargeBehavior(ChaseBehavior):
    """Similar to `ChaseBehavior` but instead has the owner "charge" down path
    corridors as far as it can.
    """

    def enact(self):
        if not self._owner.game.is_evade_mode or self._target is None:
            return

        best_dir: Direction = self._owner.game.arena.get_movement_options(
            self._owner.pos, self._target.pos
        )[0][0]

        self._owner.threaded_move(
            best_dir,
            change_heading=not self._owner.headingless,
            turn_speed=self._owner.turn_speed,
            greedy=True,
        )
        if self._owner.intersects(self._target):
            self._owner.game.gameover()


class JumperBehavior(ChaseBehavior, ColoredAbilityBehavior):
    """Behavior that allows its owner to ignore paths ("jump gaps")
    every so often.
    """

    def __init__(
        self,
        target: Pawn | None = None,
        cooldown: int = 2000,
        ready_color: str = "green",
        used_color: str = "red",
    ):
        ChaseBehavior.__init__(self, target)
        ColoredAbilityBehavior.__init__(
            self, ready_color, used_color, charge_time=cooldown
        )

    def enact(self):
        if not self._owner.game.is_evade_mode or self._target is None:
            return

        # ability on cooldown
        if not self.ability_is_ready:
            return super().enact()

        best_dir: Direction = self._owner.game.arena.get_movement_options(
            self._owner.pos, self._target.pos, ignore_paths=True
        )[0][0]

        if self._owner.game.arena.path_exists(self._owner.pos, best_dir):
            return super().enact()

        # okay, now we jump, since that's the best move

        self.use_ability()
        self._owner.threaded_move(
            best_dir,
            change_heading=not self._owner.headingless,
            turn_speed=self._owner.turn_speed,
            validate_path=False,
        )
        if self._owner.intersects(self._target):
            self._owner.game.gameover()

        self.charge_ability()
