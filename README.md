# path-mania

***THIS GAME IS A WORK IN PROGRESS: THINGS ARE APT TO CHANGE AND GENERALLY UNFINISHED. EVENT THIS README IS VERY UNFINISHED!***

A game that started as a school project, `path-mania` is a game about creating paths and avoiding enemies! You can essentially think of it as PacMan but the map is created by you as the game progresses. Additionally, there are several enemy types with varying abilities!

## Project History

As stated above, this was a quick project I did for a high school programming class.
The original code (in all its laggy glory) can be found in the `old` directory. For the updated version, I completely started from scratch, using skills and knowledge I've learned since to update and improve the game. Most notably, it's not absurdly laggy!

To keep in the spirit of the original one-file, terribly optimized game I created years ago, I used Python's `turtle` module for all graphics rendering. To improve performance, however, I had to abandon its movement and heading functions in favor of custom ones.

I also like to think I've improved on the pathfinding system greatly, pre-calculating distances to the player whenever changes to the map are submitted, allowing them to be instantly retrieved with a dictionary. It may not be the best solution, but it beats doing calculations on every game update.

## Project Goal

My goal with this game is to make it easy to customize and modify.

## Running the Project

This project is compatible with vanilla Python 3.12! As long as you have all the standard packages, you should be good to go:

```sh
python path_mania.py
```

## Game Info

The objective of the game, as of now, is to survive. You lose when you make contact with enemies (anything that moves and isn't you), so just avoid those and you'll be good.

Since this game is a work-in-progress, the levels are still being worked on. Feel free to  mess around with the game and level configurations in the meantime!

### Game Phases

The game has two main phases: path and evade.

#### Path

In **path** mode, you are invulnerable and place paths (black lines) when moving. Paths cannot be placed on top of each other, and you *MUST* place *all* paths before continuing.

#### Evade

Immediately upon placing your final path, you enter **evade** mode. While in evade mode, touching an enemy immediately ends the game (you lose). Additionally, you can only move using the paths you made; enemies must (generally) follow your paths as well. Evade mode is time-based; after a time threshold is met, you progress to the  next level and enter path mode with more paths to place.

### Controls

- `W` - move up
- `A` - move left
- `S` - move down
- `D` - move right

### Customizing Your Game

*(Just as another reminder, this game is unfinished; there will likely be more in the future, assumming I don't abandon the project.)*

Aside from just modifying the source code, you can customize your game using the `Config` object. For now, modify the one located in `path_mania.py`.

Here are the configuration options:

- `tps` - stands for "ticks per second", or the number of game updates per second
- `score_update_interval` - how often to update the score counter (in second)
- `score_per_sec` - the score to earn per second in evade mode
- `level_score_modifier` - with each increase in level, increment `score_per_sec` by this amount
- `levelup_score_bonus` - bonus score to give upon level completion
- `levelup_score_modifier` - with each increase in level, increment `levelup_score_bonus` by this amount
- `level_duration` - The duration of each level
- `level_duration_modifier` - with each increase in level, increment `level_duration` by this amount (can be negative)
- `level_duration_min` - The shortest level duration allowed (should not be negative) (restricts the effects of `level_duration_modifier`)
- `level_duration_max` - The the longest level duration allowed (should not be negative) (restricts the effects of `level_duration_modifier`)
- `paths` - The number of paths to give the player per level
    - NOTE: paths will never exceed the number of paths the player can place on the map
- `level_path_modifier` - The number of paths to add to `paths` with each level above 1.
- `paths_max` - The maximum number of paths that can be given to a player after a level (restricts the effects of `level_path_modifier`)
- `paths_min` - The minimum number of paths that can be given to a player after a level (restricts the effects of `level_path_modifier`)

The final option, `levels`, determines what happens during each level. It's a bit more complex, so it will get its own section.

#### Level Actions

`LevelAction`s are functions that do something when the game level increases. All this looks like in code is a function that takes a `Game` object as its only argument, then does whatever it wants with it. There are a few `LevelAction` factories, however, that allow you to create simple actions without have to define your own functions manually (e.g., spawning a new enemy). 

Level actions are the *most* work-in-progress aspect of this game so far. Here's an example of setting them up:

```python
import level_actions
import behaviors

manager = level_actions.LevelActionManager()

manager.add_action(
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
```

The `LevelActionManager` is essentially a glorified dictionary storing `LevelActions`. Actions can be added using the `add_action` method, which takes in the level to perform the action at and the `LevelAction`. The `Game` object will call the `LevelAction` when a level is set; thus, actions run at the start of a path mode. 

You do not need to manually set an action for every level: you may set a default `LevelAction` that runs in the absence of a custom-provided action. The default default action does nothing. (Note: if you want to access the currently level from within a default action, you can access it via the game instance provided to the function via the `level` property).

When your `LevelActionmanager` is set up, set it to the `levels` attribute of your game's `Config`.

## TODO

- [ ] complete game
- [ ] finish default level action layouts
    - create standard configs at different difficulties?
- [ ] add menu and game over screens
    - even the old version has a game over screen...
- [ ] finish documentation
    - [ ] explain enemy behaviors
    - [ ] explain general code layout probably
    - [ ] perhaps have a "player" README and a "dev" README
        - player just tells you how to play the game and load configs
        - dev is for developers who want to make changes but not necessarily have to scour source code.
