from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class CellType(Enum):
    EMPTY = "empty"
    WALL = "wall"
    AGENT = "agent"
    GOAL = "goal"
    KEY = "key"
    DOOR = "door"
    OBSTACLE = "obstacle"


class Direction(Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST = "E"
    WEST = "W"

    def turn_left(self) -> Direction:
        order = [Direction.NORTH, Direction.WEST, Direction.SOUTH, Direction.EAST]
        return order[(order.index(self) + 1) % 4]

    def turn_right(self) -> Direction:
        order = [Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST]
        return order[(order.index(self) + 1) % 4]

    def delta(self) -> tuple[int, int]:
        """Return (dx, dy); y increases downward (south)."""
        return {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0),
        }[self]

    def opposite(self) -> Direction:
        return {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST,
        }[self]


@dataclass
class Door:
    position: tuple[int, int]
    is_open: bool = False
    key_id: str = "key_1"

    def copy(self) -> Door:
        return Door(self.position, self.is_open, self.key_id)


@dataclass
class Key:
    position: tuple[int, int]
    collected: bool = False
    key_id: str = "key_1"

    def copy(self) -> Key:
        return Key(self.position, self.collected, self.key_id)


@dataclass
class WorldState:
    """Immutable snapshot of the world at one point in time."""
    agent_pos: tuple[int, int]
    agent_dir: Direction
    grid: list[list[CellType]]
    doors: list[Door]
    keys: list[Key]
    inventory: list[str]
    steps: int
    goal_pos: Optional[tuple[int, int]]
    width: int
    height: int
    visited_cells: set[tuple[int, int]] = field(default_factory=set)

    def cell_at(self, x: int, y: int) -> CellType:
        return self.grid[y][x]

    def get_accessible_cells(self) -> set[tuple[int, int]]:
        """Return all non-wall, non-obstacle cells."""
        accessible = set()
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] not in (CellType.WALL, CellType.OBSTACLE):
                    accessible.add((x, y))
        return accessible
