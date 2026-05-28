"""Task 3: Explore ≥70% of accessible cells, then generate a description."""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.renderer import Renderer
    from agent.brain import AgentBrain

from world.grid import GridWorld
from world.objects import CellType, Door, Key
from tasks import TaskResult, run_task_loop
from agent.actions import execute_action, ActionType
import config

EXPLORATION_THRESHOLD = 0.70


def setup_explore(world: GridWorld) -> str:
    """Populate a rich room and return goal description."""
    world.reset()

    # Agent start
    agent_start = world.random_empty_position()
    world.agent_pos = agent_start
    world.visited_cells = {agent_start}

    # Scatter objects so there's something to describe
    exclude = [agent_start]

    # A key
    key_pos = world.random_empty_position(exclude=exclude)
    world.set_cell(*key_pos, CellType.KEY)
    world.keys.append(Key(position=key_pos, key_id="key_explore"))
    exclude.append(key_pos)

    # A door (open from the start, just for scenery)
    door_pos = world.random_empty_position(exclude=exclude)
    world.set_cell(*door_pos, CellType.DOOR)
    world.doors.append(Door(position=door_pos, is_open=True, key_id="key_explore"))
    exclude.append(door_pos)

    # Several obstacles
    for _ in range(5):
        try:
            pos = world.random_empty_position(exclude=exclude)
            world.set_cell(*pos, CellType.OBSTACLE)
            exclude.append(pos)
        except ValueError:
            break

    return (
        "EXPLORE TASK — map the room:\n"
        f"  • Visit at least {int(EXPLORATION_THRESHOLD*100)}% of all accessible cells.\n"
        "  • When done, use the DESCRIBE action to generate a natural language report of everything you found.\n"
        "  • There is no explicit goal tile — thorough exploration is the goal.\n"
        "Tip: move systematically (e.g. sweep rows) to cover the space efficiently."
    )


def run_explore(
    world: GridWorld,
    brain: "AgentBrain",
    renderer: "Renderer",
    max_steps: int = config.MAX_STEPS,
    step_delay: float = config.STEP_DELAY,
) -> TaskResult:
    goal_desc = setup_explore(world)
    description_generated = {"done": False, "text": ""}

    def is_done(w: GridWorld) -> bool:
        state = w.get_state()
        accessible = state.get_accessible_cells()
        if not accessible:
            return True
        coverage = len(w.visited_cells) / len(accessible)
        return coverage >= EXPLORATION_THRESHOLD and description_generated["done"]

    # Wrap the standard loop with a hook to capture DESCRIBE output
    import time
    from agent.actions import execute_action

    while world.steps < max_steps:
        state = world.get_state()

        if is_done(world):
            renderer.render(state, "", "DESCRIBE", description_generated["text"])
            renderer.render_result(True, world.steps, "Exploration complete!")
            brain.log_result(True, world.steps, description_generated["text"])
            return TaskResult(True, world.steps, description_generated["text"])

        reasoning, action, confidence = brain.step(world, goal_desc)
        result = execute_action(world, action)

        # If agent chose DESCRIBE, capture a room summary from the brain
        if action == ActionType.DESCRIBE and not description_generated["done"]:
            description_generated["done"] = True
            description_generated["text"] = _generate_description(world, brain)
            result.message = description_generated["text"]

        brain.record_action_result(action, result.message)
        new_state = world.get_state()
        renderer.render(new_state, reasoning, action.value, result.message)

        if step_delay > 0:
            time.sleep(step_delay)

    renderer.render_result(False, world.steps, "Exploration failed: max steps reached.")
    brain.log_result(False, world.steps, "Max steps reached.")
    return TaskResult(False, world.steps, "Max steps reached.")


def _generate_description(world: GridWorld, brain: "AgentBrain") -> str:
    """Ask the brain to produce a natural language room report."""
    state = world.get_state()
    accessible = state.get_accessible_cells()
    coverage = len(world.visited_cells) / len(accessible) if accessible else 0

    objects_found = []
    for y in range(state.height):
        for x in range(state.width):
            cell = state.grid[y][x]
            if cell not in (CellType.EMPTY, CellType.WALL):
                objects_found.append(f"{cell.value} at ({x},{y})")

    prompt = (
        f"You have explored {coverage*100:.0f}% of the room "
        f"({len(world.visited_cells)}/{len(accessible)} cells). "
        f"Objects found: {', '.join(objects_found) if objects_found else 'none'}. "
        "Write a concise natural language description of the room and what you discovered."
    )
    try:
        resp = brain.client.messages.create(
            model=brain.model,
            max_tokens=300,
            system="You are an exploring robot. Write a concise room description based on what you found.",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception:
        return f"Explored {coverage*100:.0f}% of the room. Found: {', '.join(objects_found)}."
