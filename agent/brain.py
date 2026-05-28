from __future__ import annotations
import os
import re
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import anthropic

if TYPE_CHECKING:
    from world.grid import GridWorld

from agent.actions import ActionType
from agent.observer import build_observation
from config import (
    DEFAULT_MODEL, MAX_RETRIES, RETRY_DELAY,
    HISTORY_TURNS, OUTPUTS_DIR,
)

_SYSTEM_PROMPT = """\
You are an intelligent robot agent navigating a 2D grid world.

Each turn you receive a structured observation describing:
- Your position and what is ahead of you
- A 5×5 local view of your surroundings
- Your inventory
- Your last 3 actions and results
- Your current goal
- Notable objects within 3 cells
- The exact set of valid actions right now

Your task is to reason carefully and choose the best action.

RESPONSE FORMAT — follow exactly:
REASONING: [Think through your current situation, where you need to go, what obstacles you face, and why the chosen action is best. Be concise but thorough.]
ACTION: [One of the valid action names, e.g. MOVE_FORWARD]
CONFIDENCE: [HIGH, MEDIUM, or LOW]

Rules:
- Only use actions listed under VALID ACTIONS in the observation.
- Plan a path in your head — don't just turn randomly.
- If the goal is visible, head toward it efficiently.
- If you need a key, find it first; then find the door.
- WAIT is only for genuine uncertainty, not stalling.
"""


class AgentBrain:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        log_file: Optional[str] = None,
    ):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.history: list[dict] = []  # OpenAI-style messages list
        self.memory: list[str] = []    # plain-text action log for observation

        # Session log
        Path(OUTPUTS_DIR).mkdir(exist_ok=True)
        if log_file is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(OUTPUTS_DIR, f"session_{ts}.txt")
        self.log_file = log_file
        self._init_log()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def step(
        self,
        world: "GridWorld",
        goal_description: str,
    ) -> tuple[str, ActionType, str]:
        """
        One agent turn.
        Returns (reasoning, action_type, confidence).
        """
        observation = build_observation(world, self.memory, goal_description)
        self._log(f"\n--- STEP {world.steps} ---\n{observation}\n")

        self.history.append({"role": "user", "content": observation})
        # Keep history bounded
        if len(self.history) > HISTORY_TURNS * 2:
            self.history = self.history[-(HISTORY_TURNS * 2):]

        response_text = self._call_api()
        self.history.append({"role": "assistant", "content": response_text})

        reasoning, action_type, confidence = self._parse_response(response_text)
        self._log(f"RESPONSE:\n{response_text}\n")
        return reasoning, action_type, confidence

    def record_action_result(self, action: ActionType, result_msg: str) -> None:
        entry = f"{action.value}: {result_msg}"
        self.memory.append(entry)
        if len(self.memory) > 20:
            self.memory = self.memory[-20:]

    def log_result(self, success: bool, steps: int, message: str) -> None:
        self._log(f"\n=== FINAL RESULT ===\nSuccess: {success}\nSteps: {steps}\n{message}\n")

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _call_api(self) -> str:
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=_SYSTEM_PROMPT,
                    messages=self.history,
                )
                return response.content[0].text
            except anthropic.BadRequestError as e:
                # Non-retryable: bad request (e.g. billing, invalid model)
                msg = str(e)
                if "credit balance" in msg or "billing" in msg.lower():
                    raise SystemExit(
                        "\nERROR: Your Anthropic account has no credits.\n"
                        "Add credits at: https://console.anthropic.com/settings/billing\n"
                    ) from e
                raise
            except anthropic.RateLimitError:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    raise
            except anthropic.APIError as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    raise RuntimeError(f"API error after {MAX_RETRIES} retries: {e}") from e
        return "REASONING: API unavailable\nACTION: WAIT\nCONFIDENCE: LOW"

    def _parse_response(self, text: str) -> tuple[str, ActionType, str]:
        reasoning = ""
        action_type = ActionType.WAIT
        confidence = "LOW"

        r_match = re.search(r"REASONING:\s*(.+?)(?=ACTION:|$)", text, re.DOTALL | re.IGNORECASE)
        a_match = re.search(r"ACTION:\s*(\w+)", text, re.IGNORECASE)
        c_match = re.search(r"CONFIDENCE:\s*(HIGH|MEDIUM|LOW)", text, re.IGNORECASE)

        if r_match:
            reasoning = r_match.group(1).strip()
        if a_match:
            try:
                action_type = ActionType.from_string(a_match.group(1))
            except ValueError:
                action_type = ActionType.WAIT
        if c_match:
            confidence = c_match.group(1).upper()

        return reasoning, action_type, confidence

    def _init_log(self) -> None:
        with open(self.log_file, "w") as f:
            f.write(f"=== Agent Session Log ===\n")
            f.write(f"Started: {datetime.now().isoformat()}\n")
            f.write(f"Model:   {self.model}\n\n")

    def _log(self, text: str) -> None:
        with open(self.log_file, "a") as f:
            f.write(text + "\n")
