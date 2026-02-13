from __future__ import annotations

import json
import random
from typing import Any, Callable, Optional

from event_logger import Event, EventList
from game_entities import Item, Location


class AdventureGame:
    """Adventure game engine.

    Game world content (locations, items, rules, NPCs, interactions, and optionally
    gameplay settings) is loaded from an external JSON file.
    """

    _locations: dict[int, Location]
    _items: dict[str, Item]

    # data-driven systems from JSON
    flags: dict[str, bool]
    rules: list[dict[str, Any]]
    npcs: list[dict[str, Any]]
    interactions: list[dict[str, Any]]
    settings: dict[str, Any]

    # runtime state
    current_location_id: int
    ongoing: bool
    inventory: dict[str, list[Any]]  # {lower_item_name: [Item, count]}
    score: int
    moves_made: int

    # gameplay meters
    movement_timer: int
    health_bar: int
    hungry: bool

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        (self._locations,
         self._items,
         self.flags,
         self.rules,
         self.npcs,
         self.interactions,
         self.settings) = self._load_game_data(game_data_file)

        self.current_location_id = initial_location_id
        self.ongoing = True

        self.inventory = {}
        self.score = 0
        self.moves_made = 0

        # Gameplay defaults are configurable via JSON under top-level key "settings".
        # If omitted, the defaults below keep the game runnable.
        self.movement_timer = int(self.settings.get("movement_timer_start", 120))
        self.health_bar = int(self.settings.get("health_bar_start", 5))
        self.hungry = bool(self.settings.get("hungry_start", False))

    # -------------------------------------------------------------------------
    # Loading
    # -------------------------------------------------------------------------
    @staticmethod
    def _load_game_data(filename: str):
        with open(filename, "r") as f:
            data = json.load(f)

        items: dict[str, Item] = {}
        for item_data in data["items"]:
            item = Item(
                item_data["name"],
                item_data["description"],
                item_data["start_position"],
                item_data["target_position"],
                item_data["target_points"],
            )
            items[item_data["name"]] = item

        locations: dict[int, Location] = {}
        for loc_data in data["locations"]:
            loc = Location(
                loc_data["name"],
                loc_data["id"],
                loc_data["brief_description"],
                loc_data["long_description"],
                loc_data["available_commands"],
                [items[i] for i in loc_data["items"]],
            )
            locations[loc_data["id"]] = loc

        return (
            locations,
            items,
            data.get("initial_flags", {}),
            data.get("rules", []),
            data.get("npcs", []),
            data.get("interactions", []),
            data.get("settings", {}),
        )

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        """Return the Location with id loc_id, or the current location if loc_id is None."""
        if loc_id is None:
            loc_id = self.current_location_id
        return self._locations[loc_id]

    # -------------------------------------------------------------------------
    # Inventory
    # -------------------------------------------------------------------------
    def update_inventory(self, loc_items: list[Item]) -> None:
        """Move all items from the current location into the player's inventory."""
        for item in loc_items:
            key = item.name.lower()
            if key in self.inventory:
                self.inventory[key][1] += 1
            else:
                self.inventory[key] = [item, 1]
        loc_items.clear()


    def _add_item_to_inventory(self, item_name: str, count: int = 1) -> None:
        """Add count copies of the named item to the player's inventory."""
        item = self._items[item_name]
        key = item.name.lower()
        if key in self.inventory:
            self.inventory[key][1] += count
        else:
            self.inventory[key] = [item, count]

    def manage_inventory(self, current_location: Location) -> None:
        """Interactively manage inventory (currently supports dropping items)."""
        if not self.inventory:
            print("Your inventory is empty!")
            return

        while True:
            print("\n--- Inventory ---")
            for _, (item, count) in self.inventory.items():
                print(f"{item.name} (x{count})")
            print("-----------------")
            target = input("Select item to manage (or 'exit'): ").lower().strip()

            if target == "exit":
                return

            if target not in self.inventory:
                print("Item not found.")
                continue

            item_obj, count = self.inventory[target]
            action = input("Action [drop, exit]: ").lower().strip()

            if action == "exit":
                continue
            if action != "drop":
                print("Invalid action.")
                continue

            current_location.items.append(item_obj)
            count -= 1
            print(f"Dropped {item_obj.name}.")

            if count <= 0:
                del self.inventory[target]
            else:
                self.inventory[target][1] = count


    # -------------------------------------------------------------------------
    # Flags, requirements, rules, effects
    # -------------------------------------------------------------------------
    def requirements_met(self, requires: dict[str, Any]) -> bool:
        """Return True iff all requirements are satisfied (currently only flags)."""
        if not requires:
            return True

        for flag, expected in requires.get("flags", {}).items():
            if self.flags.get(flag) != expected:
                return False

        return True

    def apply_effects(self, effects: list[dict[str, Any]]) -> None:
        """Apply a list of effects (data-driven from JSON)."""
        handlers: dict[str, Callable[[dict[str, Any]], None]] = {
            "print": lambda eff: print(eff["message"]),
            "set_flag": lambda eff: self.flags.__setitem__(eff["flag"], eff["value"]),
            "spawn_item_here": lambda eff: self.get_location().items.append(self._items[eff["item"]]),
            "add_item_to_inventory": lambda eff: self._add_item_to_inventory(eff["item"], int(eff.get("count", 1))),
        }

        for eff in effects:
            eff_type = eff.get("type")
            if eff_type in handlers:
                handlers[eff_type](eff)

    def apply_rules(self) -> None:
        """Evaluate and apply all global rules (data-driven from JSON)."""
        for rule in self.rules:
            when = rule.get("when", {})
            if self.moves_made < when.get("moves_at_least", 0):
                continue
            if not self.requirements_met(when):
                continue
            self.apply_effects(rule.get("then", []))

    # -------------------------------------------------------------------------
    # Special commands: NPC talk + interactions
    # -------------------------------------------------------------------------
    def get_special_commands(self) -> list[str]:
        """Return special commands available at the current location."""
        cmds: list[str] = []

        loc_id = self.current_location_id
        cmds.extend([f"talk {npc['name']}" for npc in self.npcs if npc.get("location") == loc_id])

        for inter in self.interactions:
            if loc_id in inter.get("locations", []) and self.requirements_met(inter.get("requires", {})):
                cmds.append(inter["command"])

        return cmds

    def run_talk(self, name: str) -> None:
        """Run dialogue for an NPC at the current location (first matching line wins)."""
        for npc in self.npcs:
            if npc.get("location") != self.current_location_id or npc.get("name") != name:
                continue

            for line in npc.get("dialogue", []):
                if self.requirements_met(line.get("requires", {})):
                    print(line.get("say", ""))
                    self.apply_effects(line.get("effects", []))
                    return

            break  # NPC exists here but no valid line
        print("No one by that name is here.")

    def run_interaction(self, command: str) -> None:
        """Run a location interaction command, if present."""
        for inter in self.interactions:
            if (self.current_location_id in inter.get("locations", [])
                    and inter.get("command") == command):
                if self.requirements_met(inter.get("requires", {})):
                    self.apply_effects(inter.get("effects", []))
                else:
                    print("You can't do that yet.")
                return

    # -------------------------------------------------------------------------
    # Movement / time
    # -------------------------------------------------------------------------
    def _decrement_timer(self) -> None:
        """Apply one movement's time/health cost using settings-driven ranges."""
        ranges = self.settings.get("movement_costs", {})
        if self.hungry:
            low, high = ranges.get("hungry_timer_range", [10, 16])
        else:
            low, high = ranges.get("timer_range", [5, 8])

        self.movement_timer = max(0, self.movement_timer - random.randint(int(low), int(high)))

        self.health_bar -= int(ranges.get("health_per_move", 1))
        if self.health_bar <= 0:
            self.hungry = True

    def move(self, command: str) -> None:
        """Move to a new location using a command that exists in current location."""
        location = self.get_location()
        self.current_location_id = location.available_commands[command]

        self._decrement_timer()
        self.moves_made += 1
        self.apply_rules()


if __name__ == "__main__":
    game_log = EventList()
    game = AdventureGame("game_data.json", 0)

    # Menu is data-driven if provided; otherwise use the default below.
    menu: list[str] = list(game.settings.get(
        "menu",
        ["look", "inventory", "score", "log", "search", "quit"],
    ))

    start_loc = game.get_location()
    game_log.add_event(Event(start_loc.id_num, start_loc.long_description))

    menu_handlers: dict[str, Callable[[Location], None]] = {
        "log": lambda _: game_log.display_events(),
        "quit": lambda _: setattr(game, "ongoing", False),
        "inventory": lambda loc: game.manage_inventory(loc),
        "search": lambda loc: (
            (print(f"\nYou found: {', '.join([i.name for i in loc.items])}!\n"), game.update_inventory(loc.items))
            if loc.items else print("\nYou turned up empty handed!\n")
        ),
        "look": lambda loc: print(loc.long_description),
        "score": lambda _: print("Score:", game.score),
    }

    while game.ongoing:
        location = game.get_location()

        print("Location:", location.name)
        print(location.brief_description if location.visited else location.long_description)
        location.visited = True

        special_cmds = game.get_special_commands()
        all_actions = list(menu) + list(location.available_commands) + special_cmds

        print(f"What to do? Choose from: {', '.join(menu)}")
        print("At this location, you can also:")
        for action in list(location.available_commands) + special_cmds:
            print("-", action)

        choice = input("\nEnter action: ").lower().strip()
        while choice not in all_actions:
            print("Invalid option.")
            choice = input("\nEnter action: ").lower().strip()

        print("========")
        print("You decided to:", choice)

        if choice in menu_handlers:
            menu_handlers[choice](location)
        elif choice.startswith("talk "):
            game.run_talk(choice.replace("talk ", "", 1))
        elif choice in special_cmds:
            game.run_interaction(choice)
        else:
            game.move(choice)

        resulting_loc = game.get_location()
        game_log.add_event(Event(resulting_loc.id_num, resulting_loc.long_description), choice)


