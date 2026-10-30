"""
FastAPI Backend for Carbon Coach (Bridging the React MorphOrb UI to Google ADK).

Endpoints:
- POST /api/chat     -> Executes Google ADK `root_agent` (or deterministic tool pipeline
                        if GOOGLE_API_KEY is not yet set) and returns exact tool traces,
                        concise orb answer text, session summary, and reduction tips.
- GET  /api/summary  -> Returns current session summary & reduction recommendations.
- POST /api/reset    -> Clears logged activities for a fresh demo run.
"""

import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from carbon_coach.runner import run_carbon_coach_turn
from carbon_coach.tools import (
    calculate_travel_emissions,
    calculate_electricity_emissions,
    calculate_food_emissions,
    calculate_waste_emissions,
    get_summary,
    suggest_reductions,
    clear_session_logs,
)

_ROOT_DIR = Path(__file__).resolve().parent
load_dotenv(_ROOT_DIR / ".env", override=False)
load_dotenv(_ROOT_DIR / ".env.example", override=False)

app = FastAPI(
    title="Carbon Coach ADK API",
    description="DevFest 2026 Carbon Coach Agent powered by Google ADK & Deterministic Tools",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default_user"
    session_id: str = "default_session"


def _has_valid_api_key() -> bool:
    load_dotenv(_ROOT_DIR / ".env", override=False)
    load_dotenv(_ROOT_DIR / ".env.example", override=False)
    key = os.environ.get("GOOGLE_API_KEY", "").strip()
    return bool(key and key != "your_gemini_api_key_here" and len(key) > 15)


def _clean_markdown_for_orb(text: str) -> str:
    """Strip raw markdown symbols (###, **, ---, `) so word-by-word orb rendering is clean."""
    cleaned = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    cleaned = re.sub(r"^---+\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.replace("**", "").replace("`", "")
    cleaned = re.sub(r"^\s*[-*]\s+", "• ", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{2,}", "  ", cleaned)
    return cleaned.strip()


def _detect_language(text: str) -> str:
    # Telugu Unicode range: 0C00–0C7F
    if any("\u0c00" <= ch <= "\u0c7f" for ch in text):
        return "te"
    # Devanagari (Hindi) Unicode range: 0900–097F
    if any("\u0900" <= ch <= "\u097f" for ch in text):
        return "hi"
    return "en"


def _run_deterministic_tool_pipeline(message: str) -> Dict[str, Any]:
    """
    Executes the exact Carbon Coach Python tools deterministically from natural
    language input (supporting English, Telugu, and Hindi) when running without
    a live Gemini API key or if the network is offline during a live demo.
    """
    text_lower = message.lower()
    lang = _detect_language(message)
    tool_trace: List[Dict[str, Any]] = []
    logged_items: List[str] = []

    # 1. Parse Travel patterns (English + Telugu + Hindi keywords)
    travel_patterns = [
        (r"(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometre|కి\.మీ|కిమీ|किमी|किलोमीटर)[^\d]{0,25}?(bus|బస్సు|बस)", "bus"),
        (r"(bus|బస్సు|बस)[^\d]{0,25}?(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometre|కి\.మీ|కిమీ|किमी|किलोमीटर)", "bus_rev"),
        (r"(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometre|కి\.మీ|కిమీ|किमी|किलोमीटर)[^\d]{0,25}?(car|cab|taxi|uber|ola|కారు|कार)", "car_petrol"),
        (r"(car|cab|taxi|uber|ola|కారు|कार)[^\d]{0,25}?(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometre|కి\.మీ|కిమీ|किमी|किलोमीटर)", "car_rev"),
        (r"(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometre|కి\.మీ|కిమీ|किमी|किलोमीटर)[^\d]{0,25}?(bike|scooter|scooty|two wheeler|motorbike|బైక్|बाइक|स्कूटर)", "two_wheeler"),
        (r"(bike|scooter|scooty|two wheeler|motorbike|బైక్|बाइक|स्कूटर)[^\d]{0,25}?(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometre|కి\.మీ|కిమీ|किमी|किलोमीटर)", "bike_rev"),
        (r"(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometre|కి\.మీ|కిమీ|किमी|किलोमीटर)[^\d]{0,25}?(metro|train|rail|మెట్రో|రైలు|मेट्रो|ट्रेन)", "metro"),
        (r"(\d+(?:\.\d+)?)\s*(?:km|kilometer|kilometre|కి\.మీ|కిమీ|किमी|किलोमीटर)[^\d]{0,25}?(auto|rickshaw|ఆటో|ऑटो)", "auto_rickshaw"),
    ]

    matched_modes = set()
    for pat, mode_key in travel_patterns:
        for m in re.finditer(pat, text_lower):
            if mode_key.endswith("_rev"):
                km_val = float(m.group(2))
                actual_mode = "bus" if "bus" in mode_key else ("car_petrol" if "car" in mode_key else "two_wheeler")
            else:
                km_val = float(m.group(1))
                actual_mode = mode_key
            sig = (actual_mode, km_val)
            if sig in matched_modes:
                continue
            matched_modes.add(sig)
            args = {"mode": actual_mode, "km": km_val}
            tool_trace.append({"type": "tool_call", "agent": "tracker_agent", "tool_name": "calculate_travel_emissions", "args": args})
            res = calculate_travel_emissions(**args)
            tool_trace.append({"type": "tool_result", "agent": "tracker_agent", "tool_name": "calculate_travel_emissions", "result": res})
            if res.get("status") == "success":
                logged_items.append(f"{res['mode_label']} ({km_val:g} km): {res['kg_co2e']} kg CO₂e [{res['formula']}]")

    # 2. Parse Electricity / Appliance patterns (AC, Fan, Geyser, Laptop, or direct kWh)
    elec_patterns = [
        (r"(?:ac|air conditioner|ఏసీ|एसी)[^\d]{0,25}?(\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours|గంటలు|గంట|घंटे|घंटा)", "ac", False),
        (r"(\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours|గంటలు|గంట|घंटे|घंटा)[^\d]{0,25}?(?:ac|air conditioner|ఏసీ|एसी)", "ac", True),
        (r"(?:fan|ceiling fan|ఫ్యాన్|पंखा)[^\d]{0,25}?(\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours|గంటలు|घंटे)", "fan", False),
        (r"(\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours|గంటలు|घंटे)[^\d]{0,25}?(?:fan|ceiling fan|ఫ్యాన్|पंखा)", "fan", True),
        (r"(?:geyser|water heater|గీజర్|गीजर)[^\d]{0,25}?(\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours|గంటలు|घंटे)", "geyser", False),
        (r"(\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours|గంటలు|घंटे)[^\d]{0,25}?(?:geyser|water heater|గీజర్|गीजर)", "geyser", True),
        (r"(?:laptop|computer|ల్యాప్‌టాప్|लैपटॉप)[^\d]{0,25}?(\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours|గంటలు|घंटे)", "laptop", False),
        (r"(\d+(?:\.\d+)?)\s*(?:hr|hrs|hour|hours|గంటలు|घंटे)[^\d]{0,25}?(?:laptop|computer|ల్యాప్‌టాప్|लैपटॉप)", "laptop", True),
    ]
    matched_apps = set()
    for pat, app_name, num_first in elec_patterns:
        for m in re.finditer(pat, text_lower):
            hrs_val = float(m.group(1))
            sig = (app_name, hrs_val)
            if sig in matched_apps:
                continue
            matched_apps.add(sig)
            args = {"appliance": app_name, "hours": hrs_val}
            tool_trace.append({"type": "tool_call", "agent": "tracker_agent", "tool_name": "calculate_electricity_emissions", "args": args})
            res = calculate_electricity_emissions(**args)
            tool_trace.append({"type": "tool_result", "agent": "tracker_agent", "tool_name": "calculate_electricity_emissions", "result": res})
            if res.get("status") == "success":
                logged_items.append(f"{res['label']}: {res['kg_co2e']} kg CO₂e [{res['formula']}]")

    # Direct kWh
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:kwh|units|యూనిట్లు|यूनिट)", text_lower):
        kwh_val = float(m.group(1))
        args = {"kwh": kwh_val}
        tool_trace.append({"type": "tool_call", "agent": "tracker_agent", "tool_name": "calculate_electricity_emissions", "args": args})
        res = calculate_electricity_emissions(**args)
        tool_trace.append({"type": "tool_result", "agent": "tracker_agent", "tool_name": "calculate_electricity_emissions", "result": res})
        if res.get("status") == "success":
            logged_items.append(f"{res['label']}: {res['kg_co2e']} kg CO₂e [{res['formula']}]")

    # 3. Parse Food patterns
    food_keywords = [
        (["chicken", "biryani", "చికెన్", "चिकन"], "chicken"),
        (["mutton", "beef", "మటన్", "मटन"], "mutton"),
        (["fish", "seafood", "చేప", "मछली"], "fish"),
        (["egg", "omelette", "గుడ్డు", "अंडा"], "egg"),
        (["vegan", "idli", "plant based", "ఇడ్లీ"], "vegan"),
        (["veg", "vegetarian", "thali", "dal", "paneer", "శాకాహారం", "शाकाहारी"], "vegetarian"),
    ]
    for kw_list, meal_type in food_keywords:
        if any(re.search(rf"\b{re.escape(kw)}\b", text_lower) or kw in text_lower for kw in kw_list):
            if meal_type == "vegetarian" and any(k in text_lower for k in ["chicken", "mutton", "fish", "egg", "non-veg", "non veg"]):
                continue
            args = {"meal_type": meal_type, "servings": 1}
            tool_trace.append({"type": "tool_call", "agent": "tracker_agent", "tool_name": "calculate_food_emissions", "args": args})
            res = calculate_food_emissions(**args)
            tool_trace.append({"type": "tool_result", "agent": "tracker_agent", "tool_name": "calculate_food_emissions", "result": res})
            if res.get("status") == "success":
                logged_items.append(f"{res['meal_label']}: {res['kg_co2e']} kg CO₂e")
            break

    # 4. Parse Waste patterns
    bottle_match = re.search(r"(\d+)\s*(?:plastic\s*)?(?:bottle|bottles|బాటిల్|बोतल)", text_lower)
    if bottle_match:
        qty = float(bottle_match.group(1))
        args = {"waste_type": "plastic_bottle", "quantity": qty}
        tool_trace.append({"type": "tool_call", "agent": "tracker_agent", "tool_name": "calculate_waste_emissions", "args": args})
        res = calculate_waste_emissions(**args)
        tool_trace.append({"type": "tool_result", "agent": "tracker_agent", "tool_name": "calculate_waste_emissions", "result": res})
        if res.get("status") == "success":
            logged_items.append(f"{res['waste_label']} (×{qty:g}): {res['kg_co2e']} kg CO₂e")

    # 5. Always call get_summary and suggest_reductions
    period = "week" if any(w in text_lower for w in ["week", "weekly", "వారం", "सप्ताह", "हफ्ते"]) else "today"
    tool_trace.append({"type": "tool_call", "agent": "coach_advisor_agent", "tool_name": "get_summary", "args": {"period": period}})
    summary = get_summary(period=period)
    tool_trace.append({"type": "tool_result", "agent": "coach_advisor_agent", "tool_name": "get_summary", "result": summary})

    tool_trace.append({"type": "tool_call", "agent": "coach_advisor_agent", "tool_name": "suggest_reductions", "args": {"period": period}})
    reductions = suggest_reductions(period=period)
    tool_trace.append({"type": "tool_result", "agent": "coach_advisor_agent", "tool_name": "suggest_reductions", "result": reductions})

    total_co2 = summary["total_kg_co2e"]
    india_avg = summary["benchmark_comparisons"]["india_average"]["benchmark_daily_kg_co2e"]
    green_target = summary["benchmark_comparisons"]["campus_student_target"]["benchmark_daily_kg_co2e"]
    recs = reductions.get("recommendations", [])
    top_tip = recs[0] if recs else None

    if lang == "te":
        breakdown_str = " • ".join(logged_items) if logged_items else f"మొత్తం కార్యకలాపాలు: {summary['total_activities']}"
        tip_str = (
            f"💡 సూచన: {top_tip['action']} → రోజుకు {top_tip['estimated_saving_kg_co2e']} kg CO₂e ఆదా అవుతుంది (సంవత్సరానికి {top_tip['annual_saving_kg_co2e']} kg CO₂e)!"
            if top_tip else ""
        )
        reply = (
            f"✅ లెక్కించిన ఉద్గారాలు: {breakdown_str}. "
            f"🌍 ఈరోజు మొత్తం: {total_co2} kg CO₂e (భారత సగటు {india_avg} kg/రోజు, గ్రీన్ లక్ష్యం {green_target} kg/రోజు). "
            f"{tip_str}"
        )
    elif lang == "hi":
        breakdown_str = " • ".join(logged_items) if logged_items else f"कुल गतिविधियाँ: {summary['total_activities']}"
        tip_str = (
            f"💡 सुझाव: {top_tip['action']} → प्रतिदिन {top_tip['estimated_saving_kg_co2e']} kg CO₂e की बचत (सालाना {top_tip['annual_saving_kg_co2e']} kg CO₂e)!"
            if top_tip else ""
        )
        reply = (
            f"✅ उत्सर्जन विवरण: {breakdown_str}। "
            f"🌍 आज का कुल उत्सर्जन: {total_co2} kg CO₂e (भारत का दैनिक औसत {india_avg} kg/दिन, हरित लक्ष्य {green_target} kg/दिन)। "
            f"{tip_str}"
        )
    else:
        breakdown_str = " | ".join(logged_items) if logged_items else f"Logged {summary['total_activities']} activities in memory"
        cmp_word = "below" if total_co2 <= india_avg else "above"
        tip_str = (
            f"Top Action: {top_tip['action']} to save {top_tip['estimated_saving_kg_co2e']} kg CO₂e/day ({top_tip['annual_saving_kg_co2e']} kg/yr)."
            if top_tip else ""
        )
        reply = (
            f"Breakdown: {breakdown_str}. "
            f"Total Footprint ({period}): {total_co2} kg CO₂e — {cmp_word} India's daily average of {india_avg} kg CO₂e/day (Green Target: {green_target} kg/day). "
            f"{tip_str}"
        )

    return {
        "status": "success",
        "engine": "google_adk_deterministic_tools",
        "reply": reply,
        "tool_trace": tool_trace,
        "summary_today": summary,
        "reductions_today": reductions,
        "structured_report": _build_structured_report(
            user_message=message,
            tool_trace=tool_trace,
            summary=summary,
            reductions=reductions,
        ),
    }


def _build_structured_report(
    user_message: str,
    tool_trace: List[Dict[str, Any]],
    summary: Dict[str, Any],
    reductions: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Constructs a strict, zero-text-dump structured output object from the verified
    Google ADK tool calls and SQLite session summary for interactive UI widgets.
    """
    lang = _detect_language(user_message)

    # 1. Extract itemized activities logged in this specific turn (or fall back to session activities)
    raw_items: List[Dict[str, Any]] = []
    for idx, entry in enumerate(tool_trace):
        if (
            entry.get("type") == "tool_result"
            and isinstance(entry.get("result"), dict)
            and str(entry.get("tool_name", "")).startswith("calculate_")
            and entry["result"].get("status") == "success"
        ):
            r = entry["result"]
            cat = str(
                r.get("category")
                or str(entry["tool_name"]).replace("calculate_", "").replace("_emissions", "")
            )
            label = str(
                r.get("mode_label")
                or r.get("label")
                or r.get("meal_label")
                or r.get("waste_label")
                or "Logged Activity"
            )
            qty = float(r.get("km") or r.get("kwh") or r.get("servings") or r.get("quantity") or 1.0)
            unit = str(
                r.get("unit")
                or ("km" if "km" in r else ("kWh" if "kwh" in r else ("servings" if "servings" in r else "items")))
            )
            factor = float(
                r.get("emission_factor_kg_per_pkm")
                or r.get("grid_emission_factor_kg_per_kwh")
                or r.get("emission_factor_kg_per_serving")
                or r.get("emission_factor_kg_per_unit")
                or 0.0
            )
            factor_unit = (
                "kg CO₂e/p-km"
                if cat == "travel"
                else (
                    "kg CO₂e/kWh"
                    if cat == "electricity"
                    else ("kg CO₂e/serving" if cat == "food" else "kg CO₂e/unit")
                )
            )
            kg_val = float(r.get("kg_co2e", 0.0))
            formula = str(r.get("formula", ""))
            source = str(r.get("source") or r.get("grid_source") or "Verified CEA / DEFRA Factor")

            # Build interactive math tokens from formula
            math_steps = [seg.strip() for seg in re.split(r"[;=]", formula) if seg.strip()]

            raw_items.append(
                {
                    "id": f"item-{idx}",
                    "category": cat,
                    "label": label,
                    "quantity": round(qty, 2),
                    "unit": unit,
                    "emission_factor": round(factor, 4),
                    "factor_unit": factor_unit,
                    "kg_co2e": round(kg_val, 3),
                    "formula": formula,
                    "math_steps": math_steps,
                    "source": source,
                    "appliance_kw": r.get("appliance_power_kw"),
                    "hours_used": r.get("hours_used"),
                    "equivalents": {
                        "smartphones_charged": max(1, int(round(abs(kg_val) / 0.00822))),
                        "petrol_car_km": round(abs(kg_val) / 0.170, 1),
                        "tree_absorption_days": round(abs(kg_val) / 0.060, 1),
                    },
                }
            )

    # If the user asked a summary question ("How did I do this week?") with no new calculate_* calls,
    # populate itemized_breakdown from the logged session activities in SQLite.
    if not raw_items and summary.get("activities"):
        for idx, act in enumerate(summary.get("activities", [])):
            kg_val = float(act.get("kg_co2e", 0.0))
            formula = str(act.get("formula", ""))
            cat = str(act.get("category", "activity"))
            raw_items.append(
                {
                    "id": f"hist-{idx}",
                    "category": cat,
                    "label": str(act.get("label", "Logged Activity")),
                    "quantity": round(float(act.get("quantity", 1.0)), 2),
                    "unit": str(act.get("unit", "unit")),
                    "emission_factor": 0.0,
                    "factor_unit": "kg CO₂e",
                    "kg_co2e": round(kg_val, 3),
                    "formula": formula,
                    "math_steps": [seg.strip() for seg in re.split(r"[;=]", formula) if seg.strip()],
                    "source": "SQLite Verified Session Log (CEA / DEFRA)",
                    "appliance_kw": None,
                    "hours_used": None,
                    "equivalents": {
                        "smartphones_charged": max(1, int(round(abs(kg_val) / 0.00822))),
                        "petrol_car_km": round(abs(kg_val) / 0.170, 1),
                        "tree_absorption_days": round(abs(kg_val) / 0.060, 1),
                    },
                }
            )

    turn_total_kg = round(sum(i["kg_co2e"] for i in raw_items), 3)
    denom = turn_total_kg if turn_total_kg > 0 else 1.0
    for item in raw_items:
        item["share_of_turn_pct"] = round(max(0.0, (item["kg_co2e"] / denom) * 100.0), 1)

    # 2. Build Daily Footprint & Category Distribution
    total_today_kg = round(float(summary.get("total_kg_co2e", 0.0)), 3)
    by_cat = summary.get("by_category", {})
    category_distribution = [
        {
            "category": cat,
            "kg_co2e": round(float(stats.get("kg_co2e", 0.0)), 3),
            "count": int(stats.get("count", 0)),
            "share_percent": round(float(stats.get("share_percent", 0.0)), 1),
        }
        for cat, stats in by_cat.items()
    ]
    category_distribution.sort(key=lambda x: x["kg_co2e"], reverse=True)

    # 3. Build Ordered Benchmarks for Interactive Spectrum Gauge
    bm_Order = [
        ("campus_student_target", "Green Target"),
        ("india_average", "India Daily Avg"),
        ("paris_2030_target", "Paris 2030"),
        ("global_average", "Global Daily Avg"),
    ]
    raw_bms = summary.get("benchmark_comparisons", {})
    benchmarks_list = []
    for key, short_label in bm_Order:
        if key in raw_bms:
            b = raw_bms[key]
            benchmarks_list.append(
                {
                    "key": key,
                    "short_label": short_label,
                    "full_label": b.get("benchmark_label", short_label),
                    "target_kg": float(b.get("benchmark_daily_kg_co2e", 0.0)),
                    "user_kg": float(b.get("user_daily_kg_co2e", total_today_kg)),
                    "delta_kg": float(b.get("difference_kg_co2e", 0.0)),
                    "percent_of_target": float(b.get("percent_of_benchmark", 0.0)),
                    "is_below": float(b.get("difference_kg_co2e", 0.0)) <= 0,
                    "source": b.get("source", ""),
                }
            )

    # 4. Build Interactive Toggleable Reduction Actions
    recs = reductions.get("recommendations", [])
    interactive_actions = []
    for idx, rec in enumerate(recs):
        interactive_actions.append(
            {
                "id": f"action-{idx}",
                "rank": int(rec.get("rank", idx + 1)),
                "category": str(rec.get("category", "general")),
                "target_activity": str(rec.get("target_activity", "")),
                "action_title": str(rec.get("action", "")),
                "current_kg": round(float(rec.get("current_kg_co2e", 0.0)), 3),
                "new_kg": round(float(rec.get("new_kg_co2e", 0.0)), 3),
                "daily_saving_kg": round(float(rec.get("estimated_saving_kg_co2e", 0.0)), 3),
                "annual_saving_kg": round(float(rec.get("annual_saving_kg_co2e", 0.0)), 1),
                "saving_pct": round(float(rec.get("saving_percent", 0.0)), 1),
                "formula": str(rec.get("formula", "")),
                "source": str(rec.get("source", "")),
            }
        )

    potential_saving_kg = round(
        float(reductions.get("total_potential_saving_kg_co2e", 0.0)), 3
    )
    projected_after_savings_kg = round(
        max(0.0, total_today_kg - potential_saving_kg), 3
    )

    # 5. Crisp 1-Line Multilingual Verdict (No Wall of Text)
    india_target = 5.48
    is_under_india = total_today_kg <= india_target
    if lang == "te":
        verdict_badge = "భారత సగటు కంటే తక్కువ" if is_under_india else "తగ్గించే అవకాశం ఉంది"
        one_line = (
            f"ఈరోజు మొత్తం {total_today_kg} kg CO₂e నమోదైంది • సిఫార్సు చేసిన మార్పులతో రోజుకు {potential_saving_kg} kg CO₂e ఆదా చేయవచ్చు."
        )
    elif lang == "hi":
        verdict_badge = "भारत औसत से कम" if is_under_india else "बचत का अवसर"
        one_line = (
            f"आज कुल {total_today_kg} kg CO₂e दर्ज किया गया • सुझाए गए बदलावों से प्रतिदिन {potential_saving_kg} kg CO₂e बचाया जा सकता है।"
        )
    else:
        verdict_badge = "Below India Daily Avg" if is_under_india else "Actionable Reductions Found"
        one_line = (
            f"Verified {len(raw_items)} {'activity' if len(raw_items) == 1 else 'activities'} ({turn_total_kg} kg CO₂e) • Toggle actions below to cut your daily footprint from {total_today_kg} kg to {projected_after_savings_kg} kg CO₂e."
        )

    return {
        "headline_verdict": {
            "status_badge": verdict_badge,
            "is_under_india_avg": is_under_india,
            "one_line_insight": one_line,
            "language": lang,
            "turn_added_kg": turn_total_kg,
            "cumulative_today_kg": total_today_kg,
            "potential_daily_saving_kg": potential_saving_kg,
            "projected_after_savings_kg": projected_after_savings_kg,
            "annual_baseline_kg": round(total_today_kg * 365, 1),
            "annual_potential_saving_kg": round(potential_saving_kg * 365, 1),
        },
        "itemized_breakdown": raw_items,
        "daily_footprint": {
            "period": summary.get("period", "today"),
            "total_kg_co2e": total_today_kg,
            "total_activities": int(summary.get("total_activities", 0)),
            "category_distribution": category_distribution,
            "benchmarks": benchmarks_list,
        },
        "interactive_actions": interactive_actions,
    }


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest) -> Dict[str, Any]:
    if _has_valid_api_key():
        try:
            res = await run_carbon_coach_turn(
                user_message=req.message,
                user_id=req.user_id,
                session_id=req.session_id,
            )
            res["raw_markdown_reply"] = res.get("reply", "")
            res["reply"] = _clean_markdown_for_orb(res.get("reply", ""))
            res["engine"] = "google_adk_gemini"
            res["structured_report"] = _build_structured_report(
                user_message=req.message,
                tool_trace=res.get("tool_trace", []),
                summary=res.get("summary_today", {}),
                reductions=res.get("reductions_today", {}),
            )
            return res
        except Exception as exc:
            fallback = _run_deterministic_tool_pipeline(req.message)
            fallback["adk_note"] = f"Used deterministic ADK tool fallback ({type(exc).__name__})"
            return fallback
    return _run_deterministic_tool_pipeline(req.message)


@app.get("/api/summary")
async def summary_endpoint(period: str = "today") -> Dict[str, Any]:
    return {
        "status": "success",
        "summary": get_summary(period=period),
        "reductions": suggest_reductions(period=period),
    }


@app.post("/api/reset")
async def reset_endpoint() -> Dict[str, Any]:
    cleared = clear_session_logs()
    return {
        "status": "success",
        "cleared": cleared,
        "summary": get_summary(period="today"),
        "reductions": suggest_reductions(period="today"),
    }


DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")
if os.path.isdir(DIST_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_spa() -> FileResponse:
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

