from __future__ import annotations

import json
import random
from typing import Any, Optional

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
        """Initialize the game state and load world data from a JSON file.

        Loads locations, items, flags, rules, NPCs, interactions, and settings from the
        game data file and then initializes runtime state (current location,
        inventory, score, timers/health, etc.).

        Parameters:
            game_data_file: Path to the JSON file containing game world data.
            initial_location_id: The starting location ID for the player.
        """

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

        self.health_bar = int(self.settings.get("health_bar_start", 10))
        self.movement_timer = int(self.settings.get("movement_timer_start", 120))

        self.energized = False

        self.hungry = bool(self.settings.get("hungry_start", False))


    @staticmethod
    def _load_game_data(filename: str):
        """Load game content from a JSON file and build location/item objects.

        The JSON is expected to define:
        - "items": list of item definitions used to construct Item objects
        - "locations": list of location definitions used to construct Location objects

        Other keys include:
        - "initial_flags", "rules", "npcs", "interactions", "settings"

        Parameters:
            filename: Path to a JSON file containing game data.

        Returns:
            This is a tuple containing:
                - locations: dict mapping location IDs to Location objects
                - items: dict mapping item names to Item objects
                - initial_flags: dict of starting boolean flags
                - rules: list of global rule dictionaries
                - npcs: list of NPC dictionaries
                - interactions: list of interaction dictionaries
                - settings: dict of gameplay/settings values
        """

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
                item_data.get("edible", False),
                item_data.get("restore_value", 0),
                item_data.get("special_effect")
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

    def update_inventory(self, loc_items: list[Item]) -> None:
        """
        Transfer all items from a location into the player's inventory.

        For each item:
        - Add the item's target points to the player's score.
        - Increase the item's count in the inventory (keyed by lowercase name),
          creating a new entry if needed.
        - Clear the provided location item list after transferring.

        Parameters:
            loc_items: The list of items currently at the location (mutated/cleared).
        """
        for item in loc_items:
            key = item.name.lower()
            self.score += item.target_points
            print(f"Points gained: {item.target_points}")

            if key in self.inventory:
                self.inventory[key][1] += 1
            else:
                self.inventory[key] = [item, 1]
        loc_items.clear()

    def add_item_to_inventory(self, item_name: str, count: int = 1) -> None:
        """
        Add an item to the player's inventory by name.

        Looking up the Item object from the game's item registry, and then add its target points
        to the score, and increments the inventory count for that item (creating a new
        entry if necessary).

        Parameters:
            item_name: The exact name of the item to add (as stored in the item registry).
            count: Number of copies to add (default is 1).
        """
        item = self._items[item_name]

        self.score += item.target_points

        key = item.name.lower()
        if key in self.inventory:
            self.inventory[key][1] += count
        else:
            self.inventory[key] = [item, count]

    def manage_inventory(self, current_location: Location) -> None:
        """Interactively manage inventory (drop or eat items)."""
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

            options = ["drop", "exit"]
            if item_obj.edible:
                options.append("eat")

            prompt = f"Action [{', '.join(options)}]: "
            action = input(prompt).lower().strip()

            if action == "exit":
                continue

            if action == "drop":
                current_location.items.append(item_obj)
                count -= 1
                print(f"Dropped {item_obj.name}.")

            elif action == "eat" and item_obj.edible:
                print(f"You consume the {item_obj.name}.")

                if item_obj.restore_value > 0:
                    self.health_bar += item_obj.restore_value
                    self.energized = False
                    print(f"Hunger satiated! Health is now {self.health_bar}.")

                if item_obj.special_effect == "energize":
                    self.energized = True
                    print("You feel a surge of caffeine! You are now ENERGIZED (Double Speed).")
                count -= 1
            else:
                print("Invalid action.")
                continue

            if count <= 0:
                del self.inventory[target]
            else:
                self.inventory[target][1] = count
    def consume_item(self, item_name: str) -> None:
        """Eat an item to restore health (hunger) or gain status effects."""
        target_key = item_name.lower()
        if target_key not in self.inventory:
            print("You don't have that item.")
            return

        item_obj, count = self.inventory[target_key]

        if not item_obj.edible:
            print(f"You can't eat the {item_obj.name}!")
            return

        print(f"You consume the {item_obj.name}.")

        if item_obj.restore_value > 0:
            self.health_bar += item_obj.restore_value
            self.energized = False  # Eating food cancels the energy drink rush (optional balancing)
            print(f"Hunger satiated! Health is now {self.health_bar}.")

        if item_obj.special_effect == "energize":
            self.energized = True
            print("You feel a surge of caffeine! You are now ENERGIZED (Double Speed).")

        self.inventory[target_key][1] -= 1
        if self.inventory[target_key][1] <= 0:
            del self.inventory[target_key]

    def requirements_met(self, requires: dict[str, Any]) -> bool:
        """Return True iff all requirements are satisfied (currently only flags)."""
        if not requires:
            return True

        for flag, expected in requires.get("flags", {}).items():
            if self.flags.get(flag) != expected:
                return False

        return True

    def apply_effects(self, effects: list[dict[str, Any]]) -> None:
        """
        Apply a sequence of effects defined by rules/interactions/NPC dialogue.

        Effects are data driven dictionaries (loaded from JSON). Effect
        types include:
        - "print": print a message
        - "set_flag": set a boolean flag
        - "spawn_item_here": place an item in the current location
        - "add_item_to_inventory": add an item directly to inventory

        Parameters:
            effects: List of effect dictionaries to apply in order.
        """
        for effect in effects:
            effect_type = effect.get("type")

            if effect_type == "print":
                print(effect["message"])

            elif effect_type == "set_flag":
                self.flags[effect["flag"]] = effect["value"]

            elif effect_type == "spawn_item_here":
                item_obj = self._items[effect["item"]]
                self.get_location().items.append(item_obj)

            elif effect_type == "add_item_to_inventory":
                count = int(effect.get("count", 1))
                self.add_item_to_inventory(effect["item"], count)

    def apply_rules(self) -> None:
        """Evaluate and apply all global rules (data-driven from JSON)."""
        for rule in self.rules:
            when = rule.get("when", {})
            if self.moves_made < when.get("moves_at_least", 0):
                continue
            if not self.requirements_met(when):
                continue
            self.apply_effects(rule.get("then", []))

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

    def _decrement_timer(self) -> None:
        """Decrement the movement timer and health based on status and settings.

        Time cost per move is randomized within the configured "movement_costs"
        timer_range, then modified by status:
        - Energized: halves time cost
        - Starving (health_bar <= 0): doubles time cost
        - Otherwise: base cost

        Then, if the health_bar  <= 0, these conditions are rendered true:
        - Reduces movement_timer (clamped at 0)
        - Reduces health_bar by 1 each move
        - Prints status readouts

        This condition would work if this condition (time running out) is satisfied, irrespective of the fact
        whether the character is hungry or not:
        - Ends the game if time runs out
        """
        ranges = self.settings.get("movement_costs", {})
        low, high = ranges.get("timer_range", [5, 8])
        base_cost = random.randint(int(low), int(high))

        if self.energized:
            time_cost = base_cost // 2
            status_msg = " (Energized!)"
        elif self.health_bar <= 0:
            time_cost = base_cost * 2
            status_msg = " (Starving... moving slowly)"
        else:
            time_cost = base_cost
            status_msg = ""

        self.movement_timer = max(0, self.movement_timer - time_cost)
        self.health_bar -= 1

        print("-" * 40)
        print(f"Time Passed: {time_cost} mins{status_msg}")
        print(f"Time Remaining: {self.movement_timer} minutes until deadline.")
        print(f"Hunger Level: {max(0, self.health_bar)}/5")
        if self.energized:
            print("STATUS: ENERGIZED (Speed x2)")
        elif self.health_bar <= 0:
            print("STATUS: HUNGRY (Speed x0.5)")
        print("-" * 40)

        if self.movement_timer <= 0:
            print("\nIt is 1:00 PM. You missed the deadline! Now you surely won't make POST... Your life, and your friendship is over!")
            print("GAME OVER.")
            self.ongoing = False
            return

        if self.health_bar <= 0 and not self.energized:
            print("Your stomach grumbles loudly. You need calories!")

    def move(self, command: str) -> None:
        """Move to a new location using a command that exists in current location."""
        location = self.get_location()
        self.current_location_id = location.available_commands[command]

        self._decrement_timer()
        self.moves_made += 1
        self.apply_rules()

    def search_location(self) -> None:
        """Search the current location for items."""
        location = self.get_location()
        if location.items:
            found_names = ", ".join([item.name for item in location.items])
            print(f"\nYou found: {found_names}!\n")

            self.update_inventory(location.items)
        else:
            print("\nYou turned up empty handed!\n")

    def check_win(self) -> None:
        """
        Check whether the player has met the victory condition and finish the game.

        Winning condition:
        - Player is at location ID 0
        - Player has all required items in inventory

        On win:
        - Print the win narrative
        - Add remaining time as a score bonus
        - Mark the game as no longer ongoing
        """
        if self.current_location_id == 0:
            required_items = ["lucky mug", "usb drive", "laptop charger"]
            has_all = True
            for req in required_items:
                if req not in self.inventory:
                    has_all = False
                    break

            if has_all:
                print("\nYou burst into your dorm room with moments to spare!")
                print("You plug in your laptop, drink some coffee, and submit the project!")

                time_bonus = self.movement_timer
                self.score += time_bonus
                print(f"Time Bonus: {time_bonus}")
                print(f"Final Score: {self.score}")
                print("YOU WIN!")
                self.ongoing = False


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

    while game.ongoing:
        print(f"energized? {game.energized}")
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

        if choice == "log":
            game_log.display_events()

        elif choice == "quit":
            game.ongoing = False

        elif choice == "inventory":
            game.manage_inventory(location)

        elif choice == "search":
            game.search_location()

        elif choice == "look":
            print(location.long_description)

        elif choice == "score":
            print(f"Score: {game.score}")

        elif choice.startswith("eat "):
            item_to_eat = choice.replace("eat ", "", 1).strip()
            game.consume_item(item_to_eat)

        elif choice.startswith("talk "):
            game.run_talk(choice.replace("talk ", "", 1))

        elif choice in special_cmds:
            game.run_interaction(choice)

        else:
            game.move(choice)

        game.check_win()

        resulting_loc = game.get_location()
        game_log.add_event(Event(resulting_loc.id_num, resulting_loc.long_description), choice)

