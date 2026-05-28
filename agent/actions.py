from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.grid import GridWorld
from world.objects import WorldState


class ActionType(Enum):
    MOVE_FORWARD = "MOVE_FORWARD"
    TURN_LEFT    = "TURN_LEFT"
    TURN_RIGHT   = "TURN_RIGHT"
    PICK_UP      = "PICK_UP"
    USE_KEY      = "USE_KEY"
    WAIT         = "WAIT"
    DESCRIBE     = "DESCRIBE"

    @classmethod
    def from_string(cls, s: str) -> "ActionType":
        s = s.strip().upper()
        # Accept aliases
        aliases = {
            "MOVE": ActionType.MOVE_FORWARD,
            "FORWARD": ActionType.MOVE_FORWARD,
            "LEFT": ActionType.TURN_LEFT,
            "RIGHT": ActionType.TURN_RIGHT,
            "PICKUP": ActionType.PICK_UP,
            "PICK": ActionType.PICK_UP,
            "USE": ActionType.USE_KEY,
            "KEY": ActionType.USE_KEY,
        }
        try:
            return cls(s)
        except ValueError:
            if s in aliases:
                return aliases[s]
            raise ValueError(f"Unknown action: {s!r}")


@dataclass
class ActionResult:
    success: bool
    message: str
    action: ActionType
    description: str = ""  # populated by DESCRIBE action


def execute_action(world: "GridWorld", action: ActionType) -> ActionResult:
    """Dispatch an action against the live GridWorld and return result."""

    if action == ActionType.MOVE_FORWARD:
        ok, msg = world.move_agent()
        return ActionResult(ok, msg, action)

    if action == ActionType.TURN_LEFT:
        ok, msg = world.turn_left()
        return ActionResult(ok, msg, action)

    if action == ActionType.TURN_RIGHT:
        ok, msg = world.turn_right()
        return ActionResult(ok, msg, action)

    if action == ActionType.PICK_UP:
        ok, msg = world.pick_up()
        return ActionResult(ok, msg, action)

    if action == ActionType.USE_KEY:
        ok, msg = world.use_key()
        return ActionResult(ok, msg, action)

    if action == ActionType.WAIT:
        world.steps += 1
        return ActionResult(True, "Agent waited", action)

    if action == ActionType.DESCRIBE:
        world.steps += 1
        return ActionResult(True, "Agent described surroundings", action)

    return ActionResult(False, f"Unknown action: {action}", action)


def get_valid_actions(world: "GridWorld") -> list[ActionType]:
    """Return actions that make sense right now (always includes WAIT, DESCRIBE)."""
    valid = [ActionType.WAIT, ActionType.DESCRIBE, ActionType.TURN_LEFT, ActionType.TURN_RIGHT]

    dx, dy = world.agent_dir.delta()
    nx, ny = world.agent_pos[0] + dx, world.agent_pos[1] + dy
    if world.is_valid_position(nx, ny):
        valid.append(ActionType.MOVE_FORWARD)

    x, y = world.agent_pos
    if world.get_key_at(x, y):
        valid.append(ActionType.PICK_UP)

    if world.inventory:
        # Check adjacent doors
        for ddx, ddy in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
            door = world.get_door_at(x + ddx, y + ddy)
            if door and not door.is_open:
                valid.append(ActionType.USE_KEY)
                break

    return valid
