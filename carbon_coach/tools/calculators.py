"""
Deterministic Emission Calculator Tools for Google ADK Carbon Coach.

Every function computes exact kg CO2e values using cited emission factors from
`carbon_coach.data.emission_factors` and automatically logs the entry to the
SQLite session memory (unless `auto_log=False`).
"""

from typing import Dict, Any, Optional
from carbon_coach.data.emission_factors import (
    TRAVEL_FACTORS,
    ELECTRICITY_GRID_FACTOR,
    APPLIANCE_POWER_KW,
    FOOD_FACTORS,
    WASTE_FACTORS,
    resolve_travel_mode,
    resolve_appliance,
    resolve_meal_type,
    resolve_waste_type,
)
from carbon_coach.database.store import insert_activity


def calculate_travel_emissions(
    mode: str,
    km: float,
    passengers: int = 1,
    auto_log: bool = True,
) -> Dict[str, Any]:
    """Calculate carbon emissions (in kg CO2e) for a travel or commute activity.

    Args:
        mode: Mode of transport. Supported values include 'bus', 'metro', 'train',
              'two_wheeler' (bike/scooter), 'ev_two_wheeler', 'auto_rickshaw',
              'car_petrol' (or 'car'/'cab'), 'car_diesel', 'car_cng', 'car_ev',
              'flight_domestic', 'bicycle', 'walk'.
        km: Distance travelled in kilometers (must be >= 0).
        passengers: Number of people sharing the vehicle (default 1). For private
                    vehicles (car, bike, auto), emissions are divided by passengers.
        auto_log: Whether to automatically save this activity to the user's memory log.

    Returns:
        Dictionary containing exact `kg_co2e`, `formula`, `emission_factor`, `source`,
        and `logged_entry`.
    """
    if km < 0:
        return {
            "status": "error",
            "error": "Distance (km) cannot be negative.",
        }

    canonical_mode, info = resolve_travel_mode(mode)
    if not canonical_mode or not info:
        return {
            "status": "error",
            "error": f"Unrecognized transport mode '{mode}'. Supported modes: {', '.join(TRAVEL_FACTORS.keys())}",
            "supported_modes": list(TRAVEL_FACTORS.keys()),
        }

    pax = max(1, int(passengers or 1))
    base_factor = float(info["factor_kg_per_km"])

    if info.get("per_passenger", True):
        effective_factor = base_factor
        raw_co2 = float(km) * effective_factor
        formula = f"{km} km × {base_factor} kg CO2e/p-km = {raw_co2:.3f} kg CO2e"
    else:
        effective_factor = base_factor / pax
        raw_co2 = float(km) * effective_factor
        if pax > 1:
            formula = f"({km} km × {base_factor} kg CO2e/km) / {pax} passengers = {raw_co2:.3f} kg CO2e"
        else:
            formula = f"{km} km × {base_factor} kg CO2e/km = {raw_co2:.3f} kg CO2e"

    kg_co2e = round(raw_co2, 3)

    logged_entry = None
    if auto_log and km > 0:
        logged_entry = insert_activity(
            category="travel",
            subcategory=canonical_mode,
            label=f"{info['label']} ({km} km)",
            quantity=float(km),
            unit="km",
            kg_co2e=kg_co2e,
            formula=formula,
            source=info["source"],
        )

    return {
        "status": "success",
        "category": "travel",
        "mode": canonical_mode,
        "mode_label": info["label"],
        "km": round(float(km), 2),
        "passengers": pax,
        "emission_factor_kg_per_km": round(effective_factor, 4),
        "kg_co2e": kg_co2e,
        "formula": formula,
        "source": info["source"],
        "logged": bool(logged_entry),
        "activity_id": logged_entry["id"] if logged_entry else None,
    }


def calculate_electricity_emissions(
    kwh: Optional[float] = None,
    appliance: Optional[str] = None,
    hours: Optional[float] = None,
    appliance_count: int = 1,
    auto_log: bool = True,
) -> Dict[str, Any]:
    """Calculate carbon emissions (in kg CO2e) from electricity usage.

    Accepts EITHER direct electricity consumption in `kwh` OR an `appliance` name
    with duration in `hours` (e.g., appliance='ac', hours=4).

    Args:
        kwh: Direct electricity consumed in kilowatt-hours (kWh). Leave 0 or None
             if specifying `appliance` and `hours`.
        appliance: Name of electrical appliance used, e.g. 'ac' (1.5kW), 'ac_inverter' (1.1kW),
                   'cooler' (0.2kW), 'fan' (0.075kW), 'bldc_fan' (0.03kW), 'geyser' (2.0kW),
                   'laptop' (0.065kW), 'desktop' (0.2kW), 'light_led' (0.01kW),
                   'refrigerator' (0.15kW), 'washing_machine' (0.5kW), 'iron' (1.0kW),
                   'kettle' (1.5kW), 'tv' (0.1kW).
        hours: Number of hours the appliance was used.
        appliance_count: Number of identical appliances used simultaneously (default 1).
        auto_log: Whether to automatically log this activity to the user's memory.

    Returns:
        Dictionary with computed `kwh`, `kg_co2e`, `formula`, `source`, and `activity_id`.
    """
    grid_factor = float(ELECTRICITY_GRID_FACTOR["factor_kg_per_kwh"])
    grid_source = ELECTRICITY_GRID_FACTOR["source"]
    count = max(1, int(appliance_count or 1))

    # Case 1: Appliance + hours provided
    if appliance and str(appliance).strip():
        canonical_app, app_info = resolve_appliance(str(appliance))
        if not canonical_app or not app_info:
            return {
                "status": "error",
                "error": f"Unknown appliance '{appliance}'. Supported appliances: {', '.join(APPLIANCE_POWER_KW.keys())}",
                "supported_appliances": list(APPLIANCE_POWER_KW.keys()),
            }
        hrs = float(hours if hours is not None else 1.0)
        if hrs < 0:
            return {"status": "error", "error": "Usage hours cannot be negative."}

        power_kw = float(app_info["kw"])
        computed_kwh = round(power_kw * hrs * count, 4)
        raw_co2 = computed_kwh * grid_factor
        kg_co2e = round(raw_co2, 3)

        if count > 1:
            formula = (
                f"{count} × {power_kw} kW ({app_info['label']}) × {hrs} hrs = {computed_kwh:.3f} kWh; "
                f"{computed_kwh:.3f} kWh × {grid_factor} kg CO2e/kWh = {kg_co2e:.3f} kg CO2e"
            )
        else:
            formula = (
                f"{power_kw} kW ({app_info['label']}) × {hrs} hrs = {computed_kwh:.3f} kWh; "
                f"{computed_kwh:.3f} kWh × {grid_factor} kg CO2e/kWh = {kg_co2e:.3f} kg CO2e"
            )
        combined_source = f"{app_info['source']} + {grid_source}"
        subcategory = canonical_app
        label = f"{app_info['label']} ({hrs} hrs = {computed_kwh:.2f} kWh)"

    # Case 2: Direct kWh provided
    elif kwh is not None and float(kwh) >= 0:
        computed_kwh = round(float(kwh), 4)
        raw_co2 = computed_kwh * grid_factor
        kg_co2e = round(raw_co2, 3)
        formula = f"{computed_kwh} kWh × {grid_factor} kg CO2e/kWh = {kg_co2e:.3f} kg CO2e"
        combined_source = grid_source
        subcategory = "direct_kwh"
        label = f"Grid Electricity ({computed_kwh:.2f} kWh)"
        hrs = None
    else:
        return {
            "status": "error",
            "error": "Please provide either positive `kwh` OR both `appliance` and `hours`.",
        }

    logged_entry = None
    if auto_log and computed_kwh > 0:
        logged_entry = insert_activity(
            category="electricity",
            subcategory=subcategory,
            label=label,
            quantity=computed_kwh,
            unit="kWh",
            kg_co2e=kg_co2e,
            formula=formula,
            source=combined_source,
        )

    return {
        "status": "success",
        "category": "electricity",
        "subcategory": subcategory,
        "label": label,
        "hours": hrs,
        "kwh": round(computed_kwh, 3),
        "grid_factor_kg_per_kwh": grid_factor,
        "kg_co2e": kg_co2e,
        "formula": formula,
        "source": combined_source,
        "logged": bool(logged_entry),
        "activity_id": logged_entry["id"] if logged_entry else None,
    }


def calculate_food_emissions(
    meal_type: str,
    servings: float = 1.0,
    auto_log: bool = True,
) -> Dict[str, Any]:
    """Calculate carbon emissions (in kg CO2e) for food or meals consumed.

    Args:
        meal_type: Type of meal eaten. Supported values: 'vegan' (plant-based, idli, dal-rice),
                   'vegetarian' (Indian veg thali, paneer, curd/dairy meal), 'egg' (egg meal/omelette),
                   'chicken' (chicken biryani/curry), 'fish' (seafood meal), 'mutton' (red meat/goat/beef).
        servings: Number of meals or servings consumed (default 1.0).
        auto_log: Whether to automatically save this meal to the user's memory log.

    Returns:
        Dictionary containing `kg_co2e`, `formula`, `source`, and `activity_id`.
    """
    if servings < 0:
        return {"status": "error", "error": "Servings cannot be negative."}

    canonical_meal, info = resolve_meal_type(meal_type)
    if not canonical_meal or not info:
        return {
            "status": "error",
            "error": f"Unknown meal_type '{meal_type}'. Supported meal types: {', '.join(FOOD_FACTORS.keys())}",
            "supported_meal_types": list(FOOD_FACTORS.keys()),
        }

    factor = float(info["factor_kg_per_meal"])
    srv = float(servings)
    raw_co2 = srv * factor
    kg_co2e = round(raw_co2, 3)
    formula = f"{srv} meal(s) × {factor} kg CO2e/meal = {kg_co2e:.3f} kg CO2e"

    logged_entry = None
    if auto_log and srv > 0:
        logged_entry = insert_activity(
            category="food",
            subcategory=canonical_meal,
            label=f"{info['label']} ({srv:g} serving)",
            quantity=srv,
            unit="meal",
            kg_co2e=kg_co2e,
            formula=formula,
            source=info["source"],
        )

    return {
        "status": "success",
        "category": "food",
        "meal_type": canonical_meal,
        "meal_label": info["label"],
        "servings": srv,
        "emission_factor_kg_per_meal": factor,
        "kg_co2e": kg_co2e,
        "formula": formula,
        "source": info["source"],
        "logged": bool(logged_entry),
        "activity_id": logged_entry["id"] if logged_entry else None,
    }


def calculate_waste_emissions(
    waste_type: str,
    quantity: float = 1.0,
    auto_log: bool = True,
) -> Dict[str, Any]:
    """Calculate carbon emissions (in kg CO2e) for waste generated or disposed.

    Args:
        waste_type: Type of waste item or stream. Supported values:
                    'plastic_bottle' (per item), 'plastic_bag' (per item),
                    'paper_cup' (per item), 'food_waste_kg' (per kg),
                    'mixed_waste_kg' (per kg), 'composted_kg' (per kg),
                    'recycled_kg' (per kg).
        quantity: Count of items (for bottles/bags/cups) or weight in kg (for waste streams).
        auto_log: Whether to automatically save this waste activity to memory.

    Returns:
        Dictionary containing `kg_co2e`, `formula`, `source`, and `activity_id`.
    """
    if quantity < 0:
        return {"status": "error", "error": "Quantity cannot be negative."}

    canonical_waste, info = resolve_waste_type(waste_type)
    if not canonical_waste or not info:
        return {
            "status": "error",
            "error": f"Unknown waste_type '{waste_type}'. Supported types: {', '.join(WASTE_FACTORS.keys())}",
            "supported_waste_types": list(WASTE_FACTORS.keys()),
        }

    factor = float(info["factor_kg_per_unit"])
    qty = float(quantity)
    unit = info["unit"]
    raw_co2 = qty * factor
    kg_co2e = round(raw_co2, 3)
    formula = f"{qty:g} {unit}(s) × {factor} kg CO2e/{unit} = {kg_co2e:.3f} kg CO2e"

    logged_entry = None
    if auto_log and qty > 0:
        logged_entry = insert_activity(
            category="waste",
            subcategory=canonical_waste,
            label=f"{info['label']} ({qty:g} {unit})",
            quantity=qty,
            unit=unit,
            kg_co2e=kg_co2e,
            formula=formula,
            source=info["source"],
        )

    return {
        "status": "success",
        "category": "waste",
        "waste_type": canonical_waste,
        "waste_label": info["label"],
        "quantity": qty,
        "unit": unit,
        "emission_factor_kg_per_unit": factor,
        "kg_co2e": kg_co2e,
        "formula": formula,
        "source": info["source"],
        "logged": bool(logged_entry),
        "activity_id": logged_entry["id"] if logged_entry else None,
    }
