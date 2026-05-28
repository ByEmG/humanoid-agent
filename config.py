import os
from dotenv import load_dotenv

load_dotenv()

# Grid
GRID_WIDTH = 10
GRID_HEIGHT = 10

# Agent
DEFAULT_MODEL = "claude-sonnet-4-20250514"
MAX_STEPS = 100
STEP_DELAY = 0.5
HISTORY_TURNS = 5
LOCAL_VIEW_RADIUS = 2
NEARBY_RADIUS = 3

# Logging
OUTPUTS_DIR = "outputs"

# API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MAX_RETRIES = 3
RETRY_DELAY = 2.0
