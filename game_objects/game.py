from __future__ import annotations

import threading
import time
import turtle
from functools import partial

import behaviors
import config
from enums import Direction, GameState
from game_objects.arena import Arena
from game_objects.pawns import Enemy, Pawn, Player


class Game:

    def __init__(
        self,
        arena: Arena | None = None,
        screen: turtle.Screen | None = None,
        config: config.Config = config.Config(),
    ):
        """Initializes the Game object.

        Args:
            arena: The arena object the game will use.
                If `None`, an `Arena` with the default parameters will be created.
                Defaults to None.
            screen: The turtle Screen instance to use. If `None`, a Screen is
                created automatically. Defaults to None.
            config: The game configuration settings to use.
        """
        # frankly, idk if providing a screen is even necessary...
        self.screen = screen or turtle.Screen()
        self.arena: Arena = arena or Arena()
        self.config: config.Config = config

        self._state = GameState.FROZEN
        self._pawns: list[Pawn] = []
        self._players: list[Player] = []
        self._enemies: list[Enemy] = []

        self._score = 0
        self._round_start_time: float = 0
        self._level = 1

        self._score_turt = turtle.Turtle()
        self._score_turt.hideturtle()
        self._score_turt.speed(0)
        self._score_turt.penup()
        self._score_turt.goto(arena.border_len // 2, arena.border_len // 2)

        self._level_turt = turtle.Turtle()
        self._level_turt.hideturtle()
        self._level_turt.speed(0)
        self._level_turt.penup()
        self._level_turt.goto(0, arena.border_len // 2)

        self._levelup_timer: threading.Timer | None = None

        threading.Thread(target=self._update_score_display_loop, daemon=True).start()

    def begin_level(self, *, level_duration: int | float | None = None):
        """Starts the currently set level.

        This function puts the game in `EVADE` mode for `level_duration` seconds.
        After `level_duration` seconds, `level` is incremented and the game is
        put into `PATH` mode until `begin_level` is next called.

        Args:
            level_duration: The duration of the level in seconds. If `None`,
                duration is calculated using game configurations settings.
                Defaults to None.
        """

        if self._round_start_time != 0 or (
            self._levelup_timer is not None and self._levelup_timer.is_alive()
        ):
            print("Currently in Level; cannot start!")
            return

        self._round_start_time = time.time()
        self.set_state(GameState.EVADE)
        self._levelup_timer = threading.Timer(
            level_duration or self.config.calculate_level_duration(self._level),
            lambda: self.set_level(self._level + 1),
        )
        self._levelup_timer.start()

    def set_level(self, level: int, *, paths: int | None = None):
        """Sets the current level, running any level configuration functions and
        other level preparation materials.

        This function:
        - calls the LevelAction associated with `level`, if there is one
        - finalizes player score for the level
        - gives players paths based on the level
        - adds the level score bonus from the prior level

        These are all configured using the `Config` object given to the `Game`.

        Args:
            level: The level to set the game
            paths: The number of paths to give players. Overrides paths calculated
                using game configuration. Defaults to None.
        """

        self.config.levels.get_action(level)(self)

        if self._round_start_time != 0:

            self._score += self.config.calculate_score_per_second(self._level) * (
                time.time() - self._round_start_time
            )
            self._round_start_time = 0

        self.set_state(GameState.PATH)
        for player in self.players:
            player.paths = paths or self.config.calculate_level_paths(level)

        if level != 1:
            self._score += self.config.calculate_levelup_score_bonus(level - 1)
            self._write_score(self._score)

        self._level = level

        self._level_turt.clear()
        self._level_turt.write(
            f"Level: {self._level}", align="center", font=("Monospace", 15, "normal")
        )

    def set_state(self, state: GameState):
        """Sets the game state

        Args:
            state: The new game state to use.
        """
        self._state = state

    def gameover(self):
        """Ends the game."""
        print("GAMEOVER")
        self.set_state(GameState.FROZEN)

    def add_pawn(self, pawn: Pawn):
        """Adds a pawn to the game. `Player`s and `Enemy`s are automatically
        distinguished.

        Args:
            pawn: The pawn to add.
        """
        self._pawns.append(pawn)
        if isinstance(pawn, Enemy):
            self._enemies.append(pawn)
        elif isinstance(pawn, Player):
            self._players.append(pawn)

    def _write_score(self, score: int):
        """Writes the given score to the screen.

        Args:
            score: The score to print.
        """
        self._score_turt.clear()
        self._score_turt.write(
            f"Score: {score:.2f}",
            align="right",
            font=("Roboto Mono", 15, "normal"),
        )

    def _update_score_display_loop(self):
        """Loop that updates game score based elapsed time during the round."""
        while True:
            if self.is_evade_mode:
                current_score = self._score + self.config.calculate_score_per_second(
                    self._level
                ) * (time.time() - self._round_start_time)
                self._write_score(current_score)

            time.sleep(self.config.score_update_interval)

    def update(self):
        """Updates the screen and checks for `Player`-`Enemy` collisions if
        in `EVADE` mode.
        """

        if self.is_evade_mode:
            for player in self._players:
                for enemy in self._enemies:
                    if player.intersects(enemy):
                        self.gameover()
                        return

        self.screen.update()
        self.screen.ontimer(self.update, self.config.tick_interval_ms // 2)

    def mainloop(self):
        """"""
        player = Player(self, turn_speed=-1)
        # enemy = Enemy(
        #     self,
        #     behaviors.ChaseBehavior(player),
        #     size=1,
        #     speed=5,
        #     turn_speed=0,
        #     headingless=True,
        # )
        # charger = Enemy(
        #     self,
        #     behavior=behaviors.ChargeBehavior(player),
        #     size=1,
        #     color="blue",
        #     shape="triangle",
        #     speed=10,
        #     turn_speed=1.5,
        # )
        self.add_pawn(player)
        # self.add_pawn(enemy)
        # self.add_pawn(charger)
        self.arena.draw_border()

        self.screen.onkeypress(partial(player.threaded_move, Direction.WEST), "a")
        self.screen.onkeypress(partial(player.threaded_move, Direction.EAST), "d")
        self.screen.onkeypress(partial(player.threaded_move, Direction.NORTH), "w")
        self.screen.onkeypress(partial(player.threaded_move, Direction.SOUTH), "s")
        self.screen.onkeypress(partial(player.threaded_move, Direction.WEST), "Left")
        self.screen.onkeypress(partial(player.threaded_move, Direction.EAST), "Right")
        self.screen.onkeypress(partial(player.threaded_move, Direction.NORTH), "Up")
        self.screen.onkeypress(partial(player.threaded_move, Direction.SOUTH), "Down")
        self.screen.onkeypress(lambda: self.set_state(GameState.EVADE), " ")

        self.set_state(GameState.PATH)
        # enemy.refresh(self.screen)
        # charger.refresh(self.screen)
        listener = threading.Thread(target=self.screen.listen, daemon=True)
        listener.start()

        # screen.listen()

        self.screen.tracer(0, 0)
        self.update()
        print(threading.activeCount())
        for thread in threading.enumerate():
            print(thread.name)

        self.set_level(1)
        self.screen.mainloop()

    @property
    def pawns(self) -> list[Pawn]:
        """List of pawns in the `Game`."""
        return self._pawns

    @property
    def players(self) -> list[Player]:
        """List of Players in the Game."""
        return self._players

    @property
    def enemies(self) -> list[Enemy]:
        """List of Enemies in the Game"""
        return self._enemies

    @property
    def score(self) -> float:
        """Current player score."""
        return self._score

    @property
    def level(self) -> int:
        """Current level.

        Level can be set with `set_level`.
        """
        return self._level

    @property
    def state(self) -> GameState:
        """The current Game state."""
        return self._state

    @property
    def is_frozen(self) -> bool:
        """Whether the game is in the `FRONZEN` state."""
        return self._state == GameState.FROZEN

    @property
    def is_path_mode(self) -> bool:
        """Whether the game is in the `PATH` state."""
        return self._state == GameState.PATH

    @property
    def is_evade_mode(self) -> bool:
        """Whether the game is in the `EVADE` state."""
        return self._state == GameState.EVADE
