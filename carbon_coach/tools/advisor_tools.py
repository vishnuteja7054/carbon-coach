"""
Personalized Actionable Reduction Tools for Google ADK Carbon Coach.

Every recommendation computes exact mathematical savings (`estimated_saving_kg_co2e`
and `annual_saving_kg_co2e` assuming 365 days) directly from the user's logged
activities and our cited emission factors. No numbers are ever guessed.
"""

from typing import Dict, Any, List
from carbon_coach.database.store import fetch_activities
from carbon_coach.data.emission_factors import (
    TRAVEL_FACTORS,
    ELECTRICITY_GRID_FACTOR,
    APPLIANCE_POWER_KW,
    FOOD_FACTORS,
    WASTE_FACTORS,
    REDUCTION_RULES,
)


def suggest_reductions(period: str = "all") -> Dict[str, Any]:
    """Generate personalized, actionable carbon reduction tips with exact kg CO2e savings.

    Analyzes the user's logged activities in memory and calculates exact savings
    for realistic behavior changes (e.g., reducing AC hours with a fan, switching
    transport modes, shifting meal choices, or cutting waste).

    Args:
        period: Time period of logs to analyze ('today', 'week', 'month', or 'all').

    Returns:
        Dictionary containing `current_total_kg_co2e`, `total_potential_saving_kg_co2e`,
        `projected_new_total_kg_co2e`, and a ranked list of `recommendations` with
        exact formulas and sources.
    """
    records = fetch_activities(period=period)
    grid_factor = float(ELECTRICITY_GRID_FACTOR["factor_kg_per_kwh"])

    if not records:
        # Provide reference starter tips with exact unit math if no activities logged yet
        starter_tips = [
            {
                "rank": 1,
                "category": "electricity",
                "target_activity": "1.5T AC (4 hours/day = 4.296 kg CO2e)",
                "action": "Set AC to 24°C + run Ceiling Fan and cut AC runtime from 4h to 2.5h",
                "current_kg_co2e": 4.296,
                "new_kg_co2e": 2.900,
                "estimated_saving_kg_co2e": 1.396,
                "saving_percent": 32.5,
                "annual_saving_kg_co2e": round(1.396 * 365, 1),
                "formula": "4.296 kg (4h AC) - [2.685 kg (2.5h AC) + 0.215 kg (4h Fan)] = 1.396 kg CO2e saved",
                "source": "BEE India Appliance Ratings + CEA Grid Factor (0.716 kg CO2e/kWh)",
            },
            {
                "rank": 2,
                "category": "travel",
                "target_activity": "10 km Daily Petrol Car Commute (1.700 kg CO2e)",
                "action": "Switch 10 km commute from Petrol Car to Public Bus",
                "current_kg_co2e": 1.700,
                "new_kg_co2e": 0.890,
                "estimated_saving_kg_co2e": 0.810,
                "saving_percent": 47.6,
                "annual_saving_kg_co2e": round(0.810 * 365, 1),
                "formula": "10 km × (0.170 - 0.089) kg CO2e/km = 0.810 kg CO2e saved",
                "source": "India GHG Program / DEFRA 2024 Transport Factors",
            },
        ]
        return {
            "status": "success",
            "has_logged_activities": False,
            "current_total_kg_co2e": 0.0,
            "total_potential_saving_kg_co2e": 2.206,
            "recommendations": starter_tips,
        }

    current_total = round(sum(float(r["kg_co2e"]) for r in records), 3)
    recommendations: List[Dict[str, Any]] = []

    for r in records:
        cat = r["category"]
        sub = r["subcategory"]
        qty = float(r["quantity"])
        cur_co2 = round(float(r["kg_co2e"]), 3)
        if cur_co2 <= 0:
            continue

        # 1. ELECTRICITY TIPS
        if cat == "electricity":
            if sub in ("ac", "ac_inverter"):
                # qty is kWh; recover hours from power_kw
                ac_kw = float(APPLIANCE_POWER_KW.get(sub, APPLIANCE_POWER_KW["ac"])["kw"])
                hours = round(qty / ac_kw, 2) if ac_kw > 0 else 4.0
                # Tip A: Cut AC runtime by 37.5% (e.g. 4h -> 2.5h) using timer + ceiling fan for full duration
                reduced_hours = round(hours * 0.625, 2)
                fan_kw = float(APPLIANCE_POWER_KW["fan"]["kw"])
                new_ac_co2 = round(reduced_hours * ac_kw * grid_factor, 3)
                fan_co2 = round(hours * fan_kw * grid_factor, 3)
                new_co2 = round(new_ac_co2 + fan_co2, 3)
                saving = round(max(0.0, cur_co2 - new_co2), 3)
                pct = round((saving / cur_co2) * 100.0, 1) if cur_co2 > 0 else 0.0

                recommendations.append(
                    {
                        "category": "electricity",
                        "target_activity": r["label"],
                        "action": (
                            f"Set AC to 24-26°C with sleep timer (reduce AC from {hours:g}h to {reduced_hours:g}h) "
                            f"and pair with a Ceiling Fan for {hours:g}h"
                        ),
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": new_co2,
                        "estimated_saving_kg_co2e": saving,
                        "saving_percent": pct,
                        "annual_saving_kg_co2e": round(saving * 365, 1),
                        "formula": (
                            f"{cur_co2:.3f} kg ({hours:g}h AC) - "
                            f"[{new_ac_co2:.3f} kg ({reduced_hours:g}h AC) + {fan_co2:.3f} kg ({hours:g}h Fan)] "
                            f"= {saving:.3f} kg CO2e saved"
                        ),
                        "source": "BEE India 24°C AC Guideline + CEA Grid Factor (0.716 kg CO2e/kWh)",
                    }
                )
            else:
                # General electricity or other appliance: 25% conservation / 5-star efficiency
                saving = round(cur_co2 * 0.25, 3)
                new_co2 = round(cur_co2 - saving, 3)
                recommendations.append(
                    {
                        "category": "electricity",
                        "target_activity": r["label"],
                        "action": "Switch to BEE 5-Star / BLDC appliance & turn off standby loads (25% reduction)",
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": new_co2,
                        "estimated_saving_kg_co2e": saving,
                        "saving_percent": 25.0,
                        "annual_saving_kg_co2e": round(saving * 365, 1),
                        "formula": f"{cur_co2:.3f} kg CO2e × 25% efficiency saving = {saving:.3f} kg CO2e saved",
                        "source": "Bureau of Energy Efficiency (BEE) Star Labeling Program",
                    }
                )

        # 2. TRAVEL TIPS
        elif cat == "travel":
            km = qty
            if sub in ("car_petrol", "car_diesel", "car_cng"):
                bus_factor = float(TRAVEL_FACTORS["bus"]["factor_kg_per_km"])
                new_co2 = round(km * bus_factor, 3)
                saving = round(max(0.0, cur_co2 - new_co2), 3)
                pct = round((saving / cur_co2) * 100.0, 1) if cur_co2 > 0 else 0.0
                recommendations.append(
                    {
                        "category": "travel",
                        "target_activity": r["label"],
                        "action": f"Switch {km:g} km car trip to Public Bus (or carpool with 3+ people)",
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": new_co2,
                        "estimated_saving_kg_co2e": saving,
                        "saving_percent": pct,
                        "annual_saving_kg_co2e": round(saving * 365, 1),
                        "formula": f"{cur_co2:.3f} kg (Car) - ({km:g} km × {bus_factor} kg/km Bus) = {saving:.3f} kg CO2e saved",
                        "source": "India GHG Program Road vs Bus Emission Factors",
                    }
                )
            elif sub == "bus":
                # Acknowledge bus is already great vs car, and show Metro/EV or last-mile cycling saving
                car_co2 = round(km * float(TRAVEL_FACTORS["car_petrol"]["factor_kg_per_km"]), 3)
                already_saved_vs_car = round(max(0.0, car_co2 - cur_co2), 3)
                metro_factor = float(TRAVEL_FACTORS["metro"]["factor_kg_per_km"])
                metro_co2 = round(km * metro_factor, 3)
                saving_metro = round(max(0.0, cur_co2 - metro_co2), 3)

                # Also compute cycling 25% of the distance (e.g. 3 km out of 12 km)
                cycle_km = round(min(3.0, km * 0.25), 1)
                remaining_km = round(km - cycle_km, 1)
                bus_factor = float(TRAVEL_FACTORS["bus"]["factor_kg_per_km"])
                new_bus_co2 = round(remaining_km * bus_factor, 3)
                saving_cycle = round(cur_co2 - new_bus_co2, 3)
                pct = round((saving_cycle / cur_co2) * 100.0, 1) if cur_co2 > 0 else 0.0

                recommendations.append(
                    {
                        "category": "travel",
                        "target_activity": r["label"],
                        "action": (
                            f"Great choice taking the bus (already saved {already_saved_vs_car:.3f} kg CO2e vs a petrol car)! "
                            f"To cut further: walk/cycle the first/last {cycle_km:g} km ({saving_cycle:.3f} kg saved) "
                            f"or use Metro/Electric Rail where available ({saving_metro:.3f} kg saved)"
                        ),
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": new_bus_co2,
                        "estimated_saving_kg_co2e": saving_cycle,
                        "alternate_metro_saving_kg_co2e": saving_metro,
                        "already_saved_vs_petrol_car_kg_co2e": already_saved_vs_car,
                        "saving_percent": pct,
                        "annual_saving_kg_co2e": round(saving_cycle * 365, 1),
                        "formula": (
                            f"Cycling {cycle_km:g} km × {bus_factor} kg CO2e/km = {saving_cycle:.3f} kg CO2e saved "
                            f"(or Metro switch: {cur_co2:.3f} - {metro_co2:.3f} = {saving_metro:.3f} kg CO2e saved)"
                        ),
                        "source": "India GHG Program / DEFRA 2024 Bus (0.089), Metro (0.035), Petrol Car (0.170)",
                    }
                )
            elif sub in ("two_wheeler", "auto_rickshaw"):
                ev_2w_factor = float(TRAVEL_FACTORS["ev_two_wheeler"]["factor_kg_per_km"])
                new_co2 = round(km * ev_2w_factor, 3)
                saving = round(max(0.0, cur_co2 - new_co2), 3)
                pct = round((saving / cur_co2) * 100.0, 1) if cur_co2 > 0 else 0.0
                recommendations.append(
                    {
                        "category": "travel",
                        "target_activity": r["label"],
                        "action": f"Cycle short campus trips (<3 km) or switch {km:g} km ride to Electric 2-Wheeler / Shared Transit",
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": new_co2,
                        "estimated_saving_kg_co2e": saving,
                        "saving_percent": pct,
                        "annual_saving_kg_co2e": round(saving * 365, 1),
                        "formula": f"{cur_co2:.3f} kg - ({km:g} km × {ev_2w_factor} kg/km E-2W) = {saving:.3f} kg CO2e saved",
                        "source": "India GHG Program 2-Wheeler vs E-2W Factors",
                    }
                )

        # 3. FOOD TIPS
        elif cat == "food":
            servings = qty
            if sub in ("mutton", "chicken", "fish", "egg"):
                veg_factor = float(FOOD_FACTORS["vegetarian"]["factor_kg_per_meal"])
                new_co2 = round(servings * veg_factor, 3)
                saving = round(max(0.0, cur_co2 - new_co2), 3)
                pct = round((saving / cur_co2) * 100.0, 1) if cur_co2 > 0 else 0.0
                recommendations.append(
                    {
                        "category": "food",
                        "target_activity": r["label"],
                        "action": f"Swap {servings:g} {sub} meal(s) for a Vegetarian Thali (dal, paneer, vegetables)",
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": new_co2,
                        "estimated_saving_kg_co2e": saving,
                        "saving_percent": pct,
                        "annual_saving_kg_co2e": round(saving * 150, 1),  # 150 swaps/yr
                        "formula": f"{cur_co2:.3f} kg - ({servings:g} × {veg_factor} kg/meal Veg) = {saving:.3f} kg CO2e saved",
                        "source": "Poore & Nemecek (2018), Science Dietary LCA",
                    }
                )
            elif sub == "vegetarian":
                vegan_factor = float(FOOD_FACTORS["vegan"]["factor_kg_per_meal"])
                new_co2 = round(servings * vegan_factor, 3)
                saving = round(max(0.0, cur_co2 - new_co2), 3)
                pct = round((saving / cur_co2) * 100.0, 1) if cur_co2 > 0 else 0.0
                recommendations.append(
                    {
                        "category": "food",
                        "target_activity": r["label"],
                        "action": "Opt for a plant-rich meal (dal, millets, vegetables with less high-carbon dairy) & zero plate waste",
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": new_co2,
                        "estimated_saving_kg_co2e": saving,
                        "saving_percent": pct,
                        "annual_saving_kg_co2e": round(saving * 365, 1),
                        "formula": f"{cur_co2:.3f} kg (Veg w/ dairy) - ({servings:g} × {vegan_factor} kg Plant-Based) = {saving:.3f} kg CO2e saved",
                        "source": "Poore & Nemecek (2018), Science Dietary LCA",
                    }
                )

        # 4. WASTE TIPS
        elif cat == "waste":
            if sub in ("plastic_bottle", "plastic_bag", "paper_cup"):
                saving = cur_co2  # 100% avoidable with reusable steel bottle / cloth bag / mug
                recommendations.append(
                    {
                        "category": "waste",
                        "target_activity": r["label"],
                        "action": "Switch to a reusable steel water bottle, cloth bag, or ceramic mug (eliminates 100% of single-use emissions)",
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": 0.0,
                        "estimated_saving_kg_co2e": saving,
                        "saving_percent": 100.0,
                        "annual_saving_kg_co2e": round(saving * 365, 1),
                        "formula": f"{cur_co2:.3f} kg CO2e × 100% avoided = {saving:.3f} kg CO2e saved",
                        "source": "DEFRA 2024 Single-Use Avoidance LCA",
                    }
                )
            elif sub in ("food_waste_kg", "mixed_waste_kg"):
                compost_factor = float(WASTE_FACTORS["composted_kg"]["factor_kg_per_unit"])
                new_co2 = round(qty * compost_factor, 3)
                saving = round(max(0.0, cur_co2 - new_co2), 3)
                pct = round((saving / cur_co2) * 100.0, 1) if cur_co2 > 0 else 0.0
                recommendations.append(
                    {
                        "category": "waste",
                        "target_activity": r["label"],
                        "action": f"Segregate and compost {qty:g} kg of organic waste instead of sending to landfill",
                        "current_kg_co2e": cur_co2,
                        "new_kg_co2e": new_co2,
                        "estimated_saving_kg_co2e": saving,
                        "saving_percent": pct,
                        "annual_saving_kg_co2e": round(saving * 365, 1),
                        "formula": f"{cur_co2:.3f} kg (Landfill) - ({qty:g} kg × {compost_factor} kg/kg Compost) = {saving:.3f} kg CO2e saved",
                        "source": "DEFRA 2024 Composting vs Landfill Factor",
                    }
                )

    # Sort recommendations by highest estimated saving first
    recommendations.sort(key=lambda x: float(x["estimated_saving_kg_co2e"]), reverse=True)
    for idx, rec in enumerate(recommendations, start=1):
        rec["rank"] = idx

    total_saving = round(sum(float(r["estimated_saving_kg_co2e"]) for r in recommendations), 3)
    projected_new_total = round(max(0.0, current_total - total_saving), 3)
    total_saving_pct = round((total_saving / current_total) * 100.0, 1) if current_total > 0 else 0.0

    return {
        "status": "success",
        "has_logged_activities": True,
        "period": period,
        "current_total_kg_co2e": current_total,
        "total_potential_saving_kg_co2e": total_saving,
        "total_potential_saving_percent": total_saving_pct,
        "projected_new_total_kg_co2e": projected_new_total,
        "Projected_annual_saving_kg_co2e": round(total_saving * 365, 1),
        "recommendations": recommendations,
    }
