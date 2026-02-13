from __future__ import annotations
import json
import random
from typing import Optional

from game_entities import Location, Item
from event_logger import Event, EventList


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

    # puzzle data from JSON
    flags: dict[str, bool]
    rules: list
    npcs: list
    interactions: list
    moves_made: int

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        (self._locations,
         self._items,
         self.flags,
         self.rules,
         self.npcs,
         self.interactions) = self._load_game_data(game_data_file)

        self.current_location_id = initial_location_id
        self.ongoing = True

        self.inventory = {}
        self.score = 0

        self.movement_timer = 120
        self.health_bar = 5
        self.hungry = False
        self.moves_made = 0

    @staticmethod
    def _load_game_data(filename: str):
        with open(filename, 'r') as f:
            data = json.load(f)

        items = {}
        for item_data in data['items']:
            item = Item(item_data['name'],
                        item_data['description'],
                        item_data['start_position'],
                        item_data['target_position'],
                        item_data['target_points'])
            items[item_data['name']] = item

        locations = {}
        for loc_data in data['locations']:
            loc = Location(loc_data['name'],
                           loc_data['id'],
                           loc_data['brief_description'],
                           loc_data['long_description'],
                           loc_data['available_commands'],
                           [items[i] for i in loc_data['items']])
            locations[loc_data['id']] = loc

        return (locations,
                items,
                data.get("initial_flags", {}),
                data.get("rules", []),
                data.get("npcs", []),
                data.get("interactions", []))

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        if loc_id is None:
            return self._locations[self.current_location_id]
        return self._locations[loc_id]

    # -------------------------
    # Inventory
    # -------------------------
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
            for _, data in self.inventory.items():
                print(f"{data[0].name} (x{data[1]})")
            print("-----------------")
            target = input("Select item to manage (or 'exit'): ").lower().strip()

            if target == "exit":
                break

            if target in self.inventory:
                item_entry = self.inventory[target]
                item_obj = item_entry[0]

                action = input("Action [drop, exit]: ").lower().strip()
                if action == "drop":
                    current_location.items.append(item_obj)
                    item_entry[1] -= 1
                    print(f"Dropped {item_obj.name}.")
                    if item_entry[1] <= 0:
                        del self.inventory[target]
                elif action != "exit":
                    print("Invalid action.")
            else:
                print("Item not found.")

    # -------------------------
    # Flags, rules, effects
    # -------------------------
    def requirements_met(self, requires: dict) -> bool:
        if not requires:
            return True
        for flag, val in requires.get("flags", {}).items():
            if self.flags.get(flag) != val:
                return False
        return True

    def apply_effects(self, effects: list) -> None:
        for eff in effects:
            if eff["type"] == "print":
                print(eff["message"])
            elif eff["type"] == "set_flag":
                self.flags[eff["flag"]] = eff["value"]
            elif eff["type"] == "spawn_item_here":
                item = self._items[eff["item"]]
                self.get_location().items.append(item)

    def apply_rules(self) -> None:
        for rule in self.rules:
            when = rule.get("when", {})
            if "moves_at_least" in when:
                if self.moves_made < when["moves_at_least"]:
                    continue
            if not self.requirements_met(when):
                continue
            self.apply_effects(rule.get("then", []))

    # -------------------------
    # Special commands
    # -------------------------
    def get_special_commands(self) -> list[str]:
        cmds = []

        for npc in self.npcs:
            if npc["location"] == self.current_location_id:
                cmds.append(f"talk {npc['name']}")

        for inter in self.interactions:
            if self.current_location_id in inter["locations"]:
                if self.requirements_met(inter.get("requires", {})):
                    cmds.append(inter["command"])

        return cmds

    def run_talk(self, name: str) -> None:
        for npc in self.npcs:
            if npc["location"] == self.current_location_id and npc["name"] == name:
                for line in npc["dialogue"]:
                    if self.requirements_met(line.get("requires", {})):
                        print(line["say"])
                        self.apply_effects(line.get("effects", []))
                        return
        print("No one by that name is here.")

    def run_interaction(self, command: str) -> None:
        for inter in self.interactions:
            if self.current_location_id in inter["locations"] and inter["command"] == command:
                if self.requirements_met(inter.get("requires", {})):
                    self.apply_effects(inter["effects"])
                else:
                    print("You can't do that yet.")
                return


if __name__ == "__main__":
    game_log = EventList()
    game = AdventureGame('game_data.json', 0)
    menu = ["look", "inventory", "score", "log", "search", "quit"]

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

        special_cmds = game.get_special_commands()
        for sc in special_cmds:
            print("-", sc)

        choice = input("\nEnter action: ").lower().strip()
        while choice not in location.available_commands and choice not in menu and choice not in special_cmds:
            print("Invalid option.")
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
                if location.items:
                    print(f"\nYou found: {', '.join([i.name for i in location.items])}!\n")
                    game.update_inventory(location.items)
                else:
                    print("\nYou turned up empty handed!\n")
            elif choice == "look":
                print(location.long_description)
            elif choice == "score":
                print("Score:", game.score)

        elif choice in special_cmds:
            if choice.startswith("talk "):
                game.run_talk(choice.replace("talk ", ""))
            else:
                game.run_interaction(choice)

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

            if game.movement_timer < 0:
                game.movement_timer = 0

            game.moves_made += 1
            game.apply_rules()

        resulting_loc = game.get_location()
        game_log.add_event(Event(resulting_loc.id_num,
                                 resulting_loc.long_description),
                           choice)
