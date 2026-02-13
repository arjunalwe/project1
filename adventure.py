from __future__ import annotations
import json
from typing import Optional

from game_entities import Location, Item
from event_logger import Event, EventList

import random


class AdventureGame:
    _locations: dict[int, Location]
    _items: dict[str, Item]
    current_location_id: int
    ongoing: bool
    movement_timer: int
    health_bar: int
    hungry: bool
    inventory: dict[str, list]
    score: int

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        self._locations, self._items = self._load_game_data(game_data_file)

        self.current_location_id = initial_location_id
        self.ongoing = True

        self.is_clean = False
        self.inventory = {}
        self.score = 0

        self.movement_timer = 120
        self.health_bar = 5
        self.hungry = False

    @staticmethod
    def _load_game_data(filename: str) -> tuple[dict[int, Location], dict[str, Item]]:
        with open(filename, 'r') as f:
            data = json.load(f)

        items = {}
        for item_data in data['items']:
            item_obj = Item(item_data['name'], item_data['description'],
                            item_data['start_position'],
                            item_data['target_position'],
                            item_data['target_points'])
            items[item_data['name']] = item_obj

        locations = {}
        for loc_data in data['locations']:
            location_obj = Location(loc_data['name'], loc_data['id'],
                                    loc_data['brief_description'],
                                    loc_data['long_description'],
                                    loc_data['available_commands'],
                                    [items[i] for i in loc_data['items']])
            locations[loc_data['id']] = location_obj

        return locations, items

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        if loc_id is None:
            return self._locations[self.current_location_id]
        return self._locations[loc_id]

    def get_item(self, item: str) -> Item:
        return self._items[item]

    def update_inventory(self, loc_items: list[Item]) -> None:
        for i in loc_items:
            name = i.name.lower()
            if name in self.inventory:
                self.inventory[name][1] += 1
            else:
                self.inventory[name] = [i, 1]
        loc_items.clear()

    def manage_inventory(self, current_location: Location) -> None:
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


if __name__ == "__main__":
    game_log = EventList()
    game = AdventureGame('game_data.json', 0)

    menu = ["look", "inventory", "score", "log", "search", "quit"]
    choice = None

    # Initial event
    start_loc = game.get_location()
    game_log.add_event(Event(start_loc.id_num, start_loc.long_description))

    while game.ongoing:
        location = game.get_location()

        print("Location:", location.name)
        if location.visited:
            print(location.brief_description)
        else:
            print(location.long_description)
            location.visited = True

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
                game.ongoing = False

            elif choice == "inventory":
                game.manage_inventory(location)

            elif choice == "search":
                if len(location.items) > 0:
                    print(f"\nYou found: {', '.join([i.name for i in location.items])}!\n")
                    game.score += len(location.items)
                    game.update_inventory(location.items)
                else:
                    print("\nYou turned up empty handed!\n")

            elif choice == "look":
                print(location.long_description)

            elif choice == "score":
                print(f"Your score is: {game.score}")

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

            # prevent negative timer
            if game.movement_timer < 0:
                game.movement_timer = 0

        # log event after every command
        resulting_loc = game.get_location()
        game_log.add_event(Event(resulting_loc.id_num,
                                 resulting_loc.long_description),
                           choice)
