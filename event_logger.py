"""CSC111 Project 1: Text Adventure Game - Event Logger

Instructions (READ THIS FIRST!)
===============================

This Python module contains the code for Project 1. Please consult
the project handout for instructions and details.

You can copy/paste your code from Assignment 1 into this file, and modify it as
needed to work with your game.

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
from dataclasses import dataclass
from typing import Optional


# Note: We have completed the Event class for you. Do NOT modify it here for A1.
@dataclass
class Event:
    """
    A node representing one event in an adventure game.

    Instance Attributes:
    - id_num: Integer id of this event's location
    - description: Long description of this event's location
    - next_command: String command which leads this event to the next event, None if this is the last game event
    - next: Event object representing the next event in the game, or None if this is the last game event
    - prev: Event object representing the previous event in the game, None if this is the first game event
    """
    id_num: int
    description: str
    next_command: Optional[str] = None
    next: Optional[Event] = None
    prev: Optional[Event] = None


class EventList:
    """
    A linked list of game events.

    Instance Attributes:
        - first: the first event in a series of game events, or None if the list is empty
        - last: the last (most recent) event in the series of game events, or None if the list is empty

    Representation Invariants:
        - self.first.prev = None
        - self.last.next = None
    """
    first: Optional[Event]
    last: Optional[Event]

    # Note: You may ADD parameters/attributes/methods to this class as you see fit.
    # But do not rename or remove any existing methods/attributes in this class

    def __init__(self) -> None:
        """Initialize a new empty event list."""

        self.first = None
        self.last = None

    def display_events(self) -> None:
        """Display all events in chronological order."""

        curr = self.first
        while curr:
            print(f"Location: {curr.id_num}, Command: {curr.next_command}")
            curr = curr.next

    def is_empty(self) -> bool:
        """Return whether this event list is empty."""
        return self.first is None and self.last is None

    def add_event(self, event: Event, command: str = None) -> None:
        """
        Add the given new event to the end of this event list.
        The given command is the command which was used to reach this new event, or None if this is the first
        event in the game.
        """
        # Hint: You should update the previous node's <next_command> as needed

        if self.is_empty():
            self.first = event          # there's only 1 event
            self.last = event
        else:
            self.last.next = event                  # add the new event to the last event
            self.last.next_command = command        # add the new command to the last event
            event.prev = self.last                  # make previous event to the new last event be the former last event
            self.last = event                       # make the new last event be the newly added event

    def remove_last_event(self) -> None:
        """
        Remove the last event from this event list.
        If the list is empty, do nothing.
        """
        # Hint: The <next_command> and <next> attributes for the new last event should be updated as needed

        if not self.is_empty():
            if self.first == self.last:     # there's only 1 element
                self.first = None
                self.last = None
            else:
                self.last = self.last.prev      # set the new last event as the previous event to the former last event
                self.last.next = None           # make the event after the last event be None
                self.last.next_command = None   # make the command at last event also be None cuz there is no next event

    def get_id_log(self) -> list[int]:
        """Return a list of all location IDs visited for each event in this list, in sequence."""

        ids = []
        curr = self.first

        while curr is not None:
            ids.append(curr.id_num)
            curr = curr.next

        return ids

    def get_last(self) -> Event:
        """Return the last event"""

        return self.last


if __name__ == '__main__':
    # pass
    # When you are ready to check your work with python_ta, uncomment the following lines.
    # (Delete the "#" and space before each line.)
    # IMPORTANT: keep this code indented inside the "if __name__ == '__main__'" block
    import python_ta
    python_ta.check_all(config={
        'max-line-length': 120,
        'allowed-io': ['EventList.display_events'],
        'disable': ['R1705', 'static_type_checker']
    })
# })
