"""CSC111 Project 1: Text Adventure Game - Simulator

This module provides a non-interactive "simulator" for your Project 1 game.

It is meant for:
- validating a command sequence (e.g., your win walkthrough) by checking the
  resulting location ID log, and
- generating demo runs for required game features (win/lose/inventory/score/enhancements),
  as referenced by the project report. fileciteturn3file1

Important design note:
- This simulator is intentionally *data-driven*: it executes the same commands
  your interactive loop supports, using the AdventureGame class and the JSON file.
  It does not hard-code world-specific logic.
"""
from __future__ import annotations

import random
from typing import Callable

from adventure import AdventureGame
from event_logger import Event, EventList
from game_entities import Location


# A fixed seed makes simulations reproducible even if the game uses randomness
# (e.g., movement costs). This is not world-specific; it's just for stable demos.
DEFAULT_SIMULATION_SEED = 2026


class AdventureGameSimulation:
    """A simulation of an adventure game playthrough.

    The simulation:
      - constructs an AdventureGame from a JSON file
      - records a starting Event
      - executes each command in order
      - records an Event after each command (even if the location does not change)

    This mirrors the pattern used in your interactive loop in adventure.py, where
    an event is appended after each player action. fileciteturn3file11
    """

    _game: AdventureGame
    _events: EventList

    def __init__(
        self,
        game_data_file: str,
        initial_location_id: int,
        commands: list[str],
        *,
        seed: int = DEFAULT_SIMULATION_SEED,
    ) -> None:
        random.seed(seed)

        self._events = EventList()
        self._game = AdventureGame(game_data_file, initial_location_id)

        start_loc = self._game.get_location()
        self._events.add_event(Event(start_loc.id_num, start_loc.long_description))

        for command in commands:
            self._execute_command(command)
            current = self._game.get_location()
            self._events.add_event(Event(current.id_num, current.long_description), command)


    def get_id_log(self) -> list[int]:
        """Return the list of visited location IDs for this simulation."""
        return self._events.get_id_log()

    def run(self) -> None:
        """Print the simulation transcript."""
        curr = self._events.first
        while curr is not None:
            print(curr.description)
            if curr is not self._events.last:
                print("You choose:", curr.next_command)
            curr = curr.next


    def _execute_command(self, command: str) -> None:
        """Execute one command against the underlying AdventureGame."""
        location = self._game.get_location()

        menu = self._menu()
        special_cmds = self._game.get_special_commands()
        all_actions = set(menu) | set(location.available_commands) | set(special_cmds)

        if command not in all_actions and not command.startswith("talk "):
            raise ValueError(f"Invalid command for simulation at location {location.id_num}: {command!r}")

        if command in self._menu_handlers():
            self._menu_handlers()[command](location)
        elif command.startswith("talk "):
            self._game.run_talk(command.replace("talk ", "", 1))
        elif command in special_cmds:
            self._game.run_interaction(command)
        else:
            self._game.move(command)

    def _menu(self) -> list[str]:
        """Return the menu commands, using settings if provided by the JSON."""
        default_menu = ["look", "inventory", "score", "log", "search", "quit"]
        return list(self._game.settings.get("menu", default_menu))

    def _menu_handlers(self) -> dict[str, Callable[[Location], None]]:
        """Handlers for menu commands, implemented non-interactively for simulation."""
        return {
            "log": lambda _: self._events.display_events(),
            "quit": lambda _: setattr(self._game, "ongoing", False),
            "look": lambda loc: print(loc.long_description),
            "search": lambda loc: self._run_search(loc),
            "inventory": lambda _: self._print_inventory(),
            "score": lambda _: print("Score:", self._game.score),
        }

    def _run_search(self, location: Location) -> None:
        """Simulate the 'search' command (pickup items in current location)."""
        if location.items:
            print(f"\nYou found: {', '.join([i.name for i in location.items])}!\n")
            self._game.update_inventory(location.items)
        else:
            print("\nYou turned up empty handed!\n")

    def _print_inventory(self) -> None:
        """Print inventory contents without requiring interactive input."""
        if not self._game.inventory:
            print("Your inventory is empty!")
            return

        print("\n--- Inventory ---")
        for _, (item, count) in self._game.inventory.items():
            print(f"{item.name} (x{count})")
        print("-----------------")


if __name__ == "__main__":

    GAME_DATA_FILE = "game_data.json"
    INITIAL_LOCATION_ID = 0  # update if your JSON uses a different starting location

    # Demo 1: a winning walkthrough (example for this game_data.json)
    win_walkthrough = [
        "shower",
        "exit",
        "exit",
        "talk reuben",
        "go north",
        "go north",
        "search jacket pile",
        "go south",
        "go south",
        "talk reuben",
        "go north",
        "go east",
        "open locker",
        "search",
        "go west",
    ]

    # The expected log is the sequence of location IDs after each command,
    # including the starting location at the beginning.
    expected_log = [
        0,  # start
        0,  # shower
        1,  # exit
        2,  # exit
        2,  # talk reuben
        3,  # go north
        6,  # go north
        6,  # search jacket pile
        3,  # go south
        2,  # go south
        2,  # talk reuben
        3,  # go north
        8,  # go east
        8,  # open locker
        8,  # search
        3,  # go west
    ]

    # Demo 2: losing demo (fill this in to match your lose condition(s))
    lose_demo: list[str] = []

    # Demo 3: inventory demo (pick up at least one item + show inventory)
    inventory_demo = [
        "exit",
        "search",
        "inventory",
        "go home",
        "inventory",
    ]

    # Demo 4: scores demo (fill this in once score can increase in your game)
    scores_demo: list[str] = ["score"]

    # ---------------------------------------------------------------------
    # Quick self-check (optional)
    # ---------------------------------------------------------------------
    sim = AdventureGameSimulation(GAME_DATA_FILE, INITIAL_LOCATION_ID, win_walkthrough)
    assert sim.get_id_log() == expected_log, (sim.get_id_log(), expected_log)
    # sim.run()
