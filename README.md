# LLM Agent in a Virtual World

A Claude-powered agent that perceives, reasons, and acts inside a 2D grid world — built for the Humanoid robotics internship challenge.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    WORLD STATE                      │
│   Grid · Agent pos · Doors · Keys · Inventory      │
└────────────────────┬────────────────────────────────┘
                     │ get_state()
                     ▼
┌─────────────────────────────────────────────────────┐
│                   OBSERVER                          │
│  Position · Local view · Inventory · Memory        │
│  Goal · Nearby objects · Valid actions             │
└────────────────────┬────────────────────────────────┘
                     │ structured English prompt
                     ▼
┌─────────────────────────────────────────────────────┐
│              CLAUDE (Sonnet 4)                      │
│   REASONING: …                                     │
│   ACTION: MOVE_FORWARD                             │
│   CONFIDENCE: HIGH                                 │
└────────────────────┬────────────────────────────────┘
                     │ response text
                     ▼
┌─────────────────────────────────────────────────────┐
│               ACTION PARSER                         │
│   regex extract ACTION field → ActionType enum     │
└────────────────────┬────────────────────────────────┘
                     │ ActionType
                     ▼
┌─────────────────────────────────────────────────────┐
│             WORLD UPDATE                            │
│   execute_action() mutates GridWorld state         │
└────────────────────┬────────────────────────────────┘
                     │ new state + result message
                     ▼
              ┌──────┴──────┐
              │  RENDERER   │  ← rich terminal panels
              └─────────────┘
                     │
                  (repeat)
```

---

## Installation

```bash
cd humanoid-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your API key
cp .env.example .env
# Edit .env and set:  ANTHROPIC_API_KEY=sk-ant-...
```

---

## Running

```bash
# Navigate to a goal (default task)
python main.py --task navigate

# Fetch task: key → door → goal
python main.py --task fetch

# Explore task: cover 70% of the room
python main.py --task explore

# Run all three in sequence
python main.py --task all

# Reproducible run (same world every time)
python main.py --task navigate --seed 42

# Headless mode (no visuals, just logs)
python main.py --task navigate --no-render

# Custom parameters
python main.py --task navigate --seed 7 --max-steps 150 --delay 0.3

# Use a different model
python main.py --task fetch --model claude-opus-4-7
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
humanoid-agent/
├── world/
│   ├── objects.py      # CellType, Direction, Door, Key, WorldState
│   ├── grid.py         # GridWorld: state, movement, placement
│   └── renderer.py     # Rich terminal renderer
├── agent/
│   ├── actions.py      # ActionType enum + execute_action()
│   ├── observer.py     # Converts world state → English observation
│   └── brain.py        # Claude API loop, parsing, session logging
├── tasks/
│   ├── __init__.py     # Shared run_task_loop()
│   ├── navigate.py     # Task 1: reach the goal
│   ├── fetch.py        # Task 2: key → door → goal
│   └── explore.py      # Task 3: map the room
├── tests/
│   ├── test_grid.py
│   ├── test_actions.py
│   ├── test_observer.py
│   └── test_brain.py
├── outputs/            # Session logs (auto-created)
├── main.py             # CLI entry point
├── config.py           # All tunable constants
└── requirements.txt
```

---

## Design Choices

### Why a 2D grid?
Simple enough to implement correctly and render in a terminal; complex enough to require real spatial reasoning (pathfinding around obstacles, multi-step sub-goals). A continuous 3D environment would demand a physics engine and visual encoder — solving the planning problem first, in isolation, is more interesting for an LLM challenge.

### Observation design
The agent receives plain English, not raw grid arrays. Structured sections (position, local view, inventory, recent memory, goal, nearby objects, valid actions) give Claude exactly what it needs without hallucination-prone gaps. JSON was considered but rejected — structured text reads naturally to a language model and is more robust to whitespace errors.

### Why Claude?
Claude Sonnet has strong chain-of-thought reasoning for spatial tasks. The `REASONING / ACTION / CONFIDENCE` response format externalises the agent's thought process, making debugging straightforward and the internship demo compelling.

### Conversation history (last 5 turns)
The agent maintains a rolling 5-turn history so it can remember where it has been and what it has already tried. More turns → higher token cost and context noise; fewer → the agent forgets and repeats mistakes. Five turns is empirically a good balance for a 10×10 world.

### Action space
Discrete actions (turn/move/pick/use/wait) keep the API surface small and the reasoning tractable. A continuous action space would require the model to output coordinates, introducing parsing errors and reducing the signal-to-noise ratio in reasoning.

---

## What Worked and What Didn't

*(Fill this in after running the agent — be honest about failures, they're the most interesting part of the report.)*

**What worked:**
- 

**What didn't:**
- 

**Surprising behaviours:**
- 

---

## Example Session Log

```
=== Agent Session Log ===
Started: 2026-05-28T10:00:00

--- STEP 0 ---
=== POSITION ===
You are at (3, 7), facing North.
Directly ahead (3, 6): open space.
Steps taken so far: 0.

=== LOCAL VIEW (5×5 centered on you) ===
  ...  (grid excerpt)

=== CURRENT GOAL ===
Navigate to the GOAL (★) at position (7, 2).

=== VALID ACTIONS ===
WAIT, DESCRIBE, TURN_LEFT, TURN_RIGHT, MOVE_FORWARD

RESPONSE:
REASONING: The goal is at (7,2) and I'm at (3,7), so I need to move
northeast. I'm facing North and the cell ahead is open, so MOVE_FORWARD
is the best first step.
ACTION: MOVE_FORWARD
CONFIDENCE: HIGH
```
