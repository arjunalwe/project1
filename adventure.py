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
from typing import Optional, Any
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
    current_location_id: int  # Suggested attribute, can be removed
    ongoing: bool  # Suggested attribute, can be removed
    is_clean: bool
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
        self._locations, self._items, self.flags, self._rules, self._npcs, self._interactions = self._load_game_data(game_data_file)

        # Suggested attributes (you can remove and track these differently if you wish to do so):
        self.current_location_id = initial_location_id  # game begins at this location
        self.ongoing = True  # whether the game is ongoing

        self.is_clean = False   # the player didn't shower yet, so they're not clean at the start of the game
        self.inventory = []

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], dict[str, Item], dict[str, bool], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Load locations and items from a JSON file with the given filename and
        return a tuple consisting of (1) a dictionary of locations mapping each game location's ID to a Location object,
        and (2) a list of all Item objects."""

        with open(filename, 'r') as f:
            data = json.load(f)  # This loads all the data from the JSON file

        flags = data.get('initial_flags', {})
        rules = data.get('rules', [])
        npcs = data.get('npcs', [])
        interactions = data.get('interactions', [])

        locations = {}
        for loc_data in data['locations']:  # Go through each element associated with the 'locations' key in the file
            location_obj = Location(loc_data['name'], loc_data['id'], loc_data['brief_description'], loc_data['long_description'],
                                    loc_data['available_commands'], loc_data['items'])
            locations[loc_data['id']] = location_obj

        items = {}
        # TODO: Add Item objects to the items list; your code should be structured similarly to the loop above
        # YOUR CODE BELOW
        for item_data in data['items']:
            item_obj = Item(item_data['name'], item_data['description'], item_data['start_position'],
                            item_data['target_position'], item_data['target_points'])
            items[item_data['name']] = item_obj

        return locations, items, flags, rules, npcs, interactions

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

    def _requirements_met(self, req: dict[str, Any]) -> bool:
        """Return whether the given requirements dictionary is satisfied by the current game state.

        Supported requirements:
            - flags: {flag_name: bool}
        """
        flags_req = req.get('flags', {})
        for flag, val in flags_req.items():
            if self.flags.get(flag) != val:
                return False
        return True

    def _apply_effects(self, effects: list[dict[str, Any]], location: Location) -> None:
        """Apply the given effects to the game state."""
        for eff in effects:
            eff_type = eff.get('type')

            if eff_type == 'print':
                print(eff.get('message', ''))

            elif eff_type == 'set_flag':
                self.flags[eff['flag']] = eff['value']

            elif eff_type == 'spawn_item_here':
                item_name = eff['item']
                # Avoid duplicates by name
                if not any(it.name == item_name for it in location.items):
                    location.items.append(self.get_item(item_name))

    def eval_rules(self) -> None:
        """Evaluate all rules and apply any matching ones.

        This is generic: it does not mention any specific quest/location/item.
        """
        for rule in self._rules:
            when = rule.get('when', {})

            # Turn-move based trigger
            if 'moves_at_least' in when and self.turn_moves < when['moves_at_least']:
                continue

            # Flag requirements inside 'when'
            if not self._requirements_met({'flags': when.get('flags', {})}):
                continue

            # Apply effects
            self._apply_effects(rule.get('then', []), self.get_location())

    def can_talk(self, npc_name: str, location: Location) -> bool:
        """Return whether the named NPC exists at the given location."""
        for npc in self._npcs:
            if npc.get('name') == npc_name and npc.get('location') == location.id_num:
                return True
        return False

    def talk(self, npc_name: str, location: Location) -> bool:
        """Talk to an NPC at the given location. Return True iff someone was talked to."""
        for npc in self._npcs:
            if npc.get('name') == npc_name and npc.get('location') == location.id_num:
                for line in npc.get('dialogue', []):
                    if self._requirements_met(line.get('requires', {})):
                        print(line.get('say', ''))
                        self._apply_effects(line.get('effects', []), location)
                        return True
                # NPC exists but no dialogue matched
                print("They don't have anything new to say.")
                return True
        return False

    def can_run_interaction(self, command: str, location: Location) -> bool:
        """Return whether the command is a defined interaction at the given location."""
        for inter in self._interactions:
            if inter.get('command') == command and location.id_num in inter.get('locations', []):
                return True
        return False

    def run_interaction(self, command: str, location: Location) -> bool:
        """Run a location interaction command. Return True iff an interaction was processed."""
        for inter in self._interactions:
            if inter.get('command') == command and location.id_num in inter.get('locations', []):
                if self._requirements_met(inter.get('requires', {})):
                    self._apply_effects(inter.get('effects', []), location)
                else:
                    # Interaction exists here, but requirements not met
                    # (Keep it simple; the JSON can include alternate interactions for failure cases.)
                    print("Nothing happens.")
                return True
        return False



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
    menu = ["look", "inventory", "score", "log", "quit"]  # Regular menu options available at each location
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
        print("What to do? Choose from: look, inventory, score, log, quit")
        print("At this location, you can also:")
        for action in location.available_commands:
            print("-", action)

        # Validate choice
        choice = input("\nEnter action: ").lower().strip()
        while (choice not in location.available_commands
               and choice not in menu
               and not choice.startswith('talk ')
               and not game.can_run_interaction(choice, location)):
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
            did_turn_move = False

            # TALK TO NPCS (data-driven)
            if choice.startswith('talk '):
                npc_name = choice[len('talk '):].strip()
                if npc_name == '':
                    print("Talk to who?")
                elif game.talk(npc_name, location):
                    did_turn_move = True
                else:
                    print("No one by that name is here.")

            # LOCATION INTERACTIONS (data-driven)
            elif game.run_interaction(choice, location):
                did_turn_move = True

            # DEFAULT: MOVE/TRAVEL using available_commands
            else:
                result = location.available_commands[choice]
                game.current_location_id = result
                did_turn_move = True

            # Tick turn counter + evaluate rules after turn moves
            if did_turn_move:
                game.turn_moves += 1
                game.eval_rules()

            # TODO: Add in code to deal with actions which do not change the location (e.g. taking or using an item)
            # TODO: Add in code to deal with special locations (e.g. puzzles) as needed for your game
