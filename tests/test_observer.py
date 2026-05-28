import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from world.grid import GridWorld
from world.objects import Direction, CellType, Key
from agent.observer import build_observation


def make_world():
    w = GridWorld(width=10, height=10, seed=0)
    w.agent_pos = (5, 5)
    w.agent_dir = Direction.NORTH
    return w


def test_observation_has_all_sections():
    w = make_world()
    obs = build_observation(w, [], "Test goal")
    assert "POSITION" in obs
    assert "LOCAL VIEW" in obs
    assert "INVENTORY" in obs
    assert "RECENT ACTIONS" in obs
    assert "CURRENT GOAL" in obs
    assert "NEARBY OBJECTS" in obs
    assert "VALID ACTIONS" in obs


def test_observation_contains_position():
    w = make_world()
    obs = build_observation(w, [], "goal")
    assert "(5, 5)" in obs


def test_observation_contains_direction():
    w = make_world()
    obs = build_observation(w, [], "goal")
    assert "North" in obs


def test_observation_inventory_empty():
    w = make_world()
    obs = build_observation(w, [], "goal")
    assert "nothing" in obs.lower()


def test_observation_inventory_with_item():
    w = make_world()
    w.inventory = ["key_1"]
    obs = build_observation(w, [], "goal")
    assert "key_1" in obs


def test_observation_memory_shows_last_3():
    w = make_world()
    memory = ["action A", "action B", "action C", "action D"]
    obs = build_observation(w, memory, "goal")
    assert "action B" in obs
    assert "action C" in obs
    assert "action D" in obs
    assert "action A" not in obs


def test_observation_goal_text():
    w = make_world()
    obs = build_observation(w, [], "Navigate to the star")
    assert "Navigate to the star" in obs


def test_observation_nearby_key():
    w = make_world()
    w.agent_pos = (5, 5)
    w.keys.append(Key(position=(5, 6), key_id="k1"))
    w.set_cell(5, 6, CellType.KEY)
    obs = build_observation(w, [], "goal")
    assert "KEY" in obs or "key" in obs.lower()


def test_observation_valid_actions_listed():
    w = make_world()
    obs = build_observation(w, [], "goal")
    assert "WAIT" in obs
    assert "TURN_LEFT" in obs
    assert "TURN_RIGHT" in obs
