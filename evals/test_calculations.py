"""
Golden Evaluation & Unit Test Suite for Carbon Coach.

Proves 100% deterministic accuracy across:
1. Kickoff Hackathon Prompt ("I travelled 12 km by bus today and used the AC for 4 hours.")
2. Travel, Electricity (kWh & Appliance+Hours), Food, and Waste calculators
3. Session & SQLite Memory persistence (`get_summary`, `log_activity`, `clear_session_logs`)
4. Personalized Reduction Coach math (`suggest_reductions`)
5. Google ADK Agent & Tool registration integrity
"""

import os
import pytest

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
from carbon_coach.agent import root_agent, tracker_agent, coach_advisor_agent


@pytest.fixture(autouse=True)
def isolated_test_db(tmp_path, monkeypatch):
    """Use an isolated temporary SQLite database for every test."""
    db_file = tmp_path / "test_carbon_memory.db"
    monkeypatch.setenv("CARBON_DB_PATH", str(db_file))
    yield db_file


def test_golden_case_1_hackathon_kickoff_prompt():
    """
    Golden Eval 1:
    User says: 'I travelled 12 km by bus today and used the AC for 4 hours.'
    Verify exact tool outputs, cumulative summary, benchmark comparison, and reduction savings.
    """
    # Step 1: 12 km by bus
    bus_res = calculate_travel_emissions(mode="bus", km=12)
    assert bus_res["status"] == "success"
    assert bus_res["mode"] == "bus"
    assert bus_res["emission_factor_kg_per_km"] == 0.089
    assert bus_res["kg_co2e"] == 1.068  # 12 * 0.089 = 1.068
    assert bus_res["logged"] is True

    # Step 2: AC for 4 hours
    ac_res = calculate_electricity_emissions(appliance="ac", hours=4)
    assert ac_res["status"] == "success"
    assert ac_res["subcategory"] == "ac"
    assert ac_res["kwh"] == 6.0  # 1.5 kW * 4h = 6.0 kWh
    assert ac_res["kg_co2e"] == 4.296  # 6.0 * 0.716 = 4.296
    assert ac_res["logged"] is True

    # Step 3: Session summary & benchmark comparison
    summary = get_summary(period="today")
    assert summary["status"] == "success"
    assert summary["total_activities"] == 2
    assert summary["total_kg_co2e"] == 5.364  # 1.068 + 4.296 = 5.364
    assert summary["by_category"]["electricity"]["kg_co2e"] == 4.296
    assert summary["by_category"]["travel"]["kg_co2e"] == 1.068
    assert summary["highest_impact_activity"]["category"] == "electricity"

    # Check India benchmark comparison (5.48 kg/day)
    india_cmp = summary["benchmark_comparisons"]["india_average"]
    assert india_cmp["benchmark_daily_kg_co2e"] == 5.48
    assert india_cmp["difference_kg_co2e"] == -0.116

    # Step 4: Personalized reduction suggestions
    tips = suggest_reductions(period="today")
    assert tips["status"] == "success"
    assert tips["current_total_kg_co2e"] == 5.364
    assert len(tips["recommendations"]) == 2
    # Top tip must be AC optimization saving 1.396 kg CO2e
    top_tip = tips["recommendations"][0]
    assert top_tip["category"] == "electricity"
    assert top_tip["estimated_saving_kg_co2e"] == 1.396
    # Second tip is bus last-mile cycling saving 0.267 kg CO2e (and noting 0.972 kg already saved vs car)
    second_tip = tips["recommendations"][1]
    assert second_tip["category"] == "travel"
    assert second_tip["estimated_saving_kg_co2e"] == 0.267
    assert second_tip["already_saved_vs_petrol_car_kg_co2e"] == 0.972


def test_golden_case_2_carpooling_and_direct_kwh():
    """Verify car passenger splitting and direct kWh calculation."""
    # 20 km petrol car shared by 2 passengers: (20 * 0.170) / 2 = 1.700 kg CO2e
    car_res = calculate_travel_emissions(mode="petrol car", km=20, passengers=2)
    assert car_res["kg_co2e"] == 1.700

    # Direct 10 kWh electricity: 10 * 0.716 = 7.160 kg CO2e
    elec_res = calculate_electricity_emissions(kwh=10.0)
    assert elec_res["kg_co2e"] == 7.160


def test_golden_case_3_food_and_waste_calculators():
    """Verify food (veg, chicken, mutton) and waste (plastic bottles, food waste) math."""
    veg = calculate_food_emissions(meal_type="veg thali", servings=2)
    assert veg["kg_co2e"] == 2.200  # 2 * 1.10

    chicken = calculate_food_emissions(meal_type="chicken biryani", servings=1)
    assert chicken["kg_co2e"] == 2.350

    bottles = calculate_waste_emissions(waste_type="plastic bottle", quantity=3)
    assert bottles["kg_co2e"] == 0.246  # 3 * 0.082

    food_waste = calculate_waste_emissions(waste_type="food waste", quantity=0.5)
    assert food_waste["kg_co2e"] == 0.425  # 0.5 * 0.850


def test_golden_case_4_memory_lifecycle():
    """Verify explicit logging, summary retrieval, and clearing session logs."""
    log_activity(category="other", details="Campus Event Printing", kg_co2e=0.500)
    s1 = get_summary(period="all")
    assert s1["total_activities"] == 1
    assert s1["total_kg_co2e"] == 0.500

    cleared = clear_session_logs()
    assert cleared["removed_count"] == 1

    s2 = get_summary(period="all")
    assert s2["total_activities"] == 0
    assert s2["total_kg_co2e"] == 0.0


def test_golden_case_5_adk_agent_registration():
    """Verify Google ADK agents and tools are properly configured."""
    assert root_agent.name == "carbon_coach"
    assert len(root_agent.tools) == 8
    assert tracker_agent.name == "tracker_agent"
    assert coach_advisor_agent.name == "coach_advisor_agent"


def test_golden_case_6_api_multilingual_pipeline():
    """Verify the FastAPI /api/chat deterministic tool pipeline across English, Telugu, and Hindi."""
    from app import _run_deterministic_tool_pipeline

    # 1. English kickoff prompt
    res_en = _run_deterministic_tool_pipeline(
        "I travelled 12 km by bus today and used the AC for 4 hours."
    )
    assert res_en["status"] == "success"
    assert res_en["summary_today"]["total_kg_co2e"] == 5.364
    assert "5.364" in res_en["reply"]
    assert "1.396" in res_en["reply"]
    assert "structured_report" in res_en
    sr = res_en["structured_report"]
    assert sr["headline_verdict"]["turn_added_kg"] == 5.364
    assert len(sr["itemized_breakdown"]) == 2
    assert sr["daily_footprint"]["total_kg_co2e"] == 5.364
    assert len(sr["interactive_actions"]) >= 1

    clear_session_logs()

    # 2. Telugu prompt
    res_te = _run_deterministic_tool_pipeline(
        "నేను ఈరోజు బస్సులో 12 కి.మీ ప్రయాణించాను మరియు 4 గంటలు AC వాడాను."
    )
    assert res_te["summary_today"]["total_kg_co2e"] == 5.364
    assert "5.364" in res_te["reply"]

    clear_session_logs()

    # 3. Hindi prompt
    res_hi = _run_deterministic_tool_pipeline(
        "मैंने आज बस से 12 किमी यात्रा की और 4 घंटे एसी चलाया।"
    )
    assert res_hi["summary_today"]["total_kg_co2e"] == 5.364
    assert "5.364" in res_hi["reply"]


def test_golden_case_7_live_google_adk_gemini_execution():
    """Verify live Google ADK agent execution with Gemini API key and real tool invocation."""
    import asyncio
    from carbon_coach.runner import run_carbon_coach_turn

    res = asyncio.run(
        run_carbon_coach_turn(
            "I travelled 12 km by bus today and used the AC for 4 hours.",
            session_id="pytest_live_adk_session",
        )
    )
    assert res["status"] == "success"
    called_tools = [t["tool_name"] for t in res["tool_trace"] if t["type"] == "tool_call"]
    assert "calculate_travel_emissions" in called_tools
    assert "calculate_electricity_emissions" in called_tools
    assert res["summary_today"]["total_kg_co2e"] == 5.364
    assert "1.068" in res["reply"]
    assert "4.296" in res["reply"]
    assert "5.364" in res["reply"]


