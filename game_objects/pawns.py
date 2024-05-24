from __future__ import annotations

import threading
import turtle
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING, Any

import keyboard

import utils
from behaviors import Behavior
from enums import Direction
from vec2 import Vec2

from .entity import Entity

if TYPE_CHECKING:
    from .arena import Arena
    from .game import Game


class Pawn(Entity):

    _pawn_count: int = 0

    def __init__(
        self,
        game: Game,
        shape: str = "classic",
        size: int = 5,
        color: str = "black",
        pos: Vec2 = Vec2(0, 0),
        speed: int = 5,
        turn_speed: int | None = None,
        *,
        visible: bool = True,
        name: str | None = None,
        hitbox_radius: float | int | None = None,
    ):
        """Creates a `Pawn` object.

        Args:
            game: The `Game` object this `Pawn` belongs to.
            shape: The shape of the `Pawn`'s turtle. Defaults to "classic".
            size: The display size of the `Pawn`. Defaults to 5.
            color: The color of the `Pawn`. Defaults to "black".
            pos: The starting position of the `Pawn`. Defaults to Vec2(0, 0).
            speed: The movement speed of the `Pawn`. Defaults to 5.
            turn_speed: The rotate/turning speed of the `Pawn`. Defaults to None.
            visible: Wether the `Pawn` is drawn. Defaults to True.
            name: The pawn's name. Defaults to None.
            hitbox_radius: The radius of the `Pawn`'s hitbox. If `None`, this
                value is equivalent to `size`. Defaults to None.
        """
        super().__init__(game)
        self._turtle = turtle.Turtle(shape=shape, visible=visible)
        self._pawn_count += 1

        self._turtle.color(color)
        self._turtle.speed(speed)
        self._turtle.shapesize(size)

        self._name: str | None = name
        self._moving = False
        self._pos: Vec2 = pos
        self.pawn_speed: int = speed
        self.turn_speed: int | None = turn_speed
        self.hitbox_radius: int | float = hitbox_radius or size

        self._move_args: tuple[Any, ...]
        self._move_kwargs: tuple[str, Any]

        self._listener: threading.Thread = threading.Thread(
            name=f"{name or f'Pawn-{self._pawn_count}'} Move Listener",
            target=self._move_listen,
            daemon=True,
        )
        self._move_event: threading.Event = threading.Event()
        self._listener.start()
        self._lock = threading.Lock()

        self._setup()

    def _setup(self):
        """Additional setup function for pawn subclasses that wish to preserve
        the default constructor.
        """
        pass

    @contextmanager
    def temp_speed(self, speed: int | None = None):
        """Context manager that temporarily alters player speed within the
        context.

        Args:
            speed: The speed to temporarily change to. If `None`, the speed is
                unaltered. Defaults to None.
        """
        if speed is not None:
            self._turtle.speed(speed)

        yield

        if speed is not None:
            self._turtle.speed(self.pawn_speed)

    @contextmanager
    def moving(self, draw: bool = True, speed: int | None = None):
        """Context manager that initializes and finalizes player movement;
        should be used whenever the player is actively moving.

        Args:
            draw: Whether to enable line drawing during the move.
                Defaults to True.
            speed: The speed at which the `Pawn` will move within the context.
                If `None`, the `Pawn` will use its currently set speed.
                Defaults to None.

        Yields:
            Nothing; used to specify entry point for the context.
        """
        self._moving = True

        if draw:
            self._turtle.pendown()
        else:
            self._turtle.penup()

        with self.temp_speed(speed):
            yield  # run code within the context manager

        if draw:
            self._turtle.penup()

        self._moving = False

    def set_heading(
        self, heading: int | float, rotation_speed: int | float | None = None
    ):
        """Rotates the `Pawn` at a specified speed (dependent on configured
        game tick speed).

        Args:
            heading: The new heading (in degrees) to rotate the pawn to.
            rotation_speed: The speed at which to rotate the pawn.
                Defaults to None.
        """
        for deg in utils.interpolate_deg(
            self._turtle.heading(),
            heading,
            rotation_speed or self.turn_speed or self.pawn_speed * 2,
            self.game.config,
        ):
            self._turtle.setheading(deg)

    def move(
        self,
        direction: Direction,
        *,
        path: bool = False,
        validate_path: bool = True,
        validate_border: bool = True,
        speed: int | None = None,
        change_heading: bool = True,
        turn_speed: int | None = None,
        greedy: bool = False,
        max_greedy_steps: int = -1,
    ) -> bool | None:
        """Moves the pawn in the specified direction.

        Args:
            direction: The direction to move the pawn.
            path: Whether or not to create a path when moving.
                Defaults to False.
            validate_path: If True, will block the move if the
                pawn would move off path. Defaults to True.
            validate_border: If True, will block the move if
                the pawn would move out of bounds. Defaults to True.
            speed: The speed to move at; will
                temporarily change this pawn's speed to the provided value
                until the move is complete. If None, the pawn's preset speed
                is used. Defaults to None.
            change_heading: Whether to turn the pawn in the
                direction of motion when moving. Defaults to True.
            turn_speed: Assuming `change_heading` is
                True, this determines the speed at which the pawn turns for
                this move. If None, the pawn's normal turn speed will be used.
                Defaults to None.
            greedy: Whether to move at most `max_greedy_steps`
                paths in a straight line instead of one space. Defaults to
                False.
            max_greedy_steps: the maximum number of paths/steps
                the pawn can move if `greedy` is `True`. If less than zero, the
                limit is infinite. Defaults to -1.


        Returns:
            bool | None: Always returns None when path=False.
                Otherwise, returns True if new path was created, False if not.
        """

        if self._moving or self.game.is_frozen:
            return

        with self.moving(path, speed):
            dest: Vec2
            steps: int = 1
            if greedy:
                dest, steps = self.game.arena.get_destination_greedy(
                    self._pos,
                    direction,
                    max_steps=max_greedy_steps,
                )
            else:
                dest = self.game.arena.get_destination(self._pos, direction)

            if (
                steps == 0  # didn't move
                or not greedy
                and (  # movement validations
                    (validate_border and not self.game.arena.in_bounds(dest))
                    or (
                        validate_path
                        and not self.game.arena.path_exists_d(self._pos, dest)
                    )
                )
            ):
                return None

            if change_heading:
                self.set_heading(direction.value, turn_speed)

            prev_pos = self._pos
            for pos in utils.interpolate_vec2(
                self._pos, dest, speed or self.pawn_speed, self.game.config
            ):
                self._pos = pos
                self._turtle.setpos(*pos)

            # ensure we end up precisely at the intended destination
            self._pos = dest

            if path:
                p = frozenset((prev_pos, dest))
                path_created = p not in self.game.arena.paths
                self.game.arena.paths.add(p)
                self.game.arena.coords.add(dest)
                return path_created

    def threaded_move(self, *args, **kwargs):
        """See `Pawn.move` for more info; this calls `move` on a separate thread."""
        if self._moving:
            return

        with self._lock:  # honestly, idk if this does anything...
            self._move_args = args
            self._move_kwargs = kwargs
            self._move_event.set()

    def _move_listen(self):
        """Function for this Pawn's move listener.

        Listens for a threaded move request; executes the move. This should
        be ran on its own thread.
        """

        while True:
            self._move_event.wait()
            self.move(*self._move_args, **self._move_kwargs)
            self._move_event.clear()

    def teleport(self, pos: Vec2):
        """Convinience method for teleporting the `Pawn` instantly to a provided
        position.

        Args:
            pos (Vec2): The position to teleport to.
        """
        with self.moving(False, 0):
            self._pos = pos
            self.goto(*pos)

    def center(self):
        """Teleports this pawn to the center of the map."""
        self.teleport(Vec2(0, 0))

    def intersects(self, other: Pawn) -> bool:
        """Checks if this `Pawn` intersects another `Pawn`.

        Hitboxes for pawns are circles with radii determined by their
        `hitbox_radius` parameter.

        Args:
            other: _description_

        Returns:
            _description_
        """

        # hitboxes for all shapes will be circles, because its easiest:
        # every point on the circumference of a circle is equal distance from
        # the center, so we know two circles are intersecting if the distance
        # between their centers is shorter than the sum of their radii
        min_distance = other.hitbox_radius + self.hitbox_radius
        return self._pos.distance(other._pos) <= min_distance

    @property
    def pos(self) -> Vec2:
        """The pawn's current position.

        To set position, use `move`, `threaded_move`, or `teleport`.
        """
        # this is a property because we don't want people to manually set pos
        return self._pos

    @property
    def is_moving(self) -> bool:
        """Whether the pawn is actively moving or not."""
        return self._moving


class Player(Pawn):

    def _setup(self):
        self._paths = 0
        self._greedy = False

        self._path_turt = turtle.Turtle()
        self._path_turt.hideturtle()
        self._path_turt.speed(0)
        self._path_turt.penup()
        self._path_turt.goto(
            -self.game.arena.border_len // 2, self.game.arena.border_len // 2
        )

    def move(self, direction: Direction):
        if super().move(
            direction,
            path=self.game.is_path_mode,
            validate_path=not self.game.is_path_mode,
            greedy=self.game.is_evade_mode and keyboard.is_pressed("shift"),
        ):
            self.paths -= 1

        if self.game.is_path_mode and self._paths <= 0:
            # threading.Thread(target=self.game.arena.chart_all_distances).start()
            self.game.arena.chart_all_distances()
            self.game.begin_level()

    @property
    def paths(self) -> int:
        return self._paths

    @paths.setter
    def paths(self, new: int):
        if new < 0:
            raise ValueError("Cannot have negative paths")

        self._paths = new

        self._path_turt.clear()
        self._path_turt.write(
            f"Paths: {self._paths}", align="left", font=("Monospace", 15, "normal")
        )

    def toggle_greedy(self):
        """Toggles "greedy" movement for the player, or movement that moves as
        far as possible before stopping (instead of one space).
        """
        self._greedy = not self._greedy


class Enemy(Pawn):
    def __init__(
        self,
        game: Game,
        behavior: Behavior,
        shape: str = "square",
        size: int = 5,
        color: str = "red",
        pos: Vec2 = Vec2(0, 0),
        speed: int = 5,
        turn_speed: int | None = None,
        *,
        visible: bool = True,
        hitbox_radius: int | float | None = None,
        headingless: bool = False,
    ):
        """Creates an `Enemy`.

        Args:
            game: The `Game` object this `Enemy` belongs to.
            behavior: The enemy's behavior, which determines it's AI or how it
                acts.
            shape: The shape of the `Enemy`'s turtle. Defaults to "classic".
            size: The display size of the `Enemy`. Defaults to 5.
            color: The color of the `Enemy`. Defaults to "black".
            pos: The starting position of the `Enemy`. Defaults to Vec2(0, 0).
            speed: The movement speed of the `Enemy`. Defaults to 5.
            turn_speed: The rotate/turning speed of the `Enemy`. Defaults to None.
            visible: Wether the `Enemy` is drawn. Defaults to True.
            name: The pawn's name. Defaults to None.
            hitbox_radius: The radius of the `Enemy`'s hitbox. If `None`, this
                value is equivalent to `size`. Defaults to None.
        """
        super().__init__(
            game=game,
            shape=shape,
            size=size,
            color=color,
            pos=pos,
            speed=speed,
            turn_speed=turn_speed,
            visible=visible,
            hitbox_radius=hitbox_radius,
        )
        behavior.register_owner(self)
        self._behavior = behavior
        self.headingless: bool = headingless
        self.behavior_loop(game.screen)

    def behavior_loop(self, screen: turtle.Screen):
        """Repeated calls the enemy behavior's `enact` method after a short
        delay.
        """
        self._behavior.enact()
        screen.ontimer(partial(self.behavior_loop, screen), 400)
