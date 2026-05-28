"""Task 2: Find key → open door → reach goal."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.renderer import Renderer
    from agent.brain import AgentBrain

from world.grid import GridWorld
from world.objects import CellType, Door, Key
from tasks import TaskResult, run_task_loop
import config


def setup_fetch(world: GridWorld) -> str:
    """Place agent, key, locked door, and goal. Returns goal description."""
    world.reset()

    # Agent start
    agent_start = world.random_empty_position()
    world.agent_pos = agent_start
    world.visited_cells = {agent_start}

    # Key placement
    key_pos = world.random_empty_position(exclude=[agent_start])
    world.set_cell(*key_pos, CellType.KEY)
    world.keys.append(Key(position=key_pos, key_id="key_1"))

    # Door — ensure it's not adjacent to agent start to make task interesting
    exclude = [agent_start, key_pos]
    door_pos = world.random_empty_position(exclude=exclude)
    world.set_cell(*door_pos, CellType.DOOR)
    world.doors.append(Door(position=door_pos, is_open=False, key_id="key_1"))

    # Goal — on the far side of the door (just pick a free spot)
    exclude.append(door_pos)
    goal_pos = world.random_empty_position(exclude=exclude)
    world.goal_pos = goal_pos
    world.set_cell(*goal_pos, CellType.GOAL)

    kx, ky = key_pos
    dx, dy = door_pos
    gx, gy = goal_pos
    return (
        f"FETCH TASK — three steps:\n"
        f"  1. Find the KEY (🔑) at ({kx},{ky}) and pick it up.\n"
        f"  2. Use the key on the DOOR (🚪) at ({dx},{dy}) to open it.\n"
        f"  3. Walk through and reach the GOAL (★) at ({gx},{gy}).\n"
        "You succeed when you stand on the goal tile after opening the door."
    )


def run_fetch(
    world: GridWorld,
    brain: "AgentBrain",
    renderer: "Renderer",
    max_steps: int = config.MAX_STEPS,
    step_delay: float = config.STEP_DELAY,
) -> TaskResult:
    goal_desc = setup_fetch(world)

    def is_done(w: GridWorld) -> bool:
        return w.agent_pos == w.goal_pos

    return run_task_loop(
        world, brain, renderer, goal_desc, is_done, max_steps, step_delay
    )
