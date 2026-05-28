from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from world.grid import GridWorld
    from world.renderer import Renderer
    from agent.brain import AgentBrain

from agent.actions import execute_action, ActionType
from world.objects import CellType


@dataclass
class TaskResult:
    success: bool
    steps: int
    message: str


def run_task_loop(
    world: "GridWorld",
    brain: "AgentBrain",
    renderer: "Renderer",
    goal_description: str,
    is_done: Callable[["GridWorld"], bool],
    max_steps: int = 100,
    step_delay: float = 0.5,
) -> TaskResult:
    """Generic task execution loop shared by all three tasks."""
    while world.steps < max_steps:
        state = world.get_state()

        if is_done(world):
            renderer.render(state, "", "", "Goal achieved!")
            renderer.render_result(True, world.steps, "Task complete!")
            brain.log_result(True, world.steps, "Task complete!")
            return TaskResult(True, world.steps, "Task complete!")

        reasoning, action, confidence = brain.step(world, goal_description)
        result = execute_action(world, action)
        brain.record_action_result(action, result.message)

        new_state = world.get_state()
        renderer.render(new_state, reasoning, action.value, result.message)

        if step_delay > 0:
            time.sleep(step_delay)

    renderer.render_result(False, world.steps, f"Failed: max steps ({max_steps}) reached.")
    brain.log_result(False, world.steps, "Max steps reached.")
    return TaskResult(False, world.steps, f"Max steps ({max_steps}) reached.")
