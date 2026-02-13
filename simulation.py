"""CSC111 Project 1: Text Adventure Game - Simulator"""
from __future__ import annotations

import json
from typing import Optional

from event_logger import Event, EventList
from game_entities import Location


class SimpleAdventureGame:
    """A simple text adventure game class storing all location data."""

    current_location_id: int
    _locations: dict[int, Location]

    def __init__(self, game_data_file: str, initial_location_id: int) -> None:
        self._locations = self._load_game_data(game_data_file)
        self.current_location_id = initial_location_id

    @staticmethod
    def _load_game_data(filename: str) -> dict[int, Location]:
        with open(filename, 'r') as f:
            data = json.load(f)

        locations: dict[int, Location] = {}
        for loc_data in data['locations']:
            location_obj = Location(
                loc_data['name'],
                loc_data['id'],
                loc_data['brief_description'],
                loc_data['long_description'],
                loc_data['available_commands'],
                []  # items not needed for the simulator
            )
            locations[loc_data['id']] = location_obj

        return locations

    def get_location(self, loc_id: Optional[int] = None) -> Location:
        if loc_id is None:
            return self._locations[self.current_location_id]
        return self._locations[loc_id]


class AdventureGameSimulation:
    """A simulation of an adventure game playthrough."""

    _game: SimpleAdventureGame
    _events: EventList

    def __init__(self, game_data_file: str, initial_location_id: int, commands: list[str]) -> None:
        self._events = EventList()
        self._game = SimpleAdventureGame(game_data_file, initial_location_id)

        start_loc = self._game.get_location(initial_location_id)
        self._events.add_event(Event(initial_location_id, start_loc.long_description))

        self.generate_events(commands, start_loc)

    def generate_events(self, commands: list[str], current_location: Location) -> None:
        for command in commands:
            next_loc_id = current_location.available_commands[command]
            next_loc_obj = self._game.get_location(next_loc_id)

            self._events.add_event(Event(next_loc_id, next_loc_obj.long_description), command)
            current_location = next_loc_obj

    def get_id_log(self) -> list[int]:
        return self._events.get_id_log()

    def run(self) -> None:
        current_event = self._events.first
        while current_event:
            print(current_event.description)
            if current_event is not self._events.last:
                print("You choose:", current_event.next_command)
            current_event = current_event.next


if __name__ == "__main__":
    # Fill these in with your winning/losing walkthroughs once your game is finalized.
    win_walkthrough = []
    expected_log = []
    # sim = AdventureGameSimulation('game_data.json', 0, win_walkthrough)
    # assert expected_log == sim.get_id_log()
