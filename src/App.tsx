import React, { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  ArrowUp,
  Calculator,
  Car,
  Check,
  ChevronDown,
  ChevronRight,
  Clock,
  Cpu,
  Flame,
  Gauge,
  Globe,
  Leaf,
  MessageSquare,
  PanelLeft,
  Plus,
  RotateCcw,
  ShieldCheck,
  Smartphone,
  Sparkles,
  Terminal,
  Trash2,
  TreePine,
  TrendingDown,
  Utensils,
  Zap,
} from "lucide-react";

/* ─────────────────────────── Structured Output Types ─────────────────────────── */
interface ToolTraceEntry {
  type: "tool_call" | "tool_result";
  agent: string;
  tool_name: string;
  args?: Record<string, unknown>;
  result?: Record<string, unknown>;
}

interface ItemizedActivity {
  id: string;
  category: string;
  label: string;
  quantity: number;
  unit: string;
  emission_factor: number;
  factor_unit: string;
  kg_co2e: number;
  share_of_turn_pct: number;
  formula: string;
  math_steps: string[];
  source: string;
  appliance_kw?: number | null;
  hours_used?: number | null;
  equivalents: {
    smartphones_charged: number;
    petrol_car_km: number;
    tree_absorption_days: number;
  };
}

interface CategoryDistItem {
  category: string;
  kg_co2e: number;
  count: number;
  share_percent: number;
}

interface StructuredBenchmark {
  key: string;
  short_label: string;
  full_label: string;
  target_kg: number;
  user_kg: number;
  delta_kg: number;
  percent_of_target: number;
  is_below: boolean;
  source: string;
}

interface InteractiveAction {
  id: string;
  rank: number;
  category: string;
  target_activity: string;
  action_title: string;
  current_kg: number;
  new_kg: number;
  daily_saving_kg: number;
  annual_saving_kg: number;
  saving_pct: number;
  formula: string;
  source: string;
}

interface StructuredReport {
  headline_verdict: {
    status_badge: string;
    is_under_india_avg: boolean;
    one_line_insight: string;
    language: string;
    turn_added_kg: number;
    cumulative_today_kg: number;
    potential_daily_saving_kg: number;
    projected_after_savings_kg: number;
    annual_baseline_kg: number;
    annual_potential_saving_kg: number;
  };
  itemized_breakdown: ItemizedActivity[];
  daily_footprint: {
    period: string;
    total_kg_co2e: number;
    total_activities: number;
    category_distribution: CategoryDistItem[];
    benchmarks: StructuredBenchmark[];
  };
  interactive_actions: InteractiveAction[];
}

interface SummaryData {
  period: string;
  total_activities: number;
  total_kg_co2e: number;
  daily_average_kg_co2e: number;
  by_category: Record<
    string,
    { kg_co2e: number; count: number; share_percent: number }
  >;
  benchmark_comparisons: Record<
    string,
    {
      benchmark_label: string;
      benchmark_daily_kg_co2e: number;
      user_daily_kg_co2e: number;
      difference_kg_co2e: number;
      percent_of_benchmark: number;
      status: string;
      source: string;
    }
  >;
  activities: Array<{
    category: string;
    label: string;
    quantity: number;
    unit: string;
    kg_co2e: number;
    formula: string;
  }>;
}

interface CompletedChatTurn {
  id: string;
  timestamp: string;
  userPrompt: string;
  engine: string;
  toolTrace: ToolTraceEntry[];
  structuredReport: StructuredReport;
  summarySnapshot: SummaryData | null;
}

const QUICK_SCENARIOS = [
  {
    label: "12 km Bus + 4h AC",
    prompt: "I travelled 12 km by bus today and used the AC for 4 hours.",
  },
  {
    label: "Chicken Lunch + 2 Bottles",
    prompt: "I also had chicken biryani for lunch and threw away 2 plastic water bottles.",
  },
  {
    label: "Weekly Footprint Review",
    prompt: "How did I do this week? Show my total emissions and top reduction savings.",
  },
];

const LANG_PROMPTS: Record<"EN" | "TE" | "HI", string> = {
  EN: "I travelled 12 km by bus today and used the AC for 4 hours.",
  TE: "నేను ఈరోజు బస్సులో 12 కి.మీ ప్రయాణించాను మరియు 4 గంటలు ఏసీ వాడాను.",
  HI: "मैंने आज बस से 12 किमी यात्रा की और 4 घंटे एसी चलाया।",
};

function getCategoryStyle(cat: string) {
  switch (cat.toLowerCase()) {
    case "travel":
      return {
        label: "Transit",
        icon: Car,
        tint: "text-[#4d6bfe] bg-[#4d6bfe]/[0.09]",
        barColor: "bg-[#4d6bfe]",
        dotColor: "bg-[#4d6bfe]",
      };
    case "electricity":
      return {
        label: "Energy",
        icon: Zap,
        tint: "text-amber-600 bg-amber-500/[0.11]",
        barColor: "bg-amber-500",
        dotColor: "bg-amber-500",
      };
    case "food":
      return {
        label: "Nutrition",
        icon: Utensils,
        tint: "text-emerald-600 bg-emerald-500/[0.11]",
        barColor: "bg-emerald-500",
        dotColor: "bg-emerald-500",
      };
    case "waste":
      return {
        label: "Waste",
        icon: Trash2,
        tint: "text-rose-600 bg-rose-500/[0.11]",
        barColor: "bg-rose-500",
        dotColor: "bg-rose-500",
      };
    default:
      return {
        label: cat,
        icon: Flame,
        tint: "text-slate-600 bg-slate-500/[0.10]",
        barColor: "bg-slate-500",
        dotColor: "bg-slate-500",
      };
  }
}

/* Fallback builder if a turn in localStorage was saved before structured_report existed */
function ensureStructuredReport(
  rawReport: StructuredReport | undefined,
  toolTrace: ToolTraceEntry[],
  summary: SummaryData | null
): StructuredReport {
  if (rawReport && rawReport.headline_verdict && rawReport.itemized_breakdown) {
    return rawReport;
  }
  const items: ItemizedActivity[] = [];
  toolTrace.forEach((entry, idx) => {
    if (
      entry.type === "tool_result" &&
      entry.result &&
      entry.tool_name.startsWith("calculate_") &&
      entry.result.status === "success"
    ) {
      const r = entry.result;
      const kg = Number(r.kg_co2e ?? 0);
      const formula = String(r.formula || "");
      items.push({
        id: `item-${idx}`,
        category: String(
          r.category ||
            entry.tool_name.replace("calculate_", "").replace("_emissions", "")
        ),
        label: String(
          r.mode_label || r.label || r.meal_label || r.waste_label || "Activity"
        ),
        quantity: Number(r.km ?? r.kwh ?? r.servings ?? r.quantity ?? 1),
        unit: String(r.unit || (r.km ? "km" : r.kwh ? "kWh" : "unit")),
        emission_factor: Number(
          r.emission_factor_kg_per_pkm ||
            r.grid_emission_factor_kg_per_kwh ||
            r.emission_factor_kg_per_serving ||
            0
        ),
        factor_unit: "kg CO₂e",
        kg_co2e: kg,
        share_of_turn_pct: 100,
        formula,
        math_steps: formula.split(/[;=]/).map((s) => s.trim()).filter(Boolean),
        source: String(r.source || "CEA India / DEFRA 2024"),
        equivalents: {
          smartphones_charged: Math.max(1, Math.round(Math.abs(kg) / 0.00822)),
          petrol_car_km: Number((Math.abs(kg) / 0.17).toFixed(1)),
          tree_absorption_days: Number((Math.abs(kg) / 0.06).toFixed(1)),
        },
      });
    }
  });
  const turnSum = Number(items.reduce((a, b) => a + b.kg_co2e, 0).toFixed(3));
  items.forEach((it) => {
    it.share_of_turn_pct =
      turnSum > 0 ? Number(((it.kg_co2e / turnSum) * 100).toFixed(1)) : 100;
  });

  const totalToday = Number(summary?.total_kg_co2e ?? turnSum);
  const catDist: CategoryDistItem[] = Object.entries(
    summary?.by_category || {}
  ).map(([cat, st]) => ({
    category: cat,
    kg_co2e: Number(st.kg_co2e),
    count: Number(st.count),
    share_percent: Number(st.share_percent),
  }));

  const bms: StructuredBenchmark[] = Object.entries(
    summary?.benchmark_comparisons || {}
  ).map(([key, b]) => ({
    key,
    short_label: b.benchmark_label.replace(/\s*\(.*?\)/, ""),
    full_label: b.benchmark_label,
    target_kg: Number(b.benchmark_daily_kg_co2e),
    user_kg: Number(b.user_daily_kg_co2e),
    delta_kg: Number(b.difference_kg_co2e),
    percent_of_target: Number(b.percent_of_benchmark),
    is_below: Number(b.difference_kg_co2e) <= 0,
    source: b.source,
  }));

  return {
    headline_verdict: {
      status_badge:
        totalToday <= 5.48 ? "Below India Daily Avg" : "Reductions Available",
      is_under_india_avg: totalToday <= 5.48,
      one_line_insight: `Verified ${items.length} activities (${turnSum.toFixed(3)} kg CO₂e). Inspect itemized formulas or simulate reductions below.`,
      language: "en",
      turn_added_kg: turnSum,
      cumulative_today_kg: totalToday,
      potential_daily_saving_kg: 0,
      projected_after_savings_kg: totalToday,
      annual_baseline_kg: Number((totalToday * 365).toFixed(1)),
      annual_potential_saving_kg: 0,
    },
    itemized_breakdown: items,
    daily_footprint: {
      period: summary?.period || "today",
      total_kg_co2e: totalToday,
      total_activities: summary?.total_activities || items.length,
      category_distribution: catDist,
      benchmarks: bms,
    },
    interactive_actions: [],
  };
}

export default function App() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [thinkingStep, setThinkingStep] = useState(0);
  const [deepAuditOn, setDeepAuditOn] = useState(true);
  const [liveSourcesOn, setLiveSourcesOn] = useState(true);
  const [activeLang, setActiveLang] = useState<"EN" | "TE" | "HI">("EN");

  // Completed chats & verification history
  const [turns, setTurns] = useState<CompletedChatTurn[]>(() => {
    try {
      const saved = localStorage.getItem("carbon_coach_structured_turns_v3");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(() => {
    try {
      const saved = localStorage.getItem("carbon_coach_structured_turns_v3");
      const parsed = saved ? JSON.parse(saved) : [];
      return parsed.length > 0 ? parsed[0].id : null;
    } catch {
      return null;
    }
  });
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);
  const [summary, setSummary] = useState<SummaryData | null>(null);

  const startNewChat = () => {
    setSelectedTurnId(null);
    setInput("");
    setSelectedCategoryFilter(null);
    window.setTimeout(() => {
      textareaRef.current?.focus();
    }, 20);
  };

  // Interactive Output States
  const [activeOutputSection, setActiveOutputSection] = useState<
    "all" | "itemized" | "footprint" | "audit"
  >("all");
  const [expandedItemIds, setExpandedItemIds] = useState<Record<string, boolean>>({});
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string | null>(
    null
  );
  // Toggled reduction action IDs for live "What-If" Daily Footprint simulation
  const [simulatedActionIds, setSimulatedActionIds] = useState<
    Record<string, boolean>
  >({});

  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    try {
      localStorage.setItem(
        "carbon_coach_structured_turns_v3",
        JSON.stringify(turns)
      );
    } catch {
      // ignore storage quota errors
    }
  }, [turns]);

  useEffect(() => {
    fetch("/api/summary?period=today")
      .then((r) => r.json())
      .then((d) => {
        if (d?.summary) setSummary(d.summary);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!loading) {
      setThinkingStep(0);
      return;
    }
    const id = window.setInterval(() => {
      setThinkingStep((s) => (s + 1) % 4);
    }, 850);
    return () => window.clearInterval(id);
  }, [loading]);

  const activeTurn = selectedTurnId
    ? turns.find((t) => t.id === selectedTurnId) ?? null
    : null;

  // Reset category filter & auto-expand first itemized card when switching turns
  useEffect(() => {
    setSelectedCategoryFilter(null);
    if (activeTurn?.structuredReport?.itemized_breakdown?.[0]) {
      const firstId = activeTurn.structuredReport.itemized_breakdown[0].id;
      setExpandedItemIds({ [firstId]: true });
    }
    // Default-enable top reduction action so the user sees the interactive simulator live
    if (activeTurn?.structuredReport?.interactive_actions?.[0]) {
      const topActionId = activeTurn.structuredReport.interactive_actions[0].id;
      setSimulatedActionIds({ [topActionId]: true });
    } else {
      setSimulatedActionIds({});
    }
  }, [activeTurn?.id]);

  const handleLanguageSelect = (lang: "EN" | "TE" | "HI") => {
    setActiveLang(lang);
    if (!input.trim()) {
      setInput(LANG_PROMPTS[lang]);
      textareaRef.current?.focus();
    }
  };

  const submitMessage = async (overridePrompt?: string) => {
    const promptText = (overridePrompt ?? input).trim();
    if (!promptText || loading) return;

    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: promptText,
          user_id: "devfest_user",
          session_id: "devfest_session",
        }),
      });
      const data = await res.json();

      const toolTrace: ToolTraceEntry[] = Array.isArray(data.tool_trace)
        ? data.tool_trace
        : [];

      const structuredReport = ensureStructuredReport(
        data.structured_report,
        toolTrace,
        data.summary_today || null
      );

      const newTurn: CompletedChatTurn = {
        id: `turn-${Date.now()}`,
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        userPrompt: promptText,
        engine: data.engine || "google_adk_gemini",
        toolTrace,
        structuredReport,
        summarySnapshot: data.summary_today || null,
      };

      if (data.summary_today) {
        setSummary(data.summary_today);
      }

      setTurns((prev) => [newTurn, ...prev]);
      setSelectedTurnId(newTurn.id);
    } catch {
      // ignore network error
    } finally {
      setLoading(false);
    }
  };

  const handleResetAll = async () => {
    try {
      const res = await fetch("/api/reset", { method: "POST" });
      const data = await res.json();
      if (data.summary) setSummary(data.summary);
    } catch {
      // ignore
    }
    setTurns([]);
    setSelectedTurnId(null);
    localStorage.removeItem("carbon_coach_structured_turns_v3");
  };

  const toggleItemExpand = (id: string) => {
    setExpandedItemIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleSimulatedAction = (id: string) => {
    setSimulatedActionIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const thinkingLabels = [
    "Routing prompt to Google ADK tracker_agent…",
    "Running deterministic Python emission calculators…",
    "Persisting to SQLite memory & comparing daily benchmarks…",
    "Building structured interactive report & savings simulator…",
  ];

  const totalSessionCo2 = summary?.total_kg_co2e ?? 0;

  // Derived Interactive Metrics for the Active Turn
  const report = activeTurn
    ? ensureStructuredReport(
        activeTurn.structuredReport,
        activeTurn.toolTrace,
        activeTurn.summarySnapshot
      )
    : null;

  const activeSimulatedSavingKg = report
    ? Number(
        report.interactive_actions
          .filter((a) => simulatedActionIds[a.id])
          .reduce((acc, a) => acc + a.daily_saving_kg, 0)
          .toFixed(3)
      )
    : 0;

  const activeSimulatedAnnualSavingKg = report
    ? Number(
        report.interactive_actions
          .filter((a) => simulatedActionIds[a.id])
          .reduce((acc, a) => acc + a.annual_saving_kg, 0)
          .toFixed(1)
      )
    : 0;

  const baselineDailyKg = report?.daily_footprint.total_kg_co2e ?? 0;
  const simulatedDailyKg = Number(
    Math.max(0, baselineDailyKg - activeSimulatedSavingKg).toFixed(3)
  );

  const filteredItemized = report
    ? selectedCategoryFilter
      ? report.itemized_breakdown.filter(
          (i) =>
            i.category.toLowerCase() === selectedCategoryFilter.toLowerCase()
        )
      : report.itemized_breakdown
    : [];

  return (
    <div className="ds-root flex min-h-screen flex-col">
      {/* DeepSeek Architectural Grid + Soft Ambient Glow */}
      <div className="ds-grid-bg" />
      <div className="ds-ambient-glow" />

      {/* ───────────────────── Top Navigation Bar (Exact DeepSeek Scale) ───────────────────── */}
      <header className="sticky top-0 z-30 flex h-20 w-full items-center justify-between border-b border-black/[0.03] bg-white/75 px-6 backdrop-blur-xl sm:px-14">
        <div className="flex items-center gap-3.5">
          <button
            type="button"
            onClick={() => setSidebarOpen((v) => !v)}
            title={sidebarOpen ? "Hide Sidebar" : "Show Sidebar"}
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-[#64748b] transition hover:bg-black/[0.04] hover:text-[#1e293b]"
          >
            <PanelLeft className="h-[19px] w-[19px] stroke-[1.8]" />
          </button>

          {/* Brand Wordmark */}
          <a
            href="#top"
            onClick={(e) => {
              e.preventDefault();
              startNewChat();
            }}
            className="flex items-center gap-2.5 transition opacity-95 hover:opacity-100"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#3b6bf9] text-white shadow-2xs">
              <Leaf className="h-4 w-4 stroke-[2.4]" />
            </div>
            <span className="ds-heading text-[24px] font-bold tracking-[-0.025em] text-[#3b6bf9]">
              carboncoach
            </span>
          </a>
        </div>

        {/* Right Controls: Live Footprint Pill + New Chat + Segmented Language Switcher */}
        <div className="flex items-center gap-6">
          <div className="hidden md:inline-flex items-center gap-2 rounded-full border border-black/[0.07] bg-white/90 px-3.5 py-1.5 text-[13px] text-[#475569] shadow-2xs">
            <span className="h-2 w-2 rounded-full bg-[#34c759]" />
            <span>Today</span>
            <span className="ds-mono font-semibold text-[#1e293b]">
              {totalSessionCo2.toFixed(3)} kg CO₂e
            </span>
          </div>

          <button
            type="button"
            onClick={startNewChat}
            className="hidden sm:inline-block text-[15px] font-medium text-[#1e293b] transition hover:text-[#3b6bf9]"
          >
            New Chat
          </button>

          {/* DeepSeek-style Pill Segmented Control for Language */}
          <div className="inline-flex items-center rounded-full border border-[#d6deeb] bg-white/85 p-1 text-[13px] font-medium shadow-2xs">
            {(["TE", "HI", "EN"] as const).map((lang) => {
              const labelMap = { TE: "తెలుగు", HI: "हिं", EN: "EN" };
              const active = activeLang === lang;
              return (
                <button
                  key={lang}
                  type="button"
                  data-active={active}
                  onClick={() => handleLanguageSelect(lang)}
                  className={`rounded-full px-3 py-1 transition ${
                    active
                      ? "bg-[#f1f5f9] font-semibold text-[#0f172a]"
                      : "text-[#64748b] hover:text-[#1e293b]"
                  }`}
                >
                  {labelMap[lang]}
                </button>
              );
            })}
          </div>
        </div>
      </header>

      {/* ───────────────────── Workspace Layout ───────────────────── */}
      <div className="relative z-10 flex flex-1">
        {/* ─────────── Left Sidebar: Completed Chats & Verification ─────────── */}
        {sidebarOpen && (
          <aside className="flex w-[288px] shrink-0 flex-col border-r border-black/[0.05] bg-[#f5f5f7]/70 backdrop-blur-2xl">
            {/* Primary "New Chat" Button at Top of Left Sidebar */}
            <div className="px-3 pt-3.5 pb-2">
              <button
                type="button"
                onClick={startNewChat}
                className={`flex w-full items-center justify-between rounded-xl border px-3.5 py-2.5 text-[13px] font-medium transition ${
                  selectedTurnId === null
                    ? "border-[#4d6bfe]/40 bg-[#4d6bfe] text-white shadow-xs"
                    : "border-black/[0.07] bg-white/90 text-[#1d1d1f] shadow-2xs hover:border-[#4d6bfe]/35 hover:text-[#4d6bfe]"
                }`}
              >
                <span className="inline-flex items-center gap-2">
                  <Plus className="h-4 w-4 stroke-[2.2]" />
                  <span>New Chat</span>
                </span>
                <span
                  className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                    selectedTurnId === null
                      ? "bg-white/20 text-white"
                      : "bg-black/[0.04] text-[#86868b]"
                  }`}
                >
                  Fresh
                </span>
              </button>
            </div>

            <div className="flex items-center justify-between px-4 pt-2 pb-2">
              <span className="text-[11px] font-semibold tracking-wider text-[#86868b] uppercase">
                Completed Chats
              </span>
              <div className="flex items-center gap-1">
                {turns.length > 0 && (
                  <button
                    type="button"
                    onClick={handleResetAll}
                    title="Clear Session Memory"
                    className="inline-flex h-6 w-6 items-center justify-center rounded-md text-[#86868b] transition hover:bg-rose-500/10 hover:text-rose-600"
                  >
                    <RotateCcw className="h-3 w-3" />
                  </button>
                )}
              </div>
            </div>

            {/* Session Summary Mini-Widget */}
            <div className="mx-3 mb-2.5 rounded-2xl border border-black/[0.05] bg-white/85 p-3 shadow-2xs">
              <div className="flex items-baseline justify-between">
                <span className="text-[11px] font-medium text-[#86868b]">
                  Session Footprint
                </span>
                <span className="inline-flex items-center gap-1 text-[10.5px] font-medium text-[#34c759]">
                  <ShieldCheck className="h-3 w-3" /> Verified
                </span>
              </div>
              <div className="mt-1 flex items-baseline justify-between">
                <span className="ds-mono text-[18px] font-semibold tracking-tight text-[#1d1d1f]">
                  {totalSessionCo2.toFixed(3)}{" "}
                  <span className="text-[11px] font-normal text-[#86868b]">
                    kg CO₂e
                  </span>
                </span>
                <span className="text-[11px] text-[#86868b]">vs 5.48 avg</span>
              </div>
            </div>

            {/* Completed Chats Scroll List */}
            <div className="ds-scroll flex-1 space-y-1 overflow-y-auto px-2.5 pb-4">
              {turns.length === 0 ? (
                <div className="px-3 py-10 text-center">
                  <Clock className="mx-auto h-5 w-5 text-[#86868b]/60 stroke-[1.6]" />
                  <p className="mt-2 text-[12px] font-medium text-[#515154]">
                    No logs in this session
                  </p>
                  <p className="mt-0.5 text-[11px] leading-relaxed text-[#86868b]">
                    Every activity you log is stored here with its structured interactive report.
                  </p>
                </div>
              ) : (
                turns.map((turn) => {
                  const isSelected = activeTurn?.id === turn.id;
                  const toolCallsCount = turn.toolTrace.filter(
                    (t) => t.type === "tool_call"
                  ).length;
                  const turnAdded =
                    turn.structuredReport?.headline_verdict?.turn_added_kg ?? 0;
                  const cumToday =
                    turn.structuredReport?.headline_verdict
                      ?.cumulative_today_kg ?? 0;

                  return (
                    <button
                      key={turn.id}
                      type="button"
                      onClick={() => setSelectedTurnId(turn.id)}
                      className={`group flex w-full flex-col rounded-xl px-3 py-2.5 text-left transition ${
                        isSelected
                          ? "bg-white shadow-xs ring-1 ring-black/[0.06]"
                          : "hover:bg-white/60"
                      }`}
                    >
                      <div className="flex w-full items-center justify-between gap-2">
                        <span className="truncate text-[13px] font-medium text-[#1d1d1f]">
                          {turn.userPrompt}
                        </span>
                      </div>

                      <div className="mt-1.5 flex w-full items-center justify-between text-[11px] text-[#86868b]">
                        <span className="inline-flex items-center gap-1">
                          <span className="h-1.5 w-1.5 rounded-full bg-[#4d6bfe]" />
                          {toolCallsCount} tools • {turn.timestamp}
                        </span>
                        <span className="ds-mono font-medium text-[#1d1d1f]">
                          {turnAdded > 0
                            ? `+${turnAdded.toFixed(2)} kg`
                            : `${cumToday.toFixed(2)} kg`}
                        </span>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </aside>
        )}

        {/* ─────────── Center Stage (Exact DeepSeek Proportions + Redesigned Interactive Output) ─────────── */}
        <main className="flex flex-1 flex-col items-center px-5 pt-14 pb-24 sm:px-10">
          <div className="w-full max-w-[820px]">
            {/* Release / ADK Status Banner (Exact 3-line scale from reference image) */}
            <div className="mx-auto mb-7 max-w-[760px] text-center">
              <p className="text-[14.5px] sm:text-[15.5px] leading-[1.75] text-[#7c899b]">
                <Sparkles className="mr-1.5 inline-block h-4 w-4 -translate-y-0.5 text-[#7594ff]" />
                <span>
                  Carbon Coach ADK v2.6 Flash has been updated with deterministic Python calculators, significantly enhancing daily emission tracking accuracy and enabling zero-hallucination audits at faster speed. Additionally, the agent now supports CEA India &amp; DEFRA 2024 live benchmarks. →
                </span>
              </p>
            </div>

            {/* Hero Title (Exact 56px-58px scale & weight from reference image) */}
            <h1 className="ds-heading mb-9 select-none text-center text-[46px] sm:text-[58px] font-normal leading-[1.15] tracking-[-0.02em] text-[#22334d]">
              Into Zero Carbon
            </h1>

            {/* ─────────── DeepSeek × Apple Glass Composer (Exact Large Scale) ─────────── */}
            <div className="ds-input-box flex min-h-[168px] flex-col justify-between rounded-[28px] px-7 pt-6 pb-5">
              <textarea
                ref={textareaRef}
                rows={2}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    submitMessage();
                  }
                }}
                placeholder="Ask anything, log your daily activities together"
                className="w-full resize-none border-0 bg-transparent text-[16.5px] leading-[1.6] text-[#1e293b] placeholder:text-[#7c899b] focus:outline-none"
              />

              {/* Composer Bottom Bar */}
              <div className="mt-4 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={() => setDeepAuditOn((v) => !v)}
                    className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-[13.5px] font-medium transition ${
                      deepAuditOn
                        ? "border-[#dce3ee] bg-white/95 text-[#1e293b] shadow-2xs"
                        : "border-black/[0.08] bg-white/70 text-[#64748b] hover:bg-white"
                    }`}
                  >
                    <Cpu className="h-4 w-4 stroke-[1.9]" />
                    <span>ADK Verify</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setLiveSourcesOn((v) => !v)}
                    className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-[13.5px] font-medium transition ${
                      liveSourcesOn
                        ? "border-[#dce3ee] bg-white/95 text-[#1e293b] shadow-2xs"
                        : "border-black/[0.08] bg-white/70 text-[#64748b] hover:bg-white"
                    }`}
                  >
                    <Globe className="h-4 w-4 stroke-[1.9]" />
                    <span>CEA &amp; DEFRA</span>
                  </button>
                </div>

                <button
                  type="button"
                  disabled={!input.trim() || loading}
                  onClick={() => submitMessage()}
                  aria-label="Send message"
                  className={`inline-flex h-10 w-10 items-center justify-center rounded-full text-white transition ${
                    input.trim() && !loading
                      ? "bg-[#426bf7] hover:bg-[#345ce8] shadow-xs cursor-pointer"
                      : "bg-[#426bf7]/85 cursor-pointer hover:bg-[#426bf7]"
                  }`}
                >
                  <ArrowUp className="h-5 w-5 stroke-[2.3]" />
                </button>
              </div>
            </div>

            {/* ─────────── Quick Scenario Pills (Exact Large Pill Scale) ─────────── */}
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              {QUICK_SCENARIOS.map((item) => (
                <button
                  key={item.label}
                  type="button"
                  disabled={loading}
                  onClick={() => submitMessage(item.prompt)}
                  className="inline-flex items-center gap-2.5 rounded-full border border-[#e2e8f0] bg-white/95 px-6 py-3 text-[14.5px] font-medium text-[#0f172a] shadow-[0_2px_10px_rgba(15,23,42,0.03)] backdrop-blur-md transition hover:border-[#426bf7]/40 hover:shadow-xs disabled:opacity-50"
                >
                  <MessageSquare className="h-4 w-4 text-[#334155] stroke-[1.9]" />
                  <span>{item.label}</span>
                </button>
              ))}
            </div>

            {/* ─────────── Loading Card ─────────── */}
            {loading && (
              <div className="apple-surface mt-8 rounded-[22px] p-5">
                <div className="flex items-center gap-3.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#4d6bfe]/[0.08] text-[#4d6bfe]">
                    <Cpu className="h-4 w-4 animate-spin" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-[11px] font-semibold tracking-wider text-[#4d6bfe] uppercase">
                      Google ADK Active
                    </div>
                    <p className="truncate text-[13.5px] font-medium text-[#1d1d1f]">
                      {thinkingLabels[thinkingStep]}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* ═══════════════════════════════════════════════════════════════════════════
               REDESIGNED INTERACTIVE STRUCTURED OUTPUT (Zero Text Dumps)
               ═══════════════════════════════════════════════════════════════════════════ */}
            {!loading && activeTurn && report && (
              <div className="mt-8 space-y-4">
                {/* ─────────── MODULE A: Executive Impact Header & Section Switcher ─────────── */}
                <div className="apple-surface overflow-hidden rounded-[24px]">
                  <div className="border-b border-black/[0.05] px-6 pt-5 pb-4">
                    {/* Top Row: Status Pill + Interactive View Mode Switcher */}
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${
                            report.headline_verdict.is_under_india_avg
                              ? "bg-[#34c759]/[0.12] text-[#248a3d]"
                              : "bg-[#4d6bfe]/[0.10] text-[#3b5bfd]"
                          }`}
                        >
                          <Check className="h-3 w-3 stroke-[2.5]" />
                          {report.headline_verdict.status_badge}
                        </span>
                        <span className="text-[11.5px] text-[#86868b]">
                          Logged {activeTurn.timestamp}
                        </span>
                      </div>

                      {/* Apple Segmented View Filter */}
                      <div className="apple-segmented inline-flex items-center text-[11.5px] font-medium">
                        {(
                          [
                            { id: "all", label: "All Widgets" },
                            { id: "itemized", label: "Itemized Math" },
                            { id: "footprint", label: "Daily Footprint" },
                            {
                              id: "audit",
                              label: `ADK Trace (${
                                activeTurn.toolTrace.filter(
                                  (t) => t.type === "tool_call"
                                ).length
                              })`,
                            },
                          ] as const
                        ).map((tab) => (
                          <button
                            key={tab.id}
                            type="button"
                            data-active={activeOutputSection === tab.id}
                            onClick={() => setActiveOutputSection(tab.id)}
                            className="apple-segmented-item px-2.5 py-1 text-[#515154]"
                          >
                            {tab.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Logged Prompt + 1-Line Structured Takeaway */}
                    <div className="mt-3.5">
                      <div className="text-[11px] font-medium text-[#86868b]">
                        Logged Input
                      </div>
                      <div className="mt-0.5 text-[16px] font-semibold tracking-tight text-[#1d1d1f]">
                        “{activeTurn.userPrompt}”
                      </div>
                      <p className="mt-1 text-[13px] text-[#515154]">
                        {report.headline_verdict.one_line_insight}
                      </p>
                    </div>
                  </div>

                  {/* 3 Interactive Live Telemetry Counters (Turn Added | Simulated Daily | Annual Impact) */}
                  <div className="grid grid-cols-1 divide-y divide-black/[0.05] bg-[#fbfbfd]/70 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
                    {/* Counter 1: This Turn Added */}
                    <div className="px-5 py-3.5">
                      <div className="text-[11px] font-medium text-[#86868b]">
                        Itemized Turn Total
                      </div>
                      <div className="ds-mono mt-1 flex items-baseline gap-1.5">
                        <span className="text-[22px] font-semibold tracking-tight text-[#1d1d1f]">
                          +{report.headline_verdict.turn_added_kg.toFixed(3)}
                        </span>
                        <span className="text-[11.5px] text-[#86868b]">
                          kg CO₂e
                        </span>
                      </div>
                      <div className="mt-0.5 text-[11px] text-[#86868b]">
                        {report.itemized_breakdown.length}{" "}
                        {report.itemized_breakdown.length === 1
                          ? "activity"
                          : "activities"}{" "}
                        calculated
                      </div>
                    </div>

                    {/* Counter 2: Live Daily Footprint (Reacts to Simulated Action Toggles!) */}
                    <div className="px-5 py-3.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-medium text-[#86868b]">
                          Daily Footprint
                        </span>
                        {activeSimulatedSavingKg > 0 && (
                          <span className="rounded-full bg-[#34c759]/[0.14] px-2 py-0.2 text-[10px] font-semibold text-[#248a3d]">
                            Simulated
                          </span>
                        )}
                      </div>
                      <div className="ds-mono mt-1 flex items-baseline gap-2">
                        <span className="text-[22px] font-semibold tracking-tight text-[#4d6bfe]">
                          {simulatedDailyKg.toFixed(3)}
                        </span>
                        <span className="text-[11.5px] text-[#86868b]">
                          kg/day
                        </span>
                        {activeSimulatedSavingKg > 0 && (
                          <span className="text-[11.5px] text-[#86868b] line-through">
                            {baselineDailyKg.toFixed(2)}
                          </span>
                        )}
                      </div>
                      <div className="mt-0.5 text-[11px] text-[#248a3d]">
                        {activeSimulatedSavingKg > 0
                          ? `Saving ${activeSimulatedSavingKg.toFixed(3)} kg/day via active toggles`
                          : "Toggle actions below to simulate savings"}
                      </div>
                    </div>

                    {/* Counter 3: Annualized Trajectory */}
                    <div className="px-5 py-3.5">
                      <div className="text-[11px] font-medium text-[#86868b]">
                        Annualized Projection
                      </div>
                      <div className="ds-mono mt-1 flex items-baseline gap-1.5">
                        <span className="text-[22px] font-semibold tracking-tight text-[#1d1d1f]">
                          {Math.max(
                            0,
                            Math.round(
                              report.headline_verdict.annual_baseline_kg -
                                activeSimulatedAnnualSavingKg
                            )
                          ).toLocaleString()}
                        </span>
                        <span className="text-[11.5px] text-[#86868b]">
                          kg/yr
                        </span>
                      </div>
                      <div className="mt-0.5 text-[11px] text-[#4d6bfe]">
                        {activeSimulatedAnnualSavingKg > 0
                          ? `-${activeSimulatedAnnualSavingKg.toFixed(0)} kg CO₂e/yr avoided`
                          : `Baseline: ${report.headline_verdict.annual_baseline_kg.toFixed(0)} kg/yr`}
                      </div>
                    </div>
                  </div>
                </div>

                {/* ─────────── MODULE B: Interactive Itemized Breakdown (Expandable Formula & Equivalencies) ─────────── */}
                {(activeOutputSection === "all" ||
                  activeOutputSection === "itemized") && (
                  <div className="apple-surface overflow-hidden rounded-[24px] p-6">
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#4d6bfe]/[0.10] text-[#4d6bfe]">
                          <Calculator className="h-4 w-4" />
                        </div>
                        <div>
                          <h3 className="ds-heading text-[15px] font-semibold text-[#1d1d1f]">
                            Itemized Breakdown & Formula Inspector
                          </h3>
                          <p className="text-[11.5px] text-[#86868b]">
                            Click any activity row to inspect step-by-step math & real-world equivalencies
                          </p>
                        </div>
                      </div>

                      {selectedCategoryFilter && (
                        <button
                          type="button"
                          onClick={() => setSelectedCategoryFilter(null)}
                          className="inline-flex items-center gap-1 rounded-full bg-[#4d6bfe]/[0.10] px-2.5 py-1 text-[11px] font-medium text-[#3b5bfd]"
                        >
                          <span>Filter: {selectedCategoryFilter}</span>
                          <span className="ml-1 font-bold">×</span>
                        </button>
                      )}
                    </div>

                    <div className="space-y-2.5">
                      {filteredItemized.map((item) => {
                        const style = getCategoryStyle(item.category);
                        const Icon = style.icon;
                        const isExpanded = !!expandedItemIds[item.id];

                        return (
                          <div
                            key={item.id}
                            className={`overflow-hidden rounded-2xl border transition ${
                              isExpanded
                                ? "border-[#4d6bfe]/35 bg-white shadow-xs"
                                : "border-black/[0.06] bg-[#fbfbfd]/80 hover:border-black/[0.12] hover:bg-white"
                            }`}
                          >
                            {/* Interactive Summary Row */}
                            <button
                              type="button"
                              onClick={() => toggleItemExpand(item.id)}
                              className="flex w-full items-center justify-between gap-4 px-4 py-3.5 text-left"
                            >
                              <div className="flex min-w-0 flex-1 items-center gap-3.5">
                                <div
                                  className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${style.tint}`}
                                >
                                  <Icon className="h-4 w-4 stroke-[2]" />
                                </div>

                                <div className="min-w-0 flex-1">
                                  <div className="flex items-center gap-2">
                                    <span className="truncate text-[14px] font-semibold text-[#1d1d1f]">
                                      {item.label}
                                    </span>
                                    <span className="rounded-md bg-black/[0.04] px-1.5 py-0.5 text-[10.5px] font-medium text-[#515154]">
                                      {style.label}
                                    </span>
                                  </div>

                                  {/* Proportional Share Bar */}
                                  <div className="mt-1.5 flex items-center gap-2.5">
                                    <div className="h-1.5 w-28 overflow-hidden rounded-full bg-black/[0.06] sm:w-40">
                                      <div
                                        className={`h-full rounded-full ${style.barColor}`}
                                        style={{
                                          width: `${Math.min(
                                            100,
                                            Math.max(6, item.share_of_turn_pct)
                                          )}%`,
                                        }}
                                      />
                                    </div>
                                    <span className="ds-mono text-[11px] text-[#86868b]">
                                      {item.share_of_turn_pct.toFixed(1)}% of turn
                                    </span>
                                  </div>
                                </div>
                              </div>

                              <div className="flex items-center gap-3 shrink-0">
                                <div className="text-right">
                                  <div className="ds-mono text-[16px] font-semibold text-[#1d1d1f]">
                                    {item.kg_co2e.toFixed(3)}{" "}
                                    <span className="text-[11.5px] font-normal text-[#86868b]">
                                      kg CO₂e
                                    </span>
                                  </div>
                                  <div className="text-[10.5px] text-[#4d6bfe]">
                                    {isExpanded ? "Hide math" : "Inspect math"}
                                  </div>
                                </div>
                                {isExpanded ? (
                                  <ChevronDown className="h-4 w-4 text-[#86868b]" />
                                ) : (
                                  <ChevronRight className="h-4 w-4 text-[#86868b]" />
                                )}
                              </div>
                            </button>

                            {/* Expanded Interactive Math & Equivalencies Drawer */}
                            {isExpanded && (
                              <div className="border-t border-black/[0.05] bg-[#f5f5f7]/55 px-4 py-3.5 space-y-3">
                                {/* Step-by-Step Math Pills */}
                                <div>
                                  <div className="mb-1.5 text-[10.5px] font-semibold tracking-wider text-[#86868b] uppercase">
                                    Deterministic Formula Pipeline
                                  </div>
                                  <div className="flex flex-wrap items-center gap-1.5">
                                    <span className="ds-mono rounded-lg border border-black/[0.06] bg-white px-2.5 py-1 text-[12px] font-medium text-[#1d1d1f]">
                                      Qty: {item.quantity} {item.unit}
                                    </span>
                                    <ArrowRight className="h-3.5 w-3.5 text-[#86868b]" />
                                    {item.math_steps.map((step, sIdx) => (
                                      <React.Fragment key={sIdx}>
                                        <span
                                          className={`ds-mono rounded-lg border px-2.5 py-1 text-[12px] ${
                                            sIdx === item.math_steps.length - 1
                                              ? "border-[#4d6bfe]/30 bg-[#4d6bfe]/[0.08] font-semibold text-[#3b5bfd]"
                                              : "border-black/[0.06] bg-white text-[#515154]"
                                          }`}
                                        >
                                          {step}
                                        </span>
                                        {sIdx < item.math_steps.length - 1 && (
                                          <ArrowRight className="h-3.5 w-3.5 text-[#86868b]" />
                                        )}
                                      </React.Fragment>
                                    ))}
                                  </div>
                                </div>

                                {/* Real-World Tangibility Equivalencies */}
                                <div className="grid grid-cols-3 gap-2 pt-0.5">
                                  <div className="flex items-center gap-2 rounded-xl border border-black/[0.05] bg-white px-3 py-2">
                                    <Smartphone className="h-3.5 w-3.5 text-[#4d6bfe] shrink-0" />
                                    <div>
                                      <div className="ds-mono text-[12px] font-semibold text-[#1d1d1f]">
                                        ≈ {item.equivalents.smartphones_charged}
                                      </div>
                                      <div className="text-[10px] text-[#86868b]">
                                        Phones charged
                                      </div>
                                    </div>
                                  </div>

                                  <div className="flex items-center gap-2 rounded-xl border border-black/[0.05] bg-white px-3 py-2">
                                    <Car className="h-3.5 w-3.5 text-amber-600 shrink-0" />
                                    <div>
                                      <div className="ds-mono text-[12px] font-semibold text-[#1d1d1f]">
                                        ≈ {item.equivalents.petrol_car_km} km
                                      </div>
                                      <div className="text-[10px] text-[#86868b]">
                                        Petrol car drive
                                      </div>
                                    </div>
                                  </div>

                                  <div className="flex items-center gap-2 rounded-xl border border-black/[0.05] bg-white px-3 py-2">
                                    <TreePine className="h-3.5 w-3.5 text-[#34c759] shrink-0" />
                                    <div>
                                      <div className="ds-mono text-[12px] font-semibold text-[#1d1d1f]">
                                        ≈ {item.equivalents.tree_absorption_days} d
                                      </div>
                                      <div className="text-[10px] text-[#86868b]">
                                        1 tree absorption
                                      </div>
                                    </div>
                                  </div>
                                </div>

                                {/* Source Citation Footer */}
                                {liveSourcesOn && (
                                  <div className="flex items-center justify-between text-[11px] text-[#86868b] pt-0.5">
                                    <span>Source: {item.source}</span>
                                    <span className="ds-mono text-[#34c759] font-medium">
                                      ✓ Zero-Hallucination Verified
                                    </span>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* ─────────── MODULE C: Interactive Daily Footprint Spectrum & Category Bar ─────────── */}
                {(activeOutputSection === "all" ||
                  activeOutputSection === "footprint") && (
                  <div className="apple-surface overflow-hidden rounded-[24px] p-6">
                    <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#34c759]/[0.12] text-[#248a3d]">
                          <Gauge className="h-4 w-4" />
                        </div>
                        <div>
                          <h3 className="ds-heading text-[15px] font-semibold text-[#1d1d1f]">
                            Daily Footprint & Benchmark Spectrum
                          </h3>
                          <p className="text-[11.5px] text-[#86868b]">
                            Click any category pill to filter itemized breakdown • Live gauge responds to simulated savings
                          </p>
                        </div>
                      </div>

                      <div className="ds-mono text-right text-[12.5px]">
                        <span className="text-[#86868b]">Active Daily: </span>
                        <strong className="text-[#1d1d1f]">
                          {simulatedDailyKg.toFixed(3)} kg CO₂e
                        </strong>
                      </div>
                    </div>

                    {/* 1. Interactive Stacked Category Bar */}
                    {report.daily_footprint.category_distribution.length > 0 && (
                      <div className="mb-6">
                        <div className="flex h-3 w-full overflow-hidden rounded-full bg-black/[0.05] p-0.5 gap-0.5">
                          {report.daily_footprint.category_distribution.map(
                            (cat) => {
                              const style = getCategoryStyle(cat.category);
                              return (
                                <button
                                  key={cat.category}
                                  type="button"
                                  onClick={() =>
                                    setSelectedCategoryFilter((prev) =>
                                      prev === cat.category ? null : cat.category
                                    )
                                  }
                                  title={`${style.label}: ${cat.kg_co2e} kg (${cat.share_percent}%)`}
                                  className={`h-full first:rounded-l-full last:rounded-r-full transition-all hover:opacity-80 ${style.barColor}`}
                                  style={{
                                    width: `${Math.max(5, cat.share_percent)}%`,
                                  }}
                                />
                              );
                            }
                          )}
                        </div>

                        {/* Interactive Category Legend Pills */}
                        <div className="mt-2.5 flex flex-wrap gap-2">
                          {report.daily_footprint.category_distribution.map(
                            (cat) => {
                              const style = getCategoryStyle(cat.category);
                              const isSelected =
                                selectedCategoryFilter === cat.category;
                              return (
                                <button
                                  key={cat.category}
                                  type="button"
                                  onClick={() =>
                                    setSelectedCategoryFilter((prev) =>
                                      prev === cat.category ? null : cat.category
                                    )
                                  }
                                  className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11.5px] transition ${
                                    isSelected
                                      ? "border-[#4d6bfe] bg-[#4d6bfe]/[0.08] font-semibold text-[#1d1d1f]"
                                      : "border-black/[0.06] bg-[#fbfbfd] text-[#515154] hover:bg-white"
                                  }`}
                                >
                                  <span
                                    className={`h-2 w-2 rounded-full ${style.dotColor}`}
                                  />
                                  <span>{style.label}</span>
                                  <span className="ds-mono font-semibold text-[#1d1d1f]">
                                    {cat.kg_co2e.toFixed(2)} kg
                                  </span>
                                  <span className="ds-mono text-[10.5px] text-[#86868b]">
                                    ({cat.share_percent}%)
                                  </span>
                                </button>
                              );
                            }
                          )}
                        </div>
                      </div>
                    )}

                    {/* 2. Interactive Benchmark Comparison Cards (Live Updated with Simulated Footprint!) */}
                    <div className="grid gap-3 sm:grid-cols-2">
                      {report.daily_footprint.benchmarks.map((bm) => {
                        const liveDelta = Number(
                          (simulatedDailyKg - bm.target_kg).toFixed(2)
                        );
                        const isUnder = liveDelta <= 0;
                        const fillPct = Math.min(
                          100,
                          Math.round((simulatedDailyKg / bm.target_kg) * 100)
                        );
                        const basePct = Math.min(
                          100,
                          Math.round((baselineDailyKg / bm.target_kg) * 100)
                        );

                        return (
                          <div
                            key={bm.key}
                            className="rounded-2xl border border-black/[0.06] bg-[#fbfbfd] p-3.5"
                          >
                            <div className="flex items-center justify-between gap-2 text-[12.5px]">
                              <span className="font-semibold text-[#1d1d1f]">
                                {bm.short_label}
                              </span>
                              <span
                                className={`ds-mono rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                                  isUnder
                                    ? "bg-[#34c759]/[0.12] text-[#248a3d]"
                                    : "bg-amber-500/[0.12] text-amber-700"
                                }`}
                              >
                                {isUnder
                                  ? `${Math.abs(liveDelta).toFixed(2)} kg under`
                                  : `+${liveDelta.toFixed(2)} kg over`}
                              </span>
                            </div>

                            {/* Dual Progress Track (Shows Baseline Ghost Marker + Simulated Bar) */}
                            <div className="relative mt-2.5 h-2 w-full overflow-hidden rounded-full bg-black/[0.06]">
                              {activeSimulatedSavingKg > 0 && (
                                <div
                                  className="absolute inset-y-0 left-0 rounded-full bg-black/[0.12] transition-all duration-300"
                                  style={{ width: `${basePct}%` }}
                                />
                              )}
                              <div
                                className={`relative h-full rounded-full transition-all duration-500 ${
                                  isUnder ? "bg-[#4d6bfe]" : "bg-amber-500"
                                }`}
                                style={{ width: `${fillPct}%` }}
                              />
                            </div>

                            <div className="mt-1.5 flex items-center justify-between text-[11px] text-[#86868b]">
                              <span className="ds-mono">
                                You: <strong>{simulatedDailyKg.toFixed(2)} kg</strong>{" "}
                                ({fillPct}%)
                              </span>
                              <span className="ds-mono">
                                Target: <strong>{bm.target_kg.toFixed(2)} kg/d</strong>
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* 3. Interactive What-If Reduction Switches */}
                    {report.interactive_actions.length > 0 && (
                      <div className="mt-6 border-t border-black/[0.05] pt-5">
                        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                          <div>
                            <span className="text-[11px] font-semibold tracking-wider text-[#86868b] uppercase">
                              Interactive What-If Savings Simulator
                            </span>
                            <p className="text-[12px] text-[#515154]">
                              Toggle switches to simulate how recommended actions reduce your daily footprint
                            </p>
                          </div>
                          <span className="inline-flex items-center gap-1 rounded-full bg-[#34c759]/[0.12] px-3 py-1 text-[11.5px] font-semibold text-[#248a3d]">
                            <TrendingDown className="h-3.5 w-3.5" />
                            Simulating -{activeSimulatedSavingKg.toFixed(3)} kg/day
                          </span>
                        </div>

                        <div className="space-y-2.5">
                          {report.interactive_actions.map((act) => {
                            const isOn = !!simulatedActionIds[act.id];
                            return (
                              <div
                                key={act.id}
                                onClick={() => toggleSimulatedAction(act.id)}
                                className={`flex cursor-pointer items-start justify-between gap-4 rounded-2xl border p-3.5 transition ${
                                  isOn
                                    ? "border-[#34c759]/40 bg-[#34c759]/[0.04]"
                                    : "border-black/[0.06] bg-white hover:border-black/[0.12]"
                                }`}
                              >
                                <div className="min-w-0 flex-1">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="rounded-md bg-black/[0.05] px-2 py-0.5 text-[10.5px] font-semibold text-[#515154]">
                                      {act.target_activity}
                                    </span>
                                    <span className="ds-mono text-[11px] font-semibold text-[#248a3d]">
                                      -{act.daily_saving_kg.toFixed(3)} kg/day (
                                      {act.annual_saving_kg.toFixed(0)} kg/yr)
                                    </span>
                                  </div>
                                  <div className="mt-1 text-[13.5px] font-medium text-[#1d1d1f]">
                                    {act.action_title}
                                  </div>
                                  <div className="ds-mono mt-1 text-[11px] text-[#86868b]">
                                    {act.formula}
                                  </div>
                                </div>

                                {/* Apple-Style Toggle Switch */}
                                <button
                                  type="button"
                                  role="switch"
                                  aria-checked={isOn}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleSimulatedAction(act.id);
                                  }}
                                  className={`mt-1 inline-flex h-6 w-11 shrink-0 items-center rounded-full p-0.5 transition-colors ${
                                    isOn ? "bg-[#34c759]" : "bg-black/[0.15]"
                                  }`}
                                >
                                  <span
                                    className={`h-5 w-5 rounded-full bg-white shadow-xs transition-transform ${
                                      isOn ? "translate-x-5" : "translate-x-0"
                                    }`}
                                  />
                                </button>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* ─────────── MODULE D: Verified Google ADK Tool Execution Trace ─────────── */}
                {(activeOutputSection === "all" ||
                  activeOutputSection === "audit") &&
                  deepAuditOn && (
                    <div className="apple-surface overflow-hidden rounded-[24px] p-5">
                      <div className="mb-3 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Terminal className="h-4 w-4 text-[#4d6bfe]" />
                          <span className="text-[12px] font-semibold text-[#1d1d1f]">
                            Verified Google ADK Tool Trace
                          </span>
                        </div>
                        <span className="ds-mono rounded-full bg-[#4d6bfe]/[0.08] px-2.5 py-0.5 text-[11px] font-medium text-[#3b5bfd]">
                          {activeTurn.engine}
                        </span>
                      </div>

                      <div className="space-y-1.5">
                        {activeTurn.toolTrace
                          .filter((t) => t.type === "tool_call")
                          .map((call, idx) => {
                            const matchingResult = activeTurn.toolTrace.find(
                              (r) =>
                                r.type === "tool_result" &&
                                r.tool_name === call.tool_name &&
                                r !== call
                            );
                            return (
                              <div
                                key={`${call.tool_name}-${idx}`}
                                className="flex flex-col justify-between gap-1 rounded-xl border border-black/[0.05] bg-[#fbfbfd] px-3.5 py-2 text-[12px] sm:flex-row sm:items-center"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="h-1.5 w-1.5 rounded-full bg-[#34c759]" />
                                  <span className="ds-mono font-semibold text-[#1d1d1f]">
                                    {call.tool_name}
                                  </span>
                                  <span className="ds-mono text-[11px] text-[#86868b]">
                                    {JSON.stringify(call.args)}
                                  </span>
                                </div>
                                {matchingResult?.result?.formula ? (
                                  <span className="ds-mono text-[11px] font-medium text-[#4d6bfe]">
                                    {String(matchingResult.result.formula)}
                                  </span>
                                ) : (
                                  <span className="ds-mono text-[11px] text-[#248a3d]">
                                    ✓ Verified Output
                                  </span>
                                )}
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  )}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
