import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from world.grid import GridWorld
from world.objects import CellType, Direction, Door, Key


def make_world(seed=0):
    return GridWorld(width=10, height=10, seed=seed)


# ------------------------------------------------------------------
# Border walls
# ------------------------------------------------------------------

def test_border_walls_placed():
    w = make_world()
    for x in range(10):
        assert w.get_cell(x, 0) == CellType.WALL
        assert w.get_cell(x, 9) == CellType.WALL
    for y in range(10):
        assert w.get_cell(0, y) == CellType.WALL
        assert w.get_cell(9, y) == CellType.WALL


def test_interior_cells_empty_after_reset():
    w = make_world()
    assert w.get_cell(5, 5) == CellType.EMPTY


# ------------------------------------------------------------------
# Valid positions
# ------------------------------------------------------------------

def test_wall_is_invalid():
    w = make_world()
    assert not w.is_valid_position(0, 0)


def test_interior_empty_is_valid():
    w = make_world()
    assert w.is_valid_position(5, 5)


def test_obstacle_is_invalid():
    w = make_world()
    w.set_cell(3, 3, CellType.OBSTACLE)
    assert not w.is_valid_position(3, 3)


def test_out_of_bounds_is_invalid():
    w = make_world()
    assert not w.is_valid_position(-1, 0)
    assert not w.is_valid_position(10, 10)


# ------------------------------------------------------------------
# Door blocking
# ------------------------------------------------------------------

def test_closed_door_blocks_movement():
    w = make_world()
    w.doors.append(Door(position=(5, 5), is_open=False))
    assert not w.is_valid_position(5, 5)


def test_open_door_allows_movement():
    w = make_world()
    w.doors.append(Door(position=(5, 5), is_open=True))
    assert w.is_valid_position(5, 5)


# ------------------------------------------------------------------
# Agent movement
# ------------------------------------------------------------------

def test_move_forward_north():
    w = make_world()
    w.agent_pos = (5, 5)
    w.agent_dir = Direction.NORTH
    ok, _ = w.move_agent()
    assert ok
    assert w.agent_pos == (5, 4)


def test_move_blocked_by_wall():
    w = make_world()
    w.agent_pos = (1, 1)
    w.agent_dir = Direction.NORTH
    ok, msg = w.move_agent()
    assert not ok  # wall at y=0


def test_turn_left():
    w = make_world()
    w.agent_dir = Direction.NORTH
    w.turn_left()
    assert w.agent_dir == Direction.WEST


def test_turn_right():
    w = make_world()
    w.agent_dir = Direction.NORTH
    w.turn_right()
    assert w.agent_dir == Direction.EAST


# ------------------------------------------------------------------
# Pick-up and key usage
# ------------------------------------------------------------------

def test_pick_up_key():
    w = make_world()
    w.agent_pos = (3, 3)
    w.keys.append(Key(position=(3, 3), key_id="k1"))
    w.set_cell(3, 3, CellType.KEY)
    ok, msg = w.pick_up()
    assert ok
    assert "k1" in w.inventory
    assert w.get_cell(3, 3) == CellType.EMPTY


def test_pick_up_nothing():
    w = make_world()
    w.agent_pos = (5, 5)
    ok, msg = w.pick_up()
    assert not ok


def test_use_key_opens_door():
    w = make_world()
    w.agent_pos = (5, 5)
    w.agent_dir = Direction.EAST
    w.inventory = ["key_1"]
    door = Door(position=(6, 5), is_open=False, key_id="key_1")
    w.doors.append(door)
    w.set_cell(6, 5, CellType.DOOR)
    ok, msg = w.use_key()
    assert ok
    assert door.is_open


def test_use_key_without_key_fails():
    w = make_world()
    w.agent_pos = (5, 5)
    w.agent_dir = Direction.EAST
    door = Door(position=(6, 5), is_open=False, key_id="key_1")
    w.doors.append(door)
    w.set_cell(6, 5, CellType.DOOR)
    ok, msg = w.use_key()
    assert not ok


# ------------------------------------------------------------------
# Random placement
# ------------------------------------------------------------------

def test_random_empty_reproducible():
    w1 = GridWorld(seed=42)
    w2 = GridWorld(seed=42)
    assert w1.random_empty_position() == w2.random_empty_position()


def test_get_state_is_snapshot():
    w = make_world()
    w.agent_pos = (3, 3)
    state = w.get_state()
    w.agent_pos = (5, 5)
    assert state.agent_pos == (3, 3)  # snapshot unchanged


def test_visited_cells_tracked():
    w = make_world()
    w.agent_pos = (5, 5)
    w.agent_dir = Direction.SOUTH
    w.move_agent()
    assert (5, 6) in w.visited_cells
