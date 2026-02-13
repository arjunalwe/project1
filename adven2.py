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
    _item_meta: dict[str, dict]
    _location_actions: list[dict]
    current_location_id: int  # Suggested attribute, can be removed
    ongoing: bool  # Suggested attribute, can be removed
    flags: dict[str, bool]
    inventory: list[Item]

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
        self._locations, self._items, self._item_meta, self._location_actions, self.flags = \
            self._load_game_data(game_data_file)

        # Suggested attributes (you can remove and track these differently if you wish to do so):
        self.current_location_id = initial_location_id  # game begins at this location
        self.ongoing = True  # whether the game is ongoing
        self.inventory = []

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], dict[str, Item], dict[str, dict], list[dict],
                                               dict[str, bool]]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        and (2) a list of all Item objects."""

        with open(filename, 'r') as f:
            data = json.load(f)  # This loads all the data from the JSON file

        locations = {}
        for loc_data in data['locations']:  # Go through each element associated with the 'locations' key in the file
            location_obj = Location(loc_data['id'], loc_data['brief_description'], loc_data['long_description'],
                                    loc_data['available_commands'], loc_data['items'])
            locations[loc_data['id']] = location_obj

        items = {}
        item_meta = {}
        # TODO: Add Item objects to the items list; your code should be structured similarly to the loop above
        # YOUR CODE BELOW
        for item_data in data['items']:
            item_obj = Item(item_data['name'], item_data['description'], item_data['start_position'],
                            item_data['target_position'], item_data['target_points'])
            items[item_data['name']] = item_obj
            item_meta[item_data['name']] = item_data

        location_actions = data.get('location_actions', [])
        initial_flags = data.get('initial_flags', {})
        return locations, items, item_meta, location_actions, initial_flags

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return Location object associated with the provided location ID.
        If no ID is provided, return the Location object associated with the current location.
        """

        # TODO: Complete this method as specified
        # YOUR CODE BELOW
        if loc_id is None:
            return self._locations[self.current_location_id]
        else:
            return self._locations[loc_id]

    def get_item(self, item: str) -> Item:
        """
        SOMETHING
        """
        return self._items[item]

    def _resolve_item_name(self, raw_name: str) -> Optional[str]:
        """Return the canonical item name matching raw_name (case-insensitive).

        Return None if there is no item with this name.
        """
        target = raw_name.strip().lower()
        for name in self._items:
            if name.lower() == target:
                return name
        return None

    def _has_item(self, item_name: str) -> bool:
        """Return whether the player currently has item_name in their inventory."""
        return any(it.name == item_name for it in self.inventory)

    def _apply_effects(self, effects: list[dict]) -> None:
        """Apply a list of data-driven effects."""
        for effect in effects:
            effect_type = effect.get('type')

            if effect_type == 'print':
                print(effect.get('message', ''))

            elif effect_type == 'set_flag':
                flag = effect.get('flag')
                value = effect.get('value')
                if isinstance(flag, str) and isinstance(value, bool):
                    self.flags[flag] = value

    def _try_location_action(self, command: str) -> bool:
        """Try to execute a special location action defined in the JSON.

        Return True iff an action was executed.
        """
        for rule in self._location_actions:
            if rule.get('command', '').lower() != command:
                continue
            if self.current_location_id not in rule.get('locations', []):
                continue

            self._apply_effects(rule.get('effects', []))
            return True
        return False

    def try_pickup(self, raw_item_name: str) -> bool:
        """Try to pick up an item from the current location.

        Return True iff the pickup succeeded.
        """
        location = self.get_location()
        canonical = self._resolve_item_name(raw_item_name)
        if canonical is None:
            print("That item doesn't exist.")
            return False

        # Item must be present in the current location.
        location_item_match = None
        for loc_item in location.items:
            if loc_item.lower() == canonical.lower():
                location_item_match = loc_item
                break
        if location_item_match is None:
            print("That item isn't here.")
            return False

        # Enforce data-driven pickup requirements (e.g., flags).
        meta = self._item_meta.get(canonical, {})
        req_flags = meta.get('pickup_requires_flags', {})
        for flag, required_val in req_flags.items():
            if self.flags.get(flag) != required_val:
                for msg in meta.get('pickup_fail_messages', []):
                    print(msg)
                return False

        # Success.
        location.items.remove(location_item_match)
        if not self._has_item(canonical):
            self.inventory.append(self.get_item(canonical))

        for msg in meta.get('pickup_success_messages', []):
            print(msg)
        if not meta.get('pickup_success_messages'):
            print(f"Picked up {canonical}.")
        return True

    def try_drop(self, raw_item_name: str) -> bool:
        """Try to drop an item into the current location.

        Return True iff the drop succeeded.
        """
        canonical = self._resolve_item_name(raw_item_name)
        if canonical is None:
            print("That item doesn't exist.")
            return False

        for i, it in enumerate(self.inventory):
            if it.name == canonical:
                self.inventory.pop(i)
                self.get_location().items.append(canonical)
                print(f"Dropped {canonical}.")
                return True

        print("You don't have that item.")
        return False

    def try_use(self, raw_item_name: str) -> bool:
        """Try to use an item currently in the player's inventory.

        Return True iff the item was used (i.e., it existed in inventory).
        """
        canonical = self._resolve_item_name(raw_item_name)
        if canonical is None:
            print("That item doesn't exist.")
            return False

        if not self._has_item(canonical):
            print("You can only use items in your inventory.")
            return False

        meta = self._item_meta.get(canonical, {})
        self._apply_effects(meta.get('use_effects', []))
        if not meta.get('use_effects'):
            print(f"You can't use {canonical} right now.")
        return True


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
    game = AdventureGame('game_data.json', 0)  # load data, setting initial location ID to 1
    menu = ["look", "inventory", "score", "log", "quit"]  # Regular menu options available at each location
    choice = None

    # Note: You may modify the code below as needed; the following starter code is just a suggestion
    while game.ongoing:
        # Note: If the loop body is getting too long, you should split the body up into helper functions
        # for better organization. Part of your mark will be based on how well-organized your code is.

        location = game.get_location()

        # TODO: Add new Event to game log to represent current game location
        #  Note that the <choice> variable should be the command which led to this event
        # YOUR CODE HERE

        # TODO: Depending on whether or not it's been visited before,
        #  print either full description (first time visit) or brief description (every subsequent visit) of location
        # YOUR CODE HERE

        # Display possible actions at this location
        print("What to do? Choose from: look, inventory, score, log, quit")
        print("At this location, you can also:")
        for action in location.available_commands:
            print("-", action)

        # Validate choice
        choice = input("\nEnter action: ").lower().strip()

        def _is_valid_command(cmd: str) -> bool:
            return (
                cmd in menu
                or cmd in location.available_commands
                or cmd.startswith('pick up ')
                or cmd.startswith('pickup ')
                or cmd.startswith('drop ')
                or cmd.startswith('use ')
                or any(rule.get('command', '').lower() == cmd for rule in game._location_actions)
            )

        while not _is_valid_command(choice):
            print("That was an invalid option; try again.")
            choice = input("\nEnter action: ").lower().strip()

        print("========")
        print("You decided to:", choice)

        if choice in menu:
            # TODO: Handle each menu command as appropriate
            if choice == "log":
                game_log.display_events()
            # ENTER YOUR CODE BELOW to handle other menu commands (remember to use helper functions as appropriate)

        else:
            # Handle non-menu actions

            if choice in location.available_commands:
                # Movement
                game.current_location_id = location.available_commands[choice]

            elif choice.startswith('pick up '):
                game.try_pickup(choice[len('pick up '):])

            elif choice.startswith('pickup '):
                game.try_pickup(choice[len('pickup '):])

            elif choice.startswith('drop '):
                game.try_drop(choice[len('drop '):])

            elif choice.startswith('use '):
                game.try_use(choice[len('use '):])

            else:
                # Data-driven special actions tied to locations
                game._try_location_action(choice)
