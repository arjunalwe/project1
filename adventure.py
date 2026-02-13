"""CSC111 Project 1: Text Adventure Game - Game Manager

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Project 1. Please consult
the project handout for instructions and details.

Copyright and Usage Information
===============================

This file is provided solely for the personal and private use of students
taking CSC111 at the University of Toronto St. George campus. All forms of
distribution of this code, whether as given or with any changes, are
expressly prohibited. For more information on copyright for CSC111 materials,
please consult our Course Syllabus.

This file is Copyright (c) 2026 CSC111 Teaching Team
"""
from __future__ import annotations

import json
import random
from typing import Optional

from event_logger import Event, EventList
from game_entities import Item, Location


# Note: You may add in other import statements here as needed
# Note: You may add helper functions, classes, etc. below as needed


class AdventureGame:
    """A text adventure game class storing all location, item and map data."""

    # Private Instance Attributes (do NOT remove these two attributes):
    #   - _locations: a mapping from location id to Location object.
    #                       This represents all the locations in the game.
    #   - _items: a dictionary mapping item name to Item object, representing all items in the game.

    _locations: dict[int, Location]
    _items: dict[str, Item]

    # Public-ish game state
    current_location_id: int
    ongoing: bool

    # Enhancements / state
    movement_timer: int
    health_bar: int
    hungry: bool
    is_clean: bool
    inventory: dict[str, list]  # {lower_name: [Item, count]}
    score: int

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """Initialize a new text adventure game, based on the data in the given file.

        Preconditions:
        - game_data_file is the filename of a valid game data JSON file
        """
        self._locations, self._items = self._load_game_data(game_data_file)

        self.current_location_id = initial_location_id  # game begins at this location
        self.ongoing = True

        # Player/game state
        self.is_clean = False
        self.inventory = {}
        self.score = 0

        # Timer/health mechanics
        self.movement_timer = 120
        self.health_bar = 5
        self.hungry = False

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], dict[str, Item]]:
        """Load locations and items from a JSON file with the given filename and
        return (locations, items).
        """
        with open(filename, 'r') as f:
            data = json.load(f)

        items: dict[str, Item] = {}
        for item_data in data['items']:
            item_obj = Item(
                item_data['name'],
                item_data['description'],
                item_data['start_position'],
                item_data['target_position'],
                item_data['target_points'],
            )
            items[item_data['name']] = item_obj

        locations: dict[int, Location] = {}
        for loc_data in data['locations']:
            location_obj = Location(
                loc_data['name'],
                loc_data['id'],
                loc_data['brief_description'],
                loc_data['long_description'],
                loc_data['available_commands'],
                [items[i] for i in loc_data['items']],
            )
            locations[loc_data['id']] = location_obj

        return locations, items

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        """
        if loc_id is None:
            return self._locations[self.current_location_id]
        return self._locations[loc_id]

    def get_item(self, item: str) -> Item:
        """Return the Item object with the given name (exact key from the JSON)."""
        return self._items[item]

    def update_inventory(self, loc_items: list[Item]) -> None:
        """Add items from a location to the player's inventory (and clear them from the location)."""
        for i in loc_items:
            name = i.name.lower()
            if name in self.inventory:
                self.inventory[name][1] += 1
            else:
                self.inventory[name] = [i, 1]
        loc_items.clear()

    def manage_inventory(self, current_location: Location) -> None:
        """Interactive inventory menu: display items, select one, and drop/exit."""
        if not self.inventory:
            print("Your inventory is empty!")
            return

        while True:
            print("\n--- Inventory ---")
            for name, data in self.inventory.items():
                print(f"{data[0].name} (x{data[1]})")
            print("-----------------")
            target = input("Select item to manage (or 'exit'): ").lower().strip()

            if target == "exit":
                break

            if target in self.inventory:
                item_entry = self.inventory[target]
                item_obj = item_entry[0]

                print(f"Selected: {item_obj.name}")
                action = input("Action [drop, exit]: ").lower().strip()

                if action == "drop":
                    current_location.items.append(item_obj)
                    item_entry[1] -= 1
                    print(f"Dropped {item_obj.name}.")

                    if item_entry[1] <= 0:
                        del self.inventory[target]

                    if not self.inventory:
                        print("Your inventory is now empty.")
                        break
                elif action != "exit":
                    print("Invalid action.")
            else:
                print("Item not found.")

    def _apply_movement_costs(self) -> None:
        """Apply time/health costs for a turn-move (movement)."""
        if self.hungry:
            self.movement_timer -= random.randint(10, 16)
        else:
            self.movement_timer -= random.randint(5, 8)

        self.movement_timer = max(0, self.movement_timer)

        self.health_bar -= 1
        if self.health_bar <= 0:
            self.health_bar = 0
            self.hungry = True


if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })

    game_log = EventList()  # REQUIRED baseline requirement
    game = AdventureGame('game_data.json', 0)

    menu = ["look", "inventory", "score", "log", "search", "quit"]
    choice: Optional[str] = None

    # Add initial event (starting location; no previous command)
    start_loc = game.get_location()
    game_log.add_event(Event(start_loc.id_num, start_loc.long_description))

    while game.ongoing:
        location = game.get_location()

        print("Location:", location.name)

        # First time at a location: show long description; otherwise show brief description.
        # (The "look" command always prints the long description.)
        if location.visited:
            print(location.brief_description)
        else:
            print(location.long_description)
            location.visited = True

        # Display possible actions at this location
        print(f"What to do? Choose from: {', '.join(menu)}")
        print("At this location, you can also:")
        for action in location.available_commands:
            print("-", action)

        choice = input("\nEnter action: ").lower().strip()
        while choice not in location.available_commands and choice not in menu:
            print("That was an invalid option; try again.")
            choice = input("\nEnter action: ").lower().strip()

        print("========")
        print("You decided to:", choice)

        # Execute the choice (menu commands vs movement commands).
        if choice in menu:
            if choice == "log":
                game_log.display_events()

            elif choice == "quit":
                game.ongoing = False

            elif choice == "inventory":
                game.manage_inventory(location)

            elif choice == "search":
                if len(location.items) > 0:
                    print(f"\nYou found: {', '.join([i.name for i in location.items])}!\n")
                    # Minimal scoring: +1 per item picked up
                    game.score += len(location.items)
                    game.update_inventory(location.items)
                else:
                    print("\nYou turned up empty handed!\n")

            elif choice == "look":
                # Always show the long description when "look" is used
                print(location.long_description)

            elif choice == "score":
                print(f"Your score is: {game.score}")

        else:
            # Movement command: update location and apply movement costs
            next_loc_id = location.available_commands[choice]
            game.current_location_id = next_loc_id
            game._apply_movement_costs()

        # Add an event for *every* command (including non-movement ones).
        # The EventList stores the command on the previous node's <next_command>.
        resulting_loc = game.get_location()
        game_log.add_event(Event(resulting_loc.id_num, resulting_loc.long_description), choice)
