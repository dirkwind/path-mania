"""A remake of the legendary turtle_game.py with my current knowledge..."""

import sys
import time

import level_actions
from config import Config
from game_objects.arena import Arena
from game_objects.game import Game


# I was obsessed with text scrolling when I was younger...
def text_scroll(string: str) -> None:
    """Text scrolling..."""
    for c in string:
        sys.stdout.write(c)
        sys.stdout.flush()
        if c == ",":
            time.sleep(0.15)
        elif c == ".":
            time.sleep(0.25)
        else:
            time.sleep(0.004)


if __name__ == "__main__":

    # config the game here!
    config = Config()

    arena = Arena(arena_size=20)
    game = Game(arena, config=config)

    game.mainloop()
