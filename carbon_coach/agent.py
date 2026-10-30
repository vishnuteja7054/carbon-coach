"""
Google ADK Agent definitions for Carbon Coach.

Defines:
- `tracker_agent`: Specialized footprint tracker & emission calculator agent.
- `coach_advisor_agent`: Specialized carbon reduction strategist & benchmark advisor agent.
- `root_agent`: The primary Carbon Coach coordinator agent discovered by `adk web` / `adk run`.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from google.adk.agents import LlmAgent

from carbon_coach.prompts import (
    ROOT_COACH_INSTRUCTION,
    TRACKER_AGENT_INSTRUCTION,
    ADVISOR_AGENT_INSTRUCTION,
)
from carbon_coach.tools import (
    calculate_travel_emissions,
    calculate_electricity_emissions,
    calculate_food_emissions,
    calculate_waste_emissions,
    log_activity,
    get_summary,
    clear_session_logs,
    suggest_reductions,
)

_ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT_DIR / ".env", override=False)
load_dotenv(_ROOT_DIR / ".env.example", override=False)

_raw_model = os.environ.get("CARBON_COACH_MODEL", "gemini-flash-lite-latest").strip()
MODEL_NAME = "-".join(_raw_model.split()) if _raw_model else "gemini-flash-lite-latest"

# 1. Specialized Tracker Sub-Agent
tracker_agent = LlmAgent(
    name="tracker_agent",
    model=MODEL_NAME,
    description=(
        "Calculates exact kg CO2e emissions for travel, electricity, food, and waste "
        "activities using deterministic Python tools and logs them into memory."
    ),
    instruction=TRACKER_AGENT_INSTRUCTION,
    tools=[
        calculate_travel_emissions,
        calculate_electricity_emissions,
        calculate_food_emissions,
        calculate_waste_emissions,
        log_activity,
        get_summary,
        clear_session_logs,
    ],
)

# 2. Specialized Coach Advisor Sub-Agent
coach_advisor_agent = LlmAgent(
    name="coach_advisor_agent",
    model=MODEL_NAME,
    description=(
        "Analyzes logged carbon footprint data, compares totals against India and global "
        "sustainability benchmarks, and generates personalized reduction tips with exact kg CO2e savings."
    ),
    instruction=ADVISOR_AGENT_INSTRUCTION,
    tools=[
        get_summary,
        suggest_reductions,
    ],
)

# 3. Root Carbon Coach Agent (exposed to ADK Runner & Web UI)
root_agent = LlmAgent(
    name="carbon_coach",
    model=MODEL_NAME,
    description=(
        "Carbon Coach AI agent that helps students, households, and campuses measure, "
        "understand, and reduce their daily carbon footprint using verified emission factors."
    ),
    instruction=ROOT_COACH_INSTRUCTION,
    tools=[
        calculate_travel_emissions,
        calculate_electricity_emissions,
        calculate_food_emissions,
        calculate_waste_emissions,
        log_activity,
        get_summary,
        suggest_reductions,
        clear_session_logs,
    ],
)
