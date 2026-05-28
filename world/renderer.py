from __future__ import annotations
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from world.objects import CellType, Direction, WorldState

# Visual tokens
_CELL_TOKENS: dict[CellType, tuple[str, str]] = {
    CellType.EMPTY:    ("·", "grey30"),
    CellType.WALL:     ("█", "grey50"),
    CellType.GOAL:     ("⭐", "bright_yellow"),
    CellType.KEY:      ("🔑", "bright_green"),
    CellType.DOOR:     ("🚪", "red"),
    CellType.OBSTACLE: ("▪", "orange3"),
    CellType.AGENT:    ("🤖", "bright_cyan"),
}

_DIR_ARROW = {
    Direction.NORTH: "↑",
    Direction.SOUTH: "↓",
    Direction.EAST:  "→",
    Direction.WEST:  "←",
}


class Renderer:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.console = Console()
        self._step_count = 0

    def render(
        self,
        state: WorldState,
        reasoning: str = "",
        action: str = "",
        result_msg: str = "",
    ) -> None:
        if not self.enabled:
            return

        self.console.clear()
        self._step_count += 1

        grid_text = self._render_grid(state)
        stats_text = self._render_stats(state)
        thought_text = self._render_thought(reasoning, action, result_msg)

        top = Columns([
            Panel(grid_text, title="[bold cyan]Grid World[/bold cyan]", border_style="cyan"),
            Panel(stats_text, title="[bold yellow]Agent Status[/bold yellow]", border_style="yellow"),
        ])
        self.console.print(top)
        self.console.print(Panel(
            thought_text,
            title=f"[bold magenta]Step {state.steps} — Agent Reasoning[/bold magenta]",
            border_style="magenta",
        ))

    def render_result(self, success: bool, steps: int, message: str) -> None:
        if not self.enabled:
            return
        colour = "bright_green" if success else "bright_red"
        icon = "✅" if success else "❌"
        self.console.print(Rule(f"[{colour}]{icon}  {message}  (steps: {steps})[/{colour}]"))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _render_grid(self, state: WorldState) -> Text:
        text = Text()
        ax, ay = state.agent_pos
        for y in range(state.height):
            for x in range(state.width):
                if (x, y) == state.agent_pos:
                    token, colour = "🤖", "bright_cyan"
                elif state.goal_pos and (x, y) == state.goal_pos:
                    token, colour = "⭐", "bright_yellow"
                else:
                    cell = state.grid[y][x]
                    # Check if there's an open door here (rendered as passable)
                    is_open_door = any(
                        d.position == (x, y) and d.is_open for d in state.doors
                    )
                    if is_open_door:
                        token, colour = "▭", "bright_green"
                    elif cell == CellType.DOOR:
                        # Check if this door is open
                        door = next((d for d in state.doors if d.position == (x, y)), None)
                        if door and door.is_open:
                            token, colour = "▭", "bright_green"
                        else:
                            token, colour = "🚪", "red"
                    else:
                        token, colour = _CELL_TOKENS.get(cell, ("?", "white"))
                text.append(token + " ", style=colour)
            text.append("\n")
        return text

    def _render_stats(self, state: WorldState) -> Text:
        text = Text()
        text.append("Position:  ", style="bold")
        text.append(f"{state.agent_pos}\n")
        text.append("Facing:    ", style="bold")
        text.append(f"{_DIR_ARROW[state.agent_dir]} {state.agent_dir.value}\n")
        text.append("Steps:     ", style="bold")
        text.append(f"{state.steps}\n")
        text.append("Goal:      ", style="bold")
        text.append(f"{state.goal_pos or 'none'}\n\n")
        text.append("Inventory:\n", style="bold")
        if state.inventory:
            for item in state.inventory:
                text.append(f"  🔑 {item}\n", style="bright_green")
        else:
            text.append("  (empty)\n", style="grey50")
        text.append("\nVisited:   ", style="bold")
        accessible = state.get_accessible_cells()
        pct = (len(state.visited_cells) / len(accessible) * 100) if accessible else 0
        text.append(f"{len(state.visited_cells)}/{len(accessible)} ({pct:.0f}%)\n")
        return text

    def _render_thought(self, reasoning: str, action: str, result: str) -> Text:
        text = Text()
        if reasoning:
            text.append("REASONING\n", style="bold bright_white")
            text.append(reasoning.strip() + "\n\n", style="white")
        if action:
            text.append("ACTION: ", style="bold cyan")
            text.append(action + "\n", style="cyan")
        if result:
            text.append("RESULT: ", style="bold")
            text.append(result + "\n", style="grey85")
        return text
