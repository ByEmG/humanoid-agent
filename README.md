# LLM Agent in a Virtual World

A Claude-powered intelligent agent that perceives, reasons, and acts inside a 2D grid world — completing goal-directed tasks including navigation, object retrieval, and room exploration.

![Demo](demo.gif)

---

## What It Is

This system places a Large Language Model (Claude) inside a structured virtual environment where it must observe its surroundings, reason about its situation, and choose actions to accomplish goals. The core engineering challenge is the **agent harness** — the interface between the LLM and the world.

The agent is not just generating plausible text. It is genuinely reasoning about spatial relationships, planning multi-step sequences, and completing tasks reliably across different world configurations.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    WORLD STATE                       │
│   Grid, agent position, objects, doors, inventory   │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                   OBSERVER                           │
│   Converts raw world state into structured natural  │
│   language observation the LLM can reason about     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│              CLAUDE (Agent Brain)                    │
│   Receives observation, reasons step by step,       │
│   outputs REASONING + ACTION + CONFIDENCE           │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│                ACTION PARSER                         │
│   Extracts action from Claude response,             │
│   validates against available action space          │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────┐
│               WORLD UPDATE                           │
│   Executes action, updates state, checks success    │
└────────────────────┬────────────────────────────────┘
                     │
                     └──────────────► REPEAT
```

---

## Installation

### Requirements
- Python 3.10+
- Anthropic API key
- macOS / Linux

### Setup

```bash
# Clone the repository
git clone https://github.com/ByEmG/humanoid-agent
cd humanoid-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

---

## How to Run

```bash
# Navigate to goal
python main.py --task navigate

# Find key, unlock door, reach goal
python main.py --task fetch

# Explore the room and generate a description
python main.py --task explore

# Run all three tasks in sequence
python main.py --task all

# Reproducible run with fixed seed
python main.py --task navigate --seed 42

# Headless mode (no rendering, just logs)
python main.py --task navigate --no-render

# Control animation speed
python main.py --task fetch --delay 0.5
```

---

## Tasks

### Task 1: Navigate
Agent must reach a goal tile (★) in a world with random obstacles. Tests basic spatial reasoning and pathfinding.

### Task 2: Fetch
Three-step sequential task: find the key, pick it up, use it on a locked door, reach the goal beyond. Tests multi-step planning and object interaction.

### Task 3: Explore
No explicit goal tile. Agent must visit 70% of accessible cells and generate a natural language description of what it found. Tests systematic search strategies.

---

## Example Output

From a real Fetch task session (seed 42):

```
--- STEP 10 ---
POSITION: (6, 7), facing South
INVENTORY: nothing
NEARBY: KEY at (6,7) distance 1, DOOR (locked) at (8,6) distance 2

REASONING: I'm now at (6,7) where the key should be. I notice PICK_UP
is available as a valid action, which means there's an item here to
pick up. The key must be on this tile and I need to explicitly pick it up.

ACTION: PICK_UP
CONFIDENCE: HIGH

--- STEP 14 ---
POSITION: (8, 7), facing East
INVENTORY: key_1
NEARBY: DOOR (locked) at (8,6) distance 1

REASONING: I'm now at (8,7) and the locked door is directly to my north
at (8,6). USE_KEY is now available as a valid action, which means I'm in
the correct position. I have key_1 in my inventory, so I should use it.

ACTION: USE_KEY
CONFIDENCE: HIGH

=== FINAL RESULT ===
Success: True | Steps: 27 | Task: FETCH
```

---

## Design Choices

### Why a 2D Grid World

A 2D grid is the optimal choice for this challenge for three reasons. First, it is simple enough to implement rigorously — every component of the harness can be built properly rather than cutting corners on a more complex environment. Second, it is rich enough to support genuinely interesting tasks: navigation around obstacles, multi-step object interaction, and systematic exploration all require real reasoning. Third, it produces clear, verifiable results — success is unambiguous and the agent's path can be logged and inspected step by step.

A text-based world would have been easier but harder to visualise. A 3D scene would have been visually impressive but would have shifted engineering effort away from the harness — which is what Humanoid explicitly said they care about most.

### Observation Design

The observation format is the most important engineering decision in this system. The agent can only reason about what it is told, so the observation must contain exactly the right information — no more, no less.

The observation includes six sections: current position and facing direction, a 5x5 local view centred on the agent, the agent's inventory, the last three actions and their outcomes, the current goal in plain English, and the list of valid actions available right now.

The 5x5 local view is deliberately limited. Giving the agent full map knowledge would make tasks trivially easy — the agent would just compute the shortest path. Limiting vision to nearby cells forces genuine reactive decision-making and makes the reasoning more interesting to observe.

The valid actions list is critical. Telling the agent exactly which actions are available at each step prevents invalid action attempts and wasted API calls. It also creates natural affordance signals — when USE_KEY appears in the valid actions, the agent immediately understands it is in position to use its key.

Plain English formatting was chosen over JSON. The LLM reasons more naturally and consistently with structured prose than with a data format it must parse internally.

### Conversation History

The agent maintains the last five turns of conversation history in each API call. This gives it short-term memory — it can reason about what it tried recently and whether it worked. Without history, the agent would repeat failed actions. With too much history, the context window fills and latency increases. Five turns was found to be the right balance: enough to avoid loops, short enough to stay fast.

### Why Claude

Claude was chosen for its strong spatial reasoning, consistent instruction-following, and reliable output formatting. The structured REASONING / ACTION / CONFIDENCE format is followed consistently across hundreds of steps, which is essential for a production agent harness. The reasoning traces are also genuinely useful — they make the agent's decision process transparent and debuggable.

### Action Space Design

The action space is deliberately discrete and minimal: MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, PICK_UP, USE_KEY, WAIT, DESCRIBE. This forces the agent to plan multi-step sequences for any non-trivial movement, which produces more interesting and observable reasoning than a continuous or high-level action space. It also mirrors real robotics constraints where actions are atomic and sequential.

---

## What Worked and What Did Not

**What worked well:**

The observation format proved highly effective. From the session logs, Claude consistently demonstrated correct spatial reasoning — understanding its position relative to objects, planning multi-step routes, and recognising when affordances became available. The Fetch task was completed in 27 steps with no backtracking or confusion, despite the agent having only local vision.

The valid actions list was one of the most impactful design decisions. By only showing actions that are currently executable, the system eliminated an entire class of errors and made the agent's decision loop significantly more reliable.

The conversation history approach worked well for avoiding repetitive loops. In early testing without history the agent would sometimes repeat the same failed move. With five turns of history this behaviour was eliminated.

**What did not work initially:**

Early versions of the observation format included too much information — full object coordinates, distance to every cell visited, compass bearings to all objects. This produced longer and less focused reasoning. Stripping the observation back to the essentials improved both reasoning quality and consistency.

The explore task required more iterations on the success condition. An early version required 80% cell coverage, which was difficult to achieve within the step limit in worlds with complex obstacle layouts. 70% with a higher step allowance produced more reliable task completion while still requiring systematic search behaviour.

**Potential extensions:**

Adding semantic labelling using Segment Anything Model would allow the agent to classify objects it encounters and build a semantic map of the environment — directly relevant to robotics perception pipelines. Real-time path planning using A* as a tool the agent can invoke would allow it to delegate navigation to a classical planner while retaining high-level goal reasoning. Multi-agent variants with two agents collaborating or competing in the same world would be a natural next step for more complex emergent behaviour.

---

## Project Structure

```
humanoid-agent/
├── world/
│   ├── grid.py          # Grid world environment
│   ├── objects.py       # Object definitions
│   └── renderer.py      # Terminal renderer
├── agent/
│   ├── observer.py      # World state to observation
│   ├── brain.py         # Claude API integration
│   └── actions.py       # Action space
├── tasks/
│   ├── navigate.py      # Navigation task
│   ├── fetch.py         # Fetch task
│   └── explore.py       # Exploration task
├── outputs/             # Session logs
├── main.py              # Entry point
├── config.py            # Configuration
├── requirements.txt
├── .env.example
└── README.md
```

---

## Requirements

```
anthropic
rich
numpy
python-dotenv
click
```

---

Built by Pierre Emmanuel Gerard
BSc Applied Artificial Intelligence, University of Bradford
github.com/ByEmG
