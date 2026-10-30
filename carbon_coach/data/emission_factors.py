"""
Authoritative Emission Factors & Reference Constants for Carbon Coach.

Every emission factor in this module includes a documented scientific/governmental source:
1. Electricity Grid Factor: Central Electricity Authority (CEA), Ministry of Power, Govt. of India
   - CO2 Baseline Database for the Indian Power Sector (Version 19.0, 2023-24): 0.716 kg CO2e / kWh.
2. Transport Factors: India GHG Program (WRI India) & UK DESNZ / DEFRA 2024 Greenhouse Gas Conversion Factors.
3. Appliance Power Ratings: Bureau of Energy Efficiency (BEE), India typical residential/campus ratings.
4. Food & Diet Factors: Poore & Nemecek (2018), Science; Scarborough et al. (2023) & Indian dietary LCA studies.
5. Waste Factors: US EPA WARM Model & DEFRA 2024 Waste Disposal Factors.
"""

from typing import Dict, Any, Optional, Tuple

# ---------------------------------------------------------------------------
# 1. ELECTRICITY & APPLIANCES
# ---------------------------------------------------------------------------
ELECTRICITY_GRID_FACTOR: Dict[str, Any] = {
    "factor_kg_per_kwh": 0.716,
    "unit": "kWh",
    "source": "Central Electricity Authority (CEA) India CO2 Baseline Database v19.0 (0.716 kg CO2e/kWh)",
}

# Power ratings in kW (kilowatts) for common household/hostel/campus appliances
# Source: Bureau of Energy Efficiency (BEE) India standard load table
APPLIANCE_POWER_KW: Dict[str, Dict[str, Any]] = {
    "ac": {
        "kw": 1.50,
        "label": "Air Conditioner (1.5 Ton Split/Window AC)",
        "source": "BEE India Typical 1.5T AC average compressor consumption (1.50 kW)",
    },
    "ac_inverter": {
        "kw": 1.10,
        "label": "Inverter Air Conditioner (5-Star 1.5 Ton)",
        "source": "BEE India 5-Star Inverter AC average consumption (1.10 kW)",
    },
    "cooler": {
        "kw": 0.20,
        "label": "Desert / Room Air Cooler",
        "source": "BEE India Standard Evaporative Air Cooler (0.20 kW)",
    },
    "fan": {
        "kw": 0.075,
        "label": "Ceiling Fan (Standard Induction)",
        "source": "BEE India Standard Ceiling Fan (75W = 0.075 kW)",
    },
    "bldc_fan": {
        "kw": 0.030,
        "label": "BLDC Energy Efficient Ceiling Fan",
        "source": "BEE 5-Star Super-Efficient BLDC Fan (30W = 0.030 kW)",
    },
    "geyser": {
        "kw": 2.00,
        "label": "Electric Water Heater / Geyser",
        "source": "BEE India Standard Storage Water Heater (2000W = 2.00 kW)",
    },
    "laptop": {
        "kw": 0.065,
        "label": "Laptop Computer",
        "source": "ENERGY STAR Typical Notebook Computer (65W = 0.065 kW)",
    },
    "desktop": {
        "kw": 0.200,
        "label": "Desktop Computer + Monitor",
        "source": "ENERGY STAR Desktop PC + Monitor (200W = 0.200 kW)",
    },
    "light_led": {
        "kw": 0.010,
        "label": "LED Bulb / Tube Light",
        "source": "BEE India Standard LED Lamp (10W = 0.010 kW)",
    },
    "light_tube": {
        "kw": 0.040,
        "label": "Fluorescent Tube Light",
        "source": "BEE India Conventional Fluorescent Tube (40W = 0.040 kW)",
    },
    "refrigerator": {
        "kw": 0.150,
        "label": "Refrigerator (effective hourly running load)",
        "source": "BEE India Single/Double Door Fridge average hourly load (0.150 kW)",
    },
    "washing_machine": {
        "kw": 0.500,
        "label": "Washing Machine",
        "source": "BEE India Semi/Fully Automatic Washing Machine (0.500 kW)",
    },
    "iron": {
        "kw": 1.000,
        "label": "Electric Clothes Iron",
        "source": "BEE India Standard Dry/Steam Iron (1000W = 1.00 kW)",
    },
    "kettle": {
        "kw": 1.500,
        "label": "Electric Kettle / Induction Cooktop",
        "source": "Standard Residential Heating Appliance (1500W = 1.50 kW)",
    },
    "tv": {
        "kw": 0.100,
        "label": "LED Television",
        "source": "BEE India Typical 43-inch LED TV (100W = 0.100 kW)",
    },
}

APPLIANCE_ALIASES: Dict[str, str] = {
    "ac": "ac",
    "air conditioner": "ac",
    "air_conditioner": "ac",
    "split ac": "ac",
    "window ac": "ac",
    "inverter ac": "ac_inverter",
    "cooler": "cooler",
    "air cooler": "cooler",
    "fan": "fan",
    "ceiling fan": "fan",
    "table fan": "fan",
    "bldc fan": "bldc_fan",
    "geyser": "geyser",
    "water heater": "geyser",
    "heater": "geyser",
    "laptop": "laptop",
    "notebook": "laptop",
    "desktop": "desktop",
    "pc": "desktop",
    "computer": "desktop",
    "led": "light_led",
    "led bulb": "light_led",
    "bulb": "light_led",
    "light": "light_led",
    "tube light": "light_tube",
    "tubelight": "light_tube",
    "fridge": "refrigerator",
    "refrigerator": "refrigerator",
    "washing machine": "washing_machine",
    "washer": "washing_machine",
    "iron": "iron",
    "iron box": "iron",
    "kettle": "kettle",
    "induction": "kettle",
    "induction stove": "kettle",
    "tv": "tv",
    "television": "tv",
}


# ---------------------------------------------------------------------------
# 2. TRAVEL & TRANSPORT (kg CO2e per km)
# ---------------------------------------------------------------------------
TRAVEL_FACTORS: Dict[str, Dict[str, Any]] = {
    "bus": {
        "factor_kg_per_km": 0.089,
        "label": "Public / Campus Bus",
        "per_passenger": True,
        "source": "India GHG Program / DEFRA 2024 Average Local Bus (0.089 kg CO2e/passenger-km)",
    },
    "metro": {
        "factor_kg_per_km": 0.035,
        "label": "Metro / Suburban Electric Train",
        "per_passenger": True,
        "source": "India GHG Program Rail/Metro Transit (0.035 kg CO2e/passenger-km)",
    },
    "train": {
        "factor_kg_per_km": 0.041,
        "label": "Indian Railways Intercity Train",
        "per_passenger": True,
        "source": "India GHG Program National Rail (0.041 kg CO2e/passenger-km)",
    },
    "two_wheeler": {
        "factor_kg_per_km": 0.045,
        "label": "Petrol Bike / Scooter (Two-Wheeler)",
        "per_passenger": False,
        "source": "India GHG Program Road Transport - 2-Wheeler <150cc (0.045 kg CO2e/km)",
    },
    "ev_two_wheeler": {
        "factor_kg_per_km": 0.018,
        "label": "Electric Scooter / E-Bike",
        "per_passenger": False,
        "source": "CEA Grid Factor x 0.025 kWh/km E-2W consumption (0.018 kg CO2e/km)",
    },
    "auto_rickshaw": {
        "factor_kg_per_km": 0.065,
        "label": "Auto Rickshaw (CNG/LPG/Petrol)",
        "per_passenger": False,
        "source": "India GHG Program Three-Wheeler Auto Rickshaw (0.065 kg CO2e/km)",
    },
    "car_petrol": {
        "factor_kg_per_km": 0.170,
        "label": "Petrol Car / Cab",
        "per_passenger": False,
        "source": "DEFRA 2024 / India GHG Program Medium Petrol Car (0.170 kg CO2e/km)",
    },
    "car_diesel": {
        "factor_kg_per_km": 0.168,
        "label": "Diesel Car / SUV / Cab",
        "per_passenger": False,
        "source": "DEFRA 2024 / India GHG Program Medium Diesel Car (0.168 kg CO2e/km)",
    },
    "car_cng": {
        "factor_kg_per_km": 0.132,
        "label": "CNG Car / Cab",
        "per_passenger": False,
        "source": "India GHG Program CNG Passenger Car (0.132 kg CO2e/km)",
    },
    "car_ev": {
        "factor_kg_per_km": 0.085,
        "label": "Electric Car (Grid-charged in India)",
        "per_passenger": False,
        "source": "CEA Grid Factor x 0.12 kWh/km EV consumption (0.085 kg CO2e/km)",
    },
    "flight_domestic": {
        "factor_kg_per_km": 0.246,
        "label": "Domestic Flight (Economy)",
        "per_passenger": True,
        "source": "ICAO / DEFRA 2024 Short-Haul Domestic Flight with radiative forcing (0.246 kg CO2e/p-km)",
    },
    "bicycle": {
        "factor_kg_per_km": 0.0,
        "label": "Bicycle (Zero Tailpipe Emissions)",
        "per_passenger": True,
        "source": "IPCC Zero Direct Emissions Active Transport (0.000 kg CO2e/km)",
    },
    "walk": {
        "factor_kg_per_km": 0.0,
        "label": "Walking (Zero Emissions)",
        "per_passenger": True,
        "source": "IPCC Zero Direct Emissions Active Transport (0.000 kg CO2e/km)",
    },
}

TRAVEL_ALIASES: Dict[str, str] = {
    "bus": "bus",
    "city bus": "bus",
    "public bus": "bus",
    "college bus": "bus",
    "campus bus": "bus",
    "rtc": "bus",
    "apsrtc": "bus",
    "tsrtc": "bus",
    "metro": "metro",
    "subway": "metro",
    "local train": "metro",
    "train": "train",
    "rail": "train",
    "railway": "train",
    "bike": "two_wheeler",
    "motorbike": "two_wheeler",
    "motorcycle": "two_wheeler",
    "scooter": "two_wheeler",
    "scooty": "two_wheeler",
    "two wheeler": "two_wheeler",
    "two_wheeler": "two_wheeler",
    "2 wheeler": "two_wheeler",
    "ev bike": "ev_two_wheeler",
    "electric scooter": "ev_two_wheeler",
    "electric bike": "ev_two_wheeler",
    "ola scooter": "ev_two_wheeler",
    "ather": "ev_two_wheeler",
    "auto": "auto_rickshaw",
    "auto rickshaw": "auto_rickshaw",
    "auto_rickshaw": "auto_rickshaw",
    "rickshaw": "auto_rickshaw",
    "shared auto": "auto_rickshaw",
    "car": "car_petrol",
    "petrol car": "car_petrol",
    "car_petrol": "car_petrol",
    "cab": "car_petrol",
    "taxi": "car_petrol",
    "uber": "car_petrol",
    "ola": "car_petrol",
    "diesel car": "car_diesel",
    "car_diesel": "car_diesel",
    "suv": "car_diesel",
    "cng car": "car_cng",
    "car_cng": "car_cng",
    "ev": "car_ev",
    "electric car": "car_ev",
    "car_ev": "car_ev",
    "flight": "flight_domestic",
    "plane": "flight_domestic",
    "airplane": "flight_domestic",
    "flight_domestic": "flight_domestic",
    "cycle": "bicycle",
    "bicycle": "bicycle",
    "cycling": "bicycle",
    "walk": "walk",
    "walking": "walk",
    "foot": "walk",
}


# ---------------------------------------------------------------------------
# 3. FOOD & MEALS (kg CO2e per meal/serving)
# ---------------------------------------------------------------------------
FOOD_FACTORS: Dict[str, Dict[str, Any]] = {
    "vegan": {
        "factor_kg_per_meal": 0.65,
        "label": "Plant-Based / Vegan Meal (Dal, Rice, Roti, Vegetables, No Dairy)",
        "source": "Poore & Nemecek (2018) Science / Scarborough et al. (2023) Vegan Meal LCA (0.65 kg CO2e/meal)",
    },
    "vegetarian": {
        "factor_kg_per_meal": 1.10,
        "label": "Vegetarian Meal / Indian Veg Thali (includes Curd/Milk/Paneer)",
        "source": "Poore & Nemecek (2018) / Indian Vegetarian Thali LCA with dairy (1.10 kg CO2e/meal)",
    },
    "egg": {
        "factor_kg_per_meal": 1.45,
        "label": "Egg-Based Meal (Egg Curry / Omelette + Rice/Roti)",
        "source": "Poore & Nemecek (2018) Egg-inclusive meal LCA (1.45 kg CO2e/meal)",
    },
    "chicken": {
        "factor_kg_per_meal": 2.35,
        "label": "Poultry / Chicken Meal (Chicken Biryani / Chicken Curry Meal)",
        "source": "Poore & Nemecek (2018) Poultry Meal LCA (2.35 kg CO2e/meal)",
    },
    "fish": {
        "factor_kg_per_meal": 2.10,
        "label": "Fish / Seafood Meal",
        "source": "Poore & Nemecek (2018) Aquaculture/Fish Meal LCA (2.10 kg CO2e/meal)",
    },
    "mutton": {
        "factor_kg_per_meal": 6.50,
        "label": "Red Meat Meal (Mutton / Goat / Lamb / Beef)",
        "source": "Poore & Nemecek (2018) Ruminant Meat Meal LCA (6.50 kg CO2e/meal)",
    },
}

FOOD_ALIASES: Dict[str, str] = {
    "vegan": "vegan",
    "plant based": "vegan",
    "plant-based": "vegan",
    "veg": "vegetarian",
    "vegetarian": "vegetarian",
    "veg meal": "vegetarian",
    "veg thali": "vegetarian",
    "dal rice": "vegetarian",
    "sambar rice": "vegetarian",
    "idli": "vegan",
    "dosa": "vegetarian",
    "paneer": "vegetarian",
    "egg": "egg",
    "egg meal": "egg",
    "egg biryani": "egg",
    "omelette": "egg",
    "chicken": "chicken",
    "poultry": "chicken",
    "chicken biryani": "chicken",
    "chicken meal": "chicken",
    "chicken curry": "chicken",
    "non-veg": "chicken",
    "non veg": "chicken",
    "fish": "fish",
    "seafood": "fish",
    "fish curry": "fish",
    "mutton": "mutton",
    "mutton biryani": "mutton",
    "goat": "mutton",
    "lamb": "mutton",
    "beef": "mutton",
    "red meat": "mutton",
}


# ---------------------------------------------------------------------------
# 4. WASTE & RECYCLING (kg CO2e per unit/kg)
# ---------------------------------------------------------------------------
WASTE_FACTORS: Dict[str, Dict[str, Any]] = {
    "plastic_bottle": {
        "factor_kg_per_unit": 0.082,
        "unit": "item",
        "label": "Single-Use PET Plastic Bottle (500ml-1L)",
        "source": "DEFRA / PlasticsEurope PET Bottle Cradle-to-Grave LCA (0.082 kg CO2e/bottle)",
    },
    "plastic_bag": {
        "factor_kg_per_unit": 0.033,
        "unit": "item",
        "label": "Single-Use Plastic Carry Bag / Packaging",
        "source": "UK Environment Agency Carrier Bag LCA (0.033 kg CO2e/bag)",
    },
    "paper_cup": {
        "factor_kg_per_unit": 0.045,
        "unit": "item",
        "label": "Disposable Paper/Plastic-lined Tea/Coffee Cup",
        "source": "VTT Technical Research Disposable Cup LCA (0.045 kg CO2e/cup)",
    },
    "food_waste_kg": {
        "factor_kg_per_unit": 0.850,
        "unit": "kg",
        "label": "Food Waste Sent to Landfill (Methane-producing)",
        "source": "DEFRA 2024 Organic Food Waste Landfill Factor (0.850 kg CO2e/kg)",
    },
    "mixed_waste_kg": {
        "factor_kg_per_unit": 0.580,
        "unit": "kg",
        "label": "General Mixed Municipal Solid Waste (Landfill)",
        "source": "DEFRA 2024 Municipal Solid Waste Landfill Factor (0.580 kg CO2e/kg)",
    },
    "composted_kg": {
        "factor_kg_per_unit": 0.040,
        "unit": "kg",
        "label": "Composted Organic Waste (Low Emissions)",
        "source": "DEFRA 2024 Organic Waste Composting Factor (0.040 kg CO2e/kg)",
    },
    "recycled_kg": {
        "factor_kg_per_unit": 0.021,
        "unit": "kg",
        "label": "Recycled Paper/Plastic/Metal Waste",
        "source": "DEFRA 2024 Closed-Loop Recycling Process Factor (0.021 kg CO2e/kg)",
    },
}

WASTE_ALIASES: Dict[str, str] = {
    "plastic bottle": "plastic_bottle",
    "plastic_bottle": "plastic_bottle",
    "water bottle": "plastic_bottle",
    "bottle": "plastic_bottle",
    "pet bottle": "plastic_bottle",
    "plastic bag": "plastic_bag",
    "plastic_bag": "plastic_bag",
    "polythene": "plastic_bag",
    "carry bag": "plastic_bag",
    "paper cup": "paper_cup",
    "paper_cup": "paper_cup",
    "disposable cup": "paper_cup",
    "tea cup": "paper_cup",
    "food waste": "food_waste_kg",
    "food_waste": "food_waste_kg",
    "food_waste_kg": "food_waste_kg",
    "leftover food": "food_waste_kg",
    "mixed waste": "mixed_waste_kg",
    "mixed_waste": "mixed_waste_kg",
    "mixed_waste_kg": "mixed_waste_kg",
    "garbage": "mixed_waste_kg",
    "trash": "mixed_waste_kg",
    "general waste": "mixed_waste_kg",
    "compost": "composted_kg",
    "composted": "composted_kg",
    "composted_kg": "composted_kg",
    "recycle": "recycled_kg",
    "recycled": "recycled_kg",
    "recycled_kg": "recycled_kg",
}


# ---------------------------------------------------------------------------
# 5. BENCHMARKS FOR COMPARISON (kg CO2e per person per day)
# ---------------------------------------------------------------------------
DAILY_BENCHMARKS_KG_CO2E: Dict[str, Dict[str, Any]] = {
    "campus_student_target": {
        "daily_kg_co2e": 3.50,
        "label": "Green Student Daily Target",
        "source": "UN Environment Programme (UNEP) Green Campus Benchmark (3.50 kg CO2e/day)",
    },
    "india_average": {
        "daily_kg_co2e": 5.48,
        "label": "India Per-Capita Daily Average (~2.0 tonnes/year)",
        "source": "IEA / Global Carbon Project India Per-Capita Emissions (5.48 kg CO2e/day)",
    },
    "paris_2030_target": {
        "daily_kg_co2e": 6.30,
        "label": "1.5°C Paris Agreement 2030 Global Target (~2.3 tonnes/year)",
        "source": "IPCC / Oxfam 1.5°C Lifestyle Carbon Budget (6.30 kg CO2e/day)",
    },
    "global_average": {
        "daily_kg_co2e": 12.88,
        "label": "Global Per-Capita Daily Average (~4.7 tonnes/year)",
        "source": "IEA / EDGAR Global Per-Capita GHG Emissions (12.88 kg CO2e/day)",
    },
}


# ---------------------------------------------------------------------------
# 6. DETERMINISTIC REDUCTION RULES
# ---------------------------------------------------------------------------
REDUCTION_RULES = [
    {
        "id": "ac_to_fan_or_temp",
        "category": "electricity",
        "trigger_subcategories": ["ac", "ac_inverter", "direct_kwh"],
        "title": "Raise AC thermostat to 24-26°C + use Ceiling Fan, or cut AC runtime by 25%",
        "saving_fraction": 0.28,
        "explanation": "BEE India estimates every 1°C increase in AC temperature (from 20°C to 24°C) saves ~6% electricity, and pairing with a fan reduces compressor runtime by ~28%.",
        "source": "Bureau of Energy Efficiency (BEE) India '24°C Default AC Campaign'",
    },
    {
        "id": "car_to_bus_or_metro",
        "category": "travel",
        "trigger_subcategories": ["car_petrol", "car_diesel", "car_cng"],
        "title": "Switch commute from Solo Car/Cab to Bus or Metro",
        "saving_fraction": 0.476,  # (0.170 - 0.089) / 0.170 = 47.6% for bus
        "explanation": "Switching from a petrol car (0.170 kg/km) to a bus (0.089 kg/km) cuts travel emissions by 47.6%, or by 79.4% if switching to metro/train (0.035 kg/km).",
        "source": "India GHG Program Road vs Public Transit Factor Comparison",
    },
    {
        "id": "two_wheeler_to_bus_or_cycle",
        "category": "travel",
        "trigger_subcategories": ["two_wheeler", "auto_rickshaw"],
        "title": "Walk or cycle short trips (<3 km) and share rides",
        "saving_fraction": 0.35,
        "explanation": "Replacing short campus/market bike or auto trips with cycling or walking eliminates 100% of emissions on those legs (average 35% daily travel reduction).",
        "source": "IPCC Active Mobility Mitigation Potential",
    },
    {
        "id": "bus_to_metro_or_shared",
        "category": "travel",
        "trigger_subcategories": ["bus"],
        "title": "Combine errands or use Bicycle/Metro for short connectors",
        "saving_fraction": 0.20,
        "explanation": "Bus travel is already low-carbon (0.089 kg/km vs 0.170 kg/km by car). Cycling the first/last 2 km reduces remaining trip emissions by ~20%.",
        "source": "India GHG Program Transit Optimization",
    },
    {
        "id": "meat_to_veg",
        "category": "food",
        "trigger_subcategories": ["mutton", "chicken", "fish", "egg"],
        "title": "Swap Non-Veg meals for Vegetarian or Plant-Based Indian meals",
        "saving_fraction": 0.532,  # (2.35 - 1.10) / 2.35 = 53.2%
        "explanation": "Switching a chicken meal (2.35 kg CO2e) to an Indian vegetarian thali (1.10 kg CO2e) saves 1.25 kg CO2e per meal (53.2%), and from mutton (6.50 kg) saves 5.40 kg CO2e (83.1%).",
        "source": "Poore & Nemecek (2018), Science",
    },
    {
        "id": "veg_to_plant_based",
        "category": "food",
        "trigger_subcategories": ["vegetarian"],
        "title": "Reduce food waste on plate & include more low-dairy plant proteins (dal/millets)",
        "saving_fraction": 0.25,
        "explanation": "Shifting one dairy-heavy meal toward dal/millets/plant-based (0.65 kg vs 1.10 kg CO2e) cuts meal emissions by ~25-40%.",
        "source": "Poore & Nemecek (2018), Science",
    },
    {
        "id": "zero_single_use_waste",
        "category": "waste",
        "trigger_subcategories": ["plastic_bottle", "plastic_bag", "paper_cup", "food_waste_kg", "mixed_waste_kg"],
        "title": "Carry a reusable steel bottle/bag & segregate organic waste for composting",
        "saving_fraction": 0.90,
        "explanation": "Composting food waste (0.04 kg/kg vs 0.85 kg/kg in landfill) and using a reusable bottle eliminates ~90% of waste-related emissions.",
        "source": "DEFRA 2024 Waste Hierarchy Factors",
    },
]


# ---------------------------------------------------------------------------
# HELPER RESOLVERS
# ---------------------------------------------------------------------------
def resolve_travel_mode(mode: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    key = mode.strip().lower().replace("-", " ")
    canonical = TRAVEL_ALIASES.get(key) or TRAVEL_ALIASES.get(key.replace(" ", "_"))
    if not canonical and key in TRAVEL_FACTORS:
        canonical = key
    if not canonical:
        # Substring fallback
        for alias, target in TRAVEL_ALIASES.items():
            if alias in key or key in alias:
                canonical = target
                break
    if canonical and canonical in TRAVEL_FACTORS:
        return canonical, TRAVEL_FACTORS[canonical]
    return None, None


def resolve_appliance(appliance: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    key = appliance.strip().lower().replace("-", " ")
    canonical = APPLIANCE_ALIASES.get(key) or APPLIANCE_ALIASES.get(key.replace(" ", "_"))
    if not canonical and key in APPLIANCE_POWER_KW:
        canonical = key
    if not canonical:
        for alias, target in APPLIANCE_ALIASES.items():
            if alias in key or key in alias:
                canonical = target
                break
    if canonical and canonical in APPLIANCE_POWER_KW:
        return canonical, APPLIANCE_POWER_KW[canonical]
    return None, None


def resolve_meal_type(meal_type: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    key = meal_type.strip().lower().replace("-", " ")
    canonical = FOOD_ALIASES.get(key) or FOOD_ALIASES.get(key.replace(" ", "_"))
    if not canonical and key in FOOD_FACTORS:
        canonical = key
    if not canonical:
        for alias, target in FOOD_ALIASES.items():
            if alias in key or key in alias:
                canonical = target
                break
    if canonical and canonical in FOOD_FACTORS:
        return canonical, FOOD_FACTORS[canonical]
    return None, None


def resolve_waste_type(waste_type: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    key = waste_type.strip().lower().replace("-", " ")
    canonical = WASTE_ALIASES.get(key) or WASTE_ALIASES.get(key.replace(" ", "_"))
    if not canonical and key in WASTE_FACTORS:
        canonical = key
    if not canonical:
        for alias, target in WASTE_ALIASES.items():
            if alias in key or key in alias:
                canonical = target
                break
    if canonical and canonical in WASTE_FACTORS:
        return canonical, WASTE_FACTORS[canonical]
    return None, None
