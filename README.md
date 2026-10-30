# 🌱 DevFest 2026: Carbon Coach (Google ADK + MorphOrb UI)

An AI sustainability agent built with **Google ADK (`google-adk`)**, deterministic Python emission calculators, SQLite session memory, and a **3D Morphing Thinking Orb (`MorphOrb`)** UI built with React, TypeScript, Tailwind CSS v4, and shadcn/ui structure.

---

## 🚀 Quick Start (Already Running Locally)

- **Custom MorphOrb Web UI (Vite Dev Server):** [http://localhost:5173](http://localhost:5173)
- **Production Bundle + FastAPI ADK Server:** [http://localhost:8000](http://localhost:8000)
- **Google ADK Developer Web UI (Optional):**
  ```bash
  .venv/bin/adk web
  ```

### Configure Gemini API Key (for Live Google ADK LLM Mode)
Copy `.env.example` to `.env` and add your Gemini API key:
```bash
cp .env.example .env
# Edit GOOGLE_API_KEY=AIza...
```
*(Note: Even before setting `GOOGLE_API_KEY`, the backend includes a deterministic NLU tool pipeline for English, Telugu, and Hindi that invokes the exact same Python tools so live demos never fail!)*

---

## 🧪 Run Golden Evaluation Suite
```bash
.venv/bin/pytest -v
```

---

## 📁 Project Architecture
- [`src/components/ui/ai-thiking-orb-and-input.tsx`](file:///home/rgukt/Music/HACK/src/components/ui/ai-thiking-orb-and-input.tsx) — 3D Dotted Canvas Thinking Orb, morphing pill input, aurora underglow, green condensation, and unfolding answer card.
- [`src/index.css`](file:///home/rgukt/Music/HACK/src/index.css) — Tailwind v4 + `tw-animate-css` + custom `@keyframes mo-*` and `.mo-*` stage styles.
- [`src/App.tsx`](file:///home/rgukt/Music/HACK/src/App.tsx) — Full Carbon Coach experience wrapping `MorphOrb` with live ADK Tool Execution inspector, Session Memory log, and Actionable Reduction cards.
- [`carbon_coach/agent.py`](file:///home/rgukt/Music/HACK/carbon_coach/agent.py) — Google ADK `root_agent`, `tracker_agent`, and `coach_advisor_agent`.
- [`carbon_coach/tools/`](file:///home/rgukt/Music/HACK/carbon_coach/tools/) — Deterministic Python tools (`calculate_travel_emissions`, `calculate_electricity_emissions`, `calculate_food_emissions`, `calculate_waste_emissions`, `log_activity`, `get_summary`, `suggest_reductions`).
- [`carbon_coach/data/emission_factors.py`](file:///home/rgukt/Music/HACK/carbon_coach/data/emission_factors.py) — Cited emission factors (CEA India v19.0, BEE India, India GHG Program, DEFRA 2024, Poore & Nemecek).
