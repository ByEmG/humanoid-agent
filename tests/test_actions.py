import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from world.grid import GridWorld
from world.objects import Direction, CellType, Door, Key
from agent.actions import ActionType, execute_action, get_valid_actions


def make_world():
    return GridWorld(width=10, height=10, seed=1)


def test_move_forward_action():
    w = make_world()
    w.agent_pos = (5, 5)
    w.agent_dir = Direction.SOUTH
    result = execute_action(w, ActionType.MOVE_FORWARD)
    assert result.success
    assert w.agent_pos == (5, 6)


def test_turn_left_action():
    w = make_world()
    w.agent_dir = Direction.NORTH
    result = execute_action(w, ActionType.TURN_LEFT)
    assert result.success
    assert w.agent_dir == Direction.WEST


def test_turn_right_action():
    w = make_world()
    w.agent_dir = Direction.NORTH
    result = execute_action(w, ActionType.TURN_RIGHT)
    assert result.success
    assert w.agent_dir == Direction.EAST


def test_pick_up_action():
    w = make_world()
    w.agent_pos = (4, 4)
    w.keys.append(Key(position=(4, 4), key_id="key_1"))
    w.set_cell(4, 4, CellType.KEY)
    result = execute_action(w, ActionType.PICK_UP)
    assert result.success
    assert "key_1" in w.inventory


def test_pick_up_empty_fails():
    w = make_world()
    w.agent_pos = (5, 5)
    result = execute_action(w, ActionType.PICK_UP)
    assert not result.success


def test_use_key_action():
    w = make_world()
    w.agent_pos = (5, 5)
    w.agent_dir = Direction.EAST
    w.inventory = ["key_1"]
    door = Door(position=(6, 5), is_open=False, key_id="key_1")
    w.doors.append(door)
    w.set_cell(6, 5, CellType.DOOR)
    result = execute_action(w, ActionType.USE_KEY)
    assert result.success
    assert door.is_open


def test_wait_action():
    w = make_world()
    steps_before = w.steps
    result = execute_action(w, ActionType.WAIT)
    assert result.success
    assert w.steps == steps_before + 1


def test_describe_action():
    w = make_world()
    result = execute_action(w, ActionType.DESCRIBE)
    assert result.success


def test_action_from_string():
    assert ActionType.from_string("MOVE_FORWARD") == ActionType.MOVE_FORWARD
    assert ActionType.from_string("move_forward") == ActionType.MOVE_FORWARD
    assert ActionType.from_string("MOVE") == ActionType.MOVE_FORWARD
    assert ActionType.from_string("LEFT") == ActionType.TURN_LEFT


def test_action_from_string_invalid():
    with pytest.raises(ValueError):
        ActionType.from_string("JUMP")


def test_get_valid_actions_includes_always_present():
    w = make_world()
    valid = get_valid_actions(w)
    assert ActionType.WAIT in valid
    assert ActionType.TURN_LEFT in valid
    assert ActionType.TURN_RIGHT in valid


def test_move_forward_only_when_passable():
    w = make_world()
    w.agent_pos = (1, 1)
    w.agent_dir = Direction.NORTH  # wall at (1,0)
    valid = get_valid_actions(w)
    assert ActionType.MOVE_FORWARD not in valid

    w.agent_dir = Direction.SOUTH  # (1,2) is empty
    valid = get_valid_actions(w)
    assert ActionType.MOVE_FORWARD in valid


def test_pick_up_only_when_key_present():
    w = make_world()
    w.agent_pos = (5, 5)
    valid = get_valid_actions(w)
    assert ActionType.PICK_UP not in valid

    w.keys.append(Key(position=(5, 5), key_id="key_1"))
    w.set_cell(5, 5, CellType.KEY)
    valid = get_valid_actions(w)
    assert ActionType.PICK_UP in valid
