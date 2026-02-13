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
from typing import Optional

from game_entities import Location, Item
from event_logger import Event, EventList

import random


# Note: You may add in other import statements here as needed

# Note: You may add helper functions, classes, etc. below as needed


class AdventureGame:
    """A text adventure game class storing all location, item and map data.

    Instance Attributes:
        - # TODO add descriptions of public instance attributes as needed

    Representation Invariants:
        - # TODO add any appropriate representation invariants as needed
    """

    # Private Instance Attributes (do NOT remove these two attributes):
    #   - _locations: a mapping from location id to Location object.
    #                       This represents all the locations in the game.
    #   - _items: a list of Item objects, representing all items in the game.

    _locations: dict[int, Location]
    _items: dict[str, Item]
    current_location_id: int  # Suggested attribute, can be removed
    ongoing: bool  # Suggested attribute, can be removed
    movement_timer: int
    health_bar: int
    hungry: bool
    inventory: dict[str, list]

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        """
        Initialize a new text adventure game, based on the data in the given file, setting starting location of game
        at the given initial location ID.
        (note: you are allowed to modify the format of the file as you see fit)

        Preconditions:
        - game_data_file is the filename of a valid game data JSON file
        """

        # NOTES:
        # You may add parameters/attributes/methods to this class as you see fit.

        # Requirements:
        # 1. Make sure the Location class is used to represent each location.
        # 2. Make sure the Item class is used to represent each item.

        # Suggested helper method (you can remove and load these differently if you wish to do so):
        self._locations, self._items = self._load_game_data(game_data_file)

        # Suggested attributes (you can remove and track these differently if you wish to do so):
        self.current_location_id = initial_location_id  # game begins at this location
        self.ongoing = True  # whether the game is ongoing

        self.is_clean = False  # the player didn't shower yet, so they're not clean at the start of the game
        self.inventory = {}

        self.movement_timer = 120

        self.health_bar = 5
        self.hungry = False

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], dict[str, Item]]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        and (2) a list of all Item objects."""

        with open(filename, 'r') as f:
            data = json.load(f)  # This loads all the data from the JSON file

        items = {}
        for item_data in data['items']:
            item_obj = Item(item_data['name'], item_data['description'], item_data['start_position'],
                            item_data['target_position'], item_data['target_points'])
            items[item_data['name']] = item_obj

        locations = {}
        for loc_data in data['locations']:  # Go through each element associated with the 'locations' key in the file
            location_obj = Location(loc_data['name'], loc_data['id'], loc_data['brief_description'],
                                    loc_data['long_description'],
                                    loc_data['available_commands'], [items[i] for i in loc_data['items']])
            locations[loc_data['id']] = location_obj

        return locations, items

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        """
        if loc_id is None:
            return self._locations[self.current_location_id]
        else:
            return self._locations[loc_id]

    def get_item(self, item: str) -> Item:
        """
        SOMETHING
        """
        return self._items[item]

    def update_inventory(self, loc_items: list[Item]) -> None:
        """
        Add items from a location to the player's inventory.
        """
        for i in loc_items:
            name = i.name.lower()
            if name in self.inventory:
                self.inventory[name][1] += 1
            else:
                self.inventory[name] = [i, 1]

        loc_items.clear()

    def manage_inventory(self, current_location: Location) -> None:
        """
        Handles the interactive inventory menu: display items, select one, and drop/exit.
        """
        if not self.inventory:
            print("Your inventory is empty!")
            return

        # Start a loop so the player can manage multiple items without re-typing 'inventory'
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



if __name__ == "__main__":
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    # import python_ta
    # python_ta.check_all(config={
    #     'max-line-length': 120,
    #     'disable': ['R1705', 'E9998', 'E9999', 'static_type_checker']
    # })

    game_log = EventList()  # This is REQUIRED as one of the baseline requirements
    game = AdventureGame('game_data.json', 0)  # load data, setting initial location ID to 0
    menu = ["look", "inventory", "score", "log", "search", "quit"]  # Regular menu options available at each location
    choice = None

    # Note: You may modify the code below as needed; the following starter code is just a suggestion
    while game.ongoing:
        # Note: If the loop body is getting too long, you should split the body up into helper functions
        # for better organization. Part of your mark will be based on how well-organized your code is.

        location = game.get_location()

        # TODO: idk why but log says that all the commands are None
        curr_event = Event(location.id_num, location.long_description, None, None, game_log.get_last())
        game_log.add_event(curr_event)
        print("Location: ", location.name)
        if location.visited:
            print(location.brief_description)
        else:
            print(location.long_description)

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

        if choice in menu:
            if choice == "log":
                game_log.display_events()

            elif choice == "quit":
                break

            elif choice == "inventory":
                game.manage_inventory(location)

            elif choice == "search":
                if len(location.items) > 0:
                    print(f"\nYou found: {', '.join([i.name for i in location.items])}!\n")
                    game.update_inventory(location.items)
                else:
                    print("\nYou turned up empty handed!\n")

            elif choice == "look":
                if location.visited:
                    print(location.brief_description)
                else:
                    print(location.long_description)

            # ENTER YOUR CODE BELOW to handle other menu commands (remember to use helper functions as appropriate)

        else:
            # Handle non-menu actions

            # UPDATE LOCATION
            result = location.available_commands[choice]
            game.current_location_id = result

            if choice in location.available_commands:
                if game.hungry:
                    game.movement_timer -= random.randint(10, 16)
                else:
                    game.movement_timer -= random.randint(5, 8)

                game.health_bar -= 1
                if game.health_bar == 0:
                    game.hungry = True

            # TODO: Add in code to deal with actions which do not change the location (e.g. taking or using an item)
            # TODO: Add in code to deal with special locations (e.g. puzzles) as needed for your game







