from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.grid import GridWorld
from world.objects import CellType, WorldState
from agent.actions import ActionType, get_valid_actions

_CELL_NAMES = {
    CellType.EMPTY:    "open space",
    CellType.WALL:     "wall",
    CellType.GOAL:     "GOAL (★)",
    CellType.KEY:      "KEY (🔑)",
    CellType.DOOR:     "DOOR (locked)",
    CellType.OBSTACLE: "obstacle",
    CellType.AGENT:    "your position",
}

_DIR_WORDS = {
    "N": "North",
    "S": "South",
    "E": "East",
    "W": "West",
}


def build_observation(
    world: "GridWorld",
    memory: list[str],
    goal_description: str,
) -> str:
    state = world.get_state()
    sections = [
        _section_position(state),
        _section_local_view(state),
        _section_inventory(state),
        _section_memory(memory),
        _section_goal(goal_description),
        _section_nearby_objects(state),
        _section_valid_actions(world),
    ]
    return "\n".join(sections)


# ------------------------------------------------------------------
# Section builders
# ------------------------------------------------------------------

def _section_position(state: WorldState) -> str:
    x, y = state.agent_pos
    d = _DIR_WORDS[state.agent_dir.value]
    dx, dy = state.agent_dir.delta()
    nx, ny = x + dx, y + dy
    cell_ahead = state.cell_at(nx, ny) if state.in_bounds_check(nx, ny, state) else None
    ahead_name = _CELL_NAMES.get(cell_ahead, "wall") if cell_ahead else "wall"
    return (
        "=== POSITION ===\n"
        f"You are at ({x}, {y}), facing {d}.\n"
        f"Directly ahead ({nx}, {ny}): {ahead_name}.\n"
        f"Steps taken so far: {state.steps}.\n"
    )


def _section_local_view(state: WorldState, radius: int = 2) -> str:
    ax, ay = state.agent_pos
    lines = ["=== LOCAL VIEW (5×5 centered on you) ==="]
    for dy in range(-radius, radius + 1):
        row = []
        for dx in range(-radius, radius + 1):
            x, y = ax + dx, ay + dy
            if dx == 0 and dy == 0:
                row.append("[YOU]")
            elif not (0 <= x < state.width and 0 <= y < state.height):
                row.append("[###]")  # out of bounds
            else:
                cell = state.grid[y][x]
                door_state = ""
                for d in state.doors:
                    if d.position == (x, y):
                        door_state = "(open)" if d.is_open else "(locked)"
                token = {
                    CellType.EMPTY:    " . ",
                    CellType.WALL:     "███",
                    CellType.GOAL:     " ★ ",
                    CellType.KEY:      " K ",
                    CellType.DOOR:     f"D{door_state}",
                    CellType.OBSTACLE: "▪▪▪",
                    CellType.AGENT:    "[A]",
                }.get(cell, " ? ")
                row.append(token)
        lines.append("  " + "  ".join(row))
    return "\n".join(lines) + "\n"


def _section_inventory(state: WorldState) -> str:
    if state.inventory:
        items = ", ".join(state.inventory)
        return f"=== INVENTORY ===\nCarrying: {items}\n"
    return "=== INVENTORY ===\nCarrying: nothing\n"


def _section_memory(memory: list[str]) -> str:
    if not memory:
        return "=== RECENT ACTIONS ===\nNo actions taken yet.\n"
    lines = ["=== RECENT ACTIONS (last 3) ==="]
    for entry in memory[-3:]:
        lines.append(f"  • {entry}")
    return "\n".join(lines) + "\n"


def _section_goal(goal_description: str) -> str:
    return f"=== CURRENT GOAL ===\n{goal_description}\n"


def _section_nearby_objects(state: WorldState, radius: int = 3) -> str:
    ax, ay = state.agent_pos
    found = []
    for y in range(max(0, ay - radius), min(state.height, ay + radius + 1)):
        for x in range(max(0, ax - radius), min(state.width, ax + radius + 1)):
            if (x, y) == (ax, ay):
                continue
            cell = state.grid[y][x]
            if cell in (CellType.EMPTY, CellType.WALL):
                continue
            dist = abs(x - ax) + abs(y - ay)
            door_info = ""
            for d in state.doors:
                if d.position == (x, y):
                    door_info = " [OPEN]" if d.is_open else " [LOCKED]"
            name = _CELL_NAMES.get(cell, str(cell))
            found.append(f"  {name}{door_info} at ({x},{y}), distance {dist}")

    if not found:
        return "=== NEARBY OBJECTS (within 3 cells) ===\nNothing notable nearby.\n"
    return "=== NEARBY OBJECTS (within 3 cells) ===\n" + "\n".join(found) + "\n"


def _section_valid_actions(world: "GridWorld") -> str:
    actions = get_valid_actions(world)
    names = [a.value for a in actions]
    return "=== VALID ACTIONS ===\n" + ", ".join(names) + "\n"


# Monkey-patch WorldState with a helper used above
def _in_bounds_check(self, x: int, y: int, state: "WorldState") -> bool:
    return 0 <= x < state.width and 0 <= y < state.height


WorldState.in_bounds_check = _in_bounds_check  # type: ignore
