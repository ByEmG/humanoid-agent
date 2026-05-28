"""Entry point for the Humanoid LLM agent challenge."""
from __future__ import annotations
import os
import sys
import click
from dotenv import load_dotenv

load_dotenv()

from world.grid import GridWorld
from world.renderer import Renderer
from agent.brain import AgentBrain
from tasks.navigate import run_navigate
from tasks.fetch import run_fetch
from tasks.explore import run_explore
import config


TASKS = ["navigate", "fetch", "explore", "all"]


@click.command()
@click.option("--task", default="navigate", type=click.Choice(TASKS), show_default=True,
              help="Which task to run.")
@click.option("--seed", default=None, type=int, help="Random seed for reproducibility.")
@click.option("--max-steps", default=config.MAX_STEPS, show_default=True,
              help="Maximum steps before task fails.")
@click.option("--delay", default=config.STEP_DELAY, show_default=True,
              help="Seconds between steps (0 for instant).")
@click.option("--no-render", is_flag=True, help="Disable visual rendering (headless mode).")
@click.option("--model", default=config.DEFAULT_MODEL, show_default=True,
              help="Claude model to use.")
def main(task, seed, max_steps, delay, no_render, model):
    """LLM Agent in a Virtual World — Humanoid Robotics Challenge."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        click.echo(
            "ERROR: ANTHROPIC_API_KEY not set.\n"
            "Copy .env.example to .env and add your key.",
            err=True,
        )
        sys.exit(1)

    world = GridWorld(
        width=config.GRID_WIDTH,
        height=config.GRID_HEIGHT,
        seed=seed,
    )
    renderer = Renderer(enabled=not no_render)
    brain = AgentBrain(model=model, api_key=api_key)

    tasks_to_run = ["navigate", "fetch", "explore"] if task == "all" else [task]

    for t in tasks_to_run:
        if len(tasks_to_run) > 1:
            click.echo(f"\n{'='*50}\n  Running task: {t.upper()}\n{'='*50}\n")

        if t == "navigate":
            result = run_navigate(world, brain, renderer, max_steps, delay)
        elif t == "fetch":
            result = run_fetch(world, brain, renderer, max_steps, delay)
        elif t == "explore":
            result = run_explore(world, brain, renderer, max_steps, delay)

        status = "SUCCESS" if result.success else "FAILURE"
        click.echo(f"\n[{status}] {t}: {result.message} (steps: {result.steps})")
        click.echo(f"Session log: {brain.log_file}")


if __name__ == "__main__":
    main()
