"""Task 1: Navigate to goal, avoiding 10 random obstacles."""
from __future__ import annotations
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from world.renderer import Renderer
    from agent.brain import AgentBrain

from world.grid import GridWorld
from world.objects import CellType
from tasks import TaskResult, run_task_loop
import config


def setup_navigate(world: GridWorld, num_obstacles: int = 10) -> str:
    """Place agent, goal, and obstacles. Returns goal description."""
    world.reset()

    # Agent start
    agent_start = world.random_empty_position()
    world.agent_pos = agent_start
    world.visited_cells = {agent_start}

    # Goal
    goal_pos = world.random_empty_position(exclude=[agent_start])
    world.goal_pos = goal_pos
    world.set_cell(*goal_pos, CellType.GOAL)

    # Obstacles
    placed = 0
    exclude = [agent_start, goal_pos]
    for _ in range(num_obstacles * 3):  # retry budget
        if placed >= num_obstacles:
            break
        try:
            pos = world.random_empty_position(exclude=exclude)
            world.set_cell(*pos, CellType.OBSTACLE)
            exclude.append(pos)
            placed += 1
        except ValueError:
            break

    gx, gy = goal_pos
    return (
        f"Navigate to the GOAL (★) at position ({gx}, {gy}). "
        "There are obstacles blocking some paths — find a route around them. "
        "You succeed when you stand on the goal tile."
    )


def run_navigate(
    world: GridWorld,
    brain: "AgentBrain",
    renderer: "Renderer",
    max_steps: int = config.MAX_STEPS,
    step_delay: float = config.STEP_DELAY,
) -> TaskResult:
    goal_desc = setup_navigate(world)

    def is_done(w: GridWorld) -> bool:
        return w.agent_pos == w.goal_pos

    return run_task_loop(
        world, brain, renderer, goal_desc, is_done, max_steps, step_delay
    )
