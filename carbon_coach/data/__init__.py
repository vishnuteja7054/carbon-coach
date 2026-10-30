"""Emission factors and reference data for Carbon Coach."""
from .emission_factors import (
    TRAVEL_FACTORS,
    ELECTRICITY_GRID_FACTOR,
    APPLIANCE_POWER_KW,
    FOOD_FACTORS,
    WASTE_FACTORS,
    DAILY_BENCHMARKS_KG_CO2E,
    REDUCTION_RULES,
    resolve_travel_mode,
    resolve_appliance,
    resolve_meal_type,
    resolve_waste_type,
)

__all__ = [
    "TRAVEL_FACTORS",
    "ELECTRICITY_GRID_FACTOR",
    "APPLIANCE_POWER_KW",
    "FOOD_FACTORS",
    "WASTE_FACTORS",
    "DAILY_BENCHMARKS_KG_CO2E",
    "REDUCTION_RULES",
    "resolve_travel_mode",
    "resolve_appliance",
    "resolve_meal_type",
    "resolve_waste_type",
]
