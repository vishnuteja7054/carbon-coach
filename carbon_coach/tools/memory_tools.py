"""
Session and Persistent Memory Tools for Google ADK Carbon Coach.

Provides `log_activity`, `get_summary`, and `clear_session_logs` backed by SQLite.
"""

from typing import Dict, Any
from carbon_coach.database.store import (
    insert_activity,
    fetch_activities,
    clear_user_activities,
)
from carbon_coach.data.emission_factors import DAILY_BENCHMARKS_KG_CO2E


def log_activity(
    category: str,
    details: str,
    kg_co2e: float,
    quantity: float = 1.0,
    unit: str = "activity",
    subcategory: str = "manual_log",
) -> Dict[str, Any]:
    """Explicitly log a pre-calculated emission activity into the user's memory.

    Note: `calculate_travel_emissions`, `calculate_electricity_emissions`,
    `calculate_food_emissions`, and `calculate_waste_emissions` already auto-log
    by default (`auto_log=True`). Only call `log_activity` if `auto_log=False`
    was used or when recording a custom pre-verified activity.

    Args:
        category: One of 'travel', 'electricity', 'food', 'waste', or 'other'.
        details: Human-readable description of the activity.
        kg_co2e: Exact calculated emissions in kg CO2e from a calculator tool.
        quantity: Numeric amount associated with the activity (default 1.0).
        unit: Unit of measurement (e.g., 'km', 'kWh', 'meal', 'item').
        subcategory: Specific subtype identifier (default 'manual_log').

    Returns:
        Dictionary with the saved activity record and `activity_id`.
    """
    entry = insert_activity(
        category=category,
        subcategory=subcategory,
        label=details,
        quantity=quantity,
        unit=unit,
        kg_co2e=kg_co2e,
        formula=f"Logged {quantity} {unit} = {round(float(kg_co2e), 3)} kg CO2e",
        source="Carbon Coach Verified Tool Output",
    )
    return {
        "status": "success",
        "message": f"Logged {details} ({entry['kg_co2e']} kg CO2e) under {category}.",
        "entry": entry,
    }


def get_summary(period: str = "today") -> Dict[str, Any]:
    """Get a complete summary of logged carbon emissions, category breakdowns, and benchmark comparisons.

    Args:
        period: Time window to summarize. Supported values:
                'today' (last 24 hours), 'week' (last 7 days),
                'month' (last 30 days), or 'all' (entire session history).

    Returns:
        Dictionary containing `total_kg_co2e`, `by_category`, `activities`,
        `highest_impact_activity`, and `benchmark_comparisons`.
    """
    records = fetch_activities(period=period)
    total_co2 = round(sum(float(r["kg_co2e"]) for r in records), 3)

    by_category: Dict[str, Dict[str, Any]] = {}
    for r in records:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"kg_co2e": 0.0, "count": 0, "share_percent": 0.0}
        by_category[cat]["kg_co2e"] = round(by_category[cat]["kg_co2e"] + float(r["kg_co2e"]), 3)
        by_category[cat]["count"] += 1

    for cat, stats in by_category.items():
        if total_co2 > 0:
            stats["share_percent"] = round((stats["kg_co2e"] / total_co2) * 100.0, 1)

    highest_activity = None
    if records:
        top_rec = max(records, key=lambda x: float(x["kg_co2e"]))
        highest_activity = {
            "id": top_rec["id"],
            "category": top_rec["category"],
            "label": top_rec["label"],
            "kg_co2e": round(float(top_rec["kg_co2e"]), 3),
        }

    # Determine effective days in period for benchmark comparison
    p = period.lower().strip()
    if p in ("week", "weekly", "this_week", "this week", "7d"):
        # Count distinct dates with logs (at least 1)
        unique_days = len({r["logged_at"][:10] for r in records}) if records else 1
        days_divisor = max(1, unique_days)
    elif p in ("month", "monthly", "this_month", "this month", "30d"):
        unique_days = len({r["logged_at"][:10] for r in records}) if records else 1
        days_divisor = max(1, unique_days)
    else:
        days_divisor = 1

    daily_equivalent_kg = round(total_co2 / days_divisor, 3)

    comparisons: Dict[str, Dict[str, Any]] = {}
    for key, binfo in DAILY_BENCHMARKS_KG_CO2E.items():
        target = float(binfo["daily_kg_co2e"])
        diff = round(daily_equivalent_kg - target, 3)
        pct_of_benchmark = round((daily_equivalent_kg / target) * 100.0, 1) if target > 0 else 0.0
        comparisons[key] = {
            "benchmark_label": binfo["label"],
            "benchmark_daily_kg_co2e": target,
            "user_daily_kg_co2e": daily_equivalent_kg,
            "difference_kg_co2e": diff,
            "percent_of_benchmark": pct_of_benchmark,
            "status": "BELOW_BENCHMARK (Good)" if diff <= 0 else "ABOVE_BENCHMARK (Higher emissions)",
            "source": binfo["source"],
        }

    return {
        "status": "success",
        "period": period,
        "total_activities": len(records),
        "total_kg_co2e": total_co2,
        "daily_average_kg_co2e": daily_equivalent_kg,
        "by_category": by_category,
        "highest_impact_activity": highest_activity,
        "benchmark_comparisons": comparisons,
        "activities": [
            {
                "id": r["id"],
                "category": r["category"],
                "subcategory": r["subcategory"],
                "label": r["label"],
                "quantity": r["quantity"],
                "unit": r["unit"],
                "kg_co2e": round(float(r["kg_co2e"]), 3),
                "formula": r["formula"],
            }
            for r in records
        ],
    }


def clear_session_logs() -> Dict[str, Any]:
    """Clear all logged activities for the current user session to start fresh."""
    removed = clear_user_activities()
    return {
        "status": "success",
        "removed_count": removed,
        "message": f"Cleared {removed} logged activities from memory.",
    }
