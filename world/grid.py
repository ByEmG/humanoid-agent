from __future__ import annotations
import random
from typing import Optional
from world.objects import CellType, Direction, Door, Key, WorldState


class GridWorld:
    def __init__(self, width: int = 10, height: int = 10, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed
        self.rng = random.Random(seed)
        self.reset()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self) -> None:
        self._grid: list[list[CellType]] = [
            [CellType.EMPTY] * self.width for _ in range(self.height)
        ]
        self.agent_pos: tuple[int, int] = (1, 1)
        self.agent_dir: Direction = Direction.NORTH
        self.doors: list[Door] = []
        self.keys: list[Key] = []
        self.inventory: list[str] = []
        self.steps: int = 0
        self.goal_pos: Optional[tuple[int, int]] = None
        self.visited_cells: set[tuple[int, int]] = {(1, 1)}
        self._place_border_walls()

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def get_state(self) -> WorldState:
        return WorldState(
            agent_pos=self.agent_pos,
            agent_dir=self.agent_dir,
            grid=[row[:] for row in self._grid],
            doors=[d.copy() for d in self.doors],
            keys=[k.copy() for k in self.keys],
            inventory=list(self.inventory),
            steps=self.steps,
            goal_pos=self.goal_pos,
            width=self.width,
            height=self.height,
            visited_cells=set(self.visited_cells),
        )

    # ------------------------------------------------------------------
    # Validity
    # ------------------------------------------------------------------

    def is_valid_position(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        cell = self._grid[y][x]
        if cell in (CellType.WALL, CellType.OBSTACLE):
            return False
        for door in self.doors:
            if door.position == (x, y) and not door.is_open:
                return False
        return True

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def get_cell(self, x: int, y: int) -> CellType:
        return self._grid[y][x]

    def set_cell(self, x: int, y: int, cell_type: CellType) -> None:
        self._grid[y][x] = cell_type

    # ------------------------------------------------------------------
    # Placement helpers
    # ------------------------------------------------------------------

    def place_objects(self, cell_type: CellType, position: tuple[int, int]) -> None:
        x, y = position
        self._grid[y][x] = cell_type

    def get_empty_positions(self, exclude: Optional[list] = None) -> list[tuple[int, int]]:
        exclude_set = set(map(tuple, exclude or []))
        positions = []
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                pos = (x, y)
                if self._grid[y][x] == CellType.EMPTY and pos not in exclude_set:
                    positions.append(pos)
        return positions

    def random_empty_position(self, exclude: Optional[list] = None) -> tuple[int, int]:
        positions = self.get_empty_positions(exclude)
        if not positions:
            raise ValueError("No empty positions available")
        return self.rng.choice(positions)

    def _place_border_walls(self) -> None:
        for x in range(self.width):
            self._grid[0][x] = CellType.WALL
            self._grid[self.height - 1][x] = CellType.WALL
        for y in range(self.height):
            self._grid[y][0] = CellType.WALL
            self._grid[y][self.width - 1] = CellType.WALL

    # ------------------------------------------------------------------
    # Door / key helpers
    # ------------------------------------------------------------------

    def get_door_at(self, x: int, y: int) -> Optional[Door]:
        for door in self.doors:
            if door.position == (x, y):
                return door
        return None

    def get_key_at(self, x: int, y: int) -> Optional[Key]:
        for key in self.keys:
            if key.position == (x, y) and not key.collected:
                return key
        return None

    def has_key_in_inventory(self, key_id: str = "key_1") -> bool:
        return key_id in self.inventory

    # ------------------------------------------------------------------
    # Agent movement
    # ------------------------------------------------------------------

    def move_agent(self) -> tuple[bool, str]:
        dx, dy = self.agent_dir.delta()
        nx, ny = self.agent_pos[0] + dx, self.agent_pos[1] + dy
        if not self.is_valid_position(nx, ny):
            return False, f"Cannot move {self.agent_dir.value}: blocked"
        self.agent_pos = (nx, ny)
        self.visited_cells.add(self.agent_pos)
        self.steps += 1
        return True, f"Moved {self.agent_dir.value} to {self.agent_pos}"

    def turn_left(self) -> tuple[bool, str]:
        self.agent_dir = self.agent_dir.turn_left()
        self.steps += 1
        return True, f"Turned left, now facing {self.agent_dir.value}"

    def turn_right(self) -> tuple[bool, str]:
        self.agent_dir = self.agent_dir.turn_right()
        self.steps += 1
        return True, f"Turned right, now facing {self.agent_dir.value}"

    def pick_up(self) -> tuple[bool, str]:
        x, y = self.agent_pos
        key = self.get_key_at(x, y)
        if key:
            key.collected = True
            self.inventory.append(key.key_id)
            self._grid[y][x] = CellType.EMPTY
            self.steps += 1
            return True, f"Picked up {key.key_id}"
        return False, "Nothing to pick up here"

    def use_key(self) -> tuple[bool, str]:
        dx, dy = self.agent_dir.delta()
        nx, ny = self.agent_pos[0] + dx, self.agent_pos[1] + dy
        door = self.get_door_at(nx, ny)
        if not door:
            # Also check all adjacent cells
            for ddx, ddy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
                ax, ay = self.agent_pos[0] + ddx, self.agent_pos[1] + ddy
                door = self.get_door_at(ax, ay)
                if door:
                    break
        if not door:
            return False, "No door adjacent to use key on"
        if door.is_open:
            return False, "Door is already open"
        if not self.has_key_in_inventory(door.key_id):
            return False, f"You don't have the required key ({door.key_id})"
        door.is_open = True
        dx2, dy2 = door.position
        self._grid[dy2][dx2] = CellType.EMPTY
        self.steps += 1
        return True, f"Used key to open door at {door.position}"
