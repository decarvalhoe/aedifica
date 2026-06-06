"use client";
import { useEffect, useMemo, useRef, useState } from "react";
// frappe-gantt's package.json exports the CSS under the package style key, but
// not as a direct CSS sub-path import. We pull it from the dist folder directly.
import "../../node_modules/frappe-gantt/dist/frappe-gantt.css";

// W11.C + W14.C.3 — multi-project Gantt over the atelier's task pool.
// W14.C.3 fixes the "écrasé, inutilisable" critique:
//   - Explicit zoom toggle (Jour / Semaine / Mois / Trimestre + Auto)
//   - Default view_mode auto-selected from the date span (no more multi-year
//     plan squashed into a Week view, no more 1-week plan stretched into Month)
//   - Visible horizontal scroll container with a min-height so single-row
//     plans don't collapse into nothing
//   - Per-project legend up top so the architect knows which color is which
//   - Bigger bar height + padding for legibility

export type AtelierTask = {
  id: number; title: string; status: string; priority: string;
  estimate_hours?: number | null; due_date?: string | null;
  blocked_by?: number[]; is_quick_win?: boolean; is_blocked?: boolean;
  project_id: string; project_name: string; assignee?: string | null;
};

const PROGRESS: Record<string, number> = { todo: 0, doing: 50, blocked: 30, done: 100 };

type ViewMode = "Day" | "Week" | "Month" | "Quarter Day";

function addDays(d: Date, days: number): Date {
  const x = new Date(d); x.setDate(x.getDate() + days); return x;
}
function toISODate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

// Pick a sensible default view_mode based on the date span. Avoids the
// "100-task year-long plan squashed into Week view" trap the user saw.
function autoViewMode(rows: { start: string; end: string }[]): ViewMode {
  if (rows.length === 0) return "Week";
  const starts = rows.map((r) => new Date(r.start).getTime()).filter((n) => !isNaN(n));
  const ends = rows.map((r) => new Date(r.end).getTime()).filter((n) => !isNaN(n));
  if (starts.length === 0 || ends.length === 0) return "Week";
  const min = Math.min(...starts); const max = Math.max(...ends);
  const days = Math.max(1, Math.round((max - min) / 86400000));
  if (days <= 14) return "Day";
  if (days <= 90) return "Week";
  if (days <= 365) return "Month";
  return "Quarter Day"; // frappe-gantt's roughest zoom — fits multi-year plans
}

// Stable, color-blind-friendly palette tied to the Datum state squares.
// Each project_id deterministically maps to one slot via simple hash modulo.
const PROJECT_PALETTE = [
  "#4F7B3A", "#C0392B", "#2C3E50", "#7C6A2B",
  "#B7723A", "#3F6B8C", "#7A2E5B", "#566D2D",
];
function projectColor(pid: string): string {
  let h = 0;
  for (const c of pid) h = ((h << 5) - h + c.charCodeAt(0)) | 0;
  return PROJECT_PALETTE[Math.abs(h) % PROJECT_PALETTE.length];
}
export { projectColor };

export function GanttView({ tasks, onPatch }: {
  tasks: AtelierTask[];
  onPatch: (project_id: string, task_id: number, body: any) => Promise<any>;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const styleRef = useRef<HTMLStyleElement | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode | "auto">("auto");

  const plotted = tasks.filter((t) => !!t.due_date);
  const skipped = tasks.filter((t) => !t.due_date);

  // Group projects so we can stamp per-project CSS rules into the doc head.
  const palette: Record<string, string> = useMemo(() => {
    const p: Record<string, string> = {};
    for (const t of tasks) p[t.project_id] = projectColor(t.project_id);
    return p;
  }, [tasks]);
  // Stable label for the legend: first project_name we see for each id.
  const projectNames: Record<string, string> = useMemo(() => {
    const n: Record<string, string> = {};
    for (const t of tasks) { if (!n[t.project_id]) n[t.project_id] = t.project_name || t.project_id; }
    return n;
  }, [tasks]);

  // W15 fix — the previous formula `-(max(1, ceil(eh/8))) + 1` produced
  // start === end for the most common case (estimate_hours = 8 = 1 day),
  // which frappe-gantt renders as a zero-width bar (invisible). The user:
  // "le rendu gantt est ridicule et inutilisable". Now: start = due - days,
  // end = due, guaranteeing at least 1 day of visible width.
  const rows = useMemo(() => plotted.map((t) => {
    const due = new Date(t.due_date!);
    const days = Math.max(1, Math.ceil((Number(t.estimate_hours) || 8) / 8));
    return {
      id: `${t.project_id}::${t.id}`,
      name: `${t.title}  ·  ${t.project_name}`,
      start: toISODate(addDays(due, -days)),
      end: toISODate(due),
      progress: PROGRESS[t.status] ?? 0,
      dependencies: (t.blocked_by || []).map((d) => `${t.project_id}::${d}`).join(","),
      custom_class: `gp-${t.project_id.replace(/[^A-Za-z0-9_-]/g, "_")}`,
    };
  }), [plotted]);

  const effectiveMode: ViewMode = viewMode === "auto" ? autoViewMode(rows) : viewMode;

  useEffect(() => {
    // Inject per-project bar colors as a <style> tag — frappe-gantt honors
    // custom_class on each bar's outer group.
    if (typeof document === "undefined") return;
    if (!styleRef.current) {
      const s = document.createElement("style");
      s.dataset.scope = "aedifica-gantt-colors";
      document.head.appendChild(s);
      styleRef.current = s;
    }
    styleRef.current.textContent = Object.entries(palette).map(([pid, color]) => {
      const cls = `gp-${pid.replace(/[^A-Za-z0-9_-]/g, "_")}`;
      return `.${cls} .bar { fill: ${color}; stroke: ${color}; }`
           + ` .${cls} .bar-progress { fill: ${color}; opacity: 0.55; }`;
    }).join("\n");
  }, [palette]);

  useEffect(() => {
    let cancelled = false;
    if (!ref.current || rows.length === 0) return;
    (async () => {
      const mod: any = await import("frappe-gantt");
      if (cancelled || !ref.current) return;
      ref.current.innerHTML = "<svg></svg>";
      const svg = ref.current.firstChild as SVGElement;
      const Gantt = mod.default || mod;
      new Gantt(svg, rows, {
        view_mode: effectiveMode,
        bar_height: 26,
        padding: 22,
        language: "fr",
        on_date_change: async (task: any, start: Date, end: Date) => {
          const [pid, tidRaw] = String(task.id).split("::");
          const tid = parseInt(tidRaw, 10);
          if (!pid || isNaN(tid)) return;
          const days = Math.max(1, Math.round((end.getTime() - start.getTime()) / 86400000) + 1);
          try { await onPatch(pid, tid, { due_date: toISODate(end), estimate_hours: days * 8 }); }
          catch { /* surfaced by parent */ }
        },
        on_progress_change: async (task: any, progress: number) => {
          const [pid, tidRaw] = String(task.id).split("::");
          const tid = parseInt(tidRaw, 10);
          if (!pid || isNaN(tid)) return;
          const status = progress >= 100 ? "done" : progress >= 70 ? "blocked" : progress > 0 ? "doing" : "todo";
          try { await onPatch(pid, tid, { status }); }
          catch { }
        },
      });
      // W15 fix — frappe-gantt's SVG is much wider than the visible
      // container (it covers the whole project span); by default it
      // shows from "today + start_padding", which can leave the only
      // bar off-screen to the right. Auto-scroll the overflow container
      // so the first bar sits in the left third of the viewport.
      // Delay by one frame so the SVG is fully painted.
      requestAnimationFrame(() => {
        if (cancelled || !ref.current) return;
        const firstBar = svg.querySelector(".bar") as SVGRectElement | null;
        if (!firstBar) return;
        // The scrollable container is the parent of ref (we wrap the
        // <div ref> in an `overflow: auto` div in JSX below).
        const scroller = ref.current.parentElement;
        if (!scroller || scroller.scrollWidth <= scroller.clientWidth) return;
        const barRect = firstBar.getBoundingClientRect();
        const scRect = scroller.getBoundingClientRect();
        // Distance from the visible left edge to the bar.
        const offset = (barRect.left - scRect.left) + scroller.scrollLeft;
        // Position the bar at ~1/4 of the viewport (gives the user some
        // history context to the left + plenty of room to the right).
        const target = Math.max(0, offset - scroller.clientWidth * 0.25);
        scroller.scrollLeft = target;
      });
    })();
    return () => { cancelled = true; };
  }, [rows, effectiveMode, onPatch]);

  if (rows.length === 0) {
    return (
      <div className="card" style={{ borderLeft: "3px solid var(--ts-assume)" }}>
        <h3 style={{ margin: 0 }}>Aucune tâche datée dans l&apos;atelier</h3>
        <p>
          Le Gantt n&apos;a rien à dessiner tant qu&apos;aucune tâche n&apos;a d&apos;échéance. Pour faire apparaître des barres :
        </p>
        <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
          <li>Ouvrez un projet → <i>Tâches &amp; priorités</i></li>
          <li>Sur chaque tâche, renseignez une <b>échéance</b> et idéalement une <b>estimation en heures</b> (la durée de la barre = heures / 8 jours, minimum 1 jour)</li>
          <li>Revenez ici — la barre apparaîtra avec la couleur du projet</li>
        </ul>
        {skipped.length > 0 && (
          <p className="note" style={{ color: "var(--mut)", marginTop: 6 }}>
            {skipped.length} tâche{skipped.length > 1 ? "s" : ""} actuellement <b>sans échéance</b>.
          </p>
        )}
      </div>
    );
  }

  return (
    <>
      {/* Toolbar: zoom toggle + auto-mode badge */}
      <div className="row" style={{ alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <span className="mono" style={{ fontSize: 11, color: "var(--mut)", letterSpacing: ".08em", textTransform: "uppercase" }}>Zoom</span>
        {(["auto", "Day", "Week", "Month", "Quarter Day"] as const).map((m) => {
          const lb = m === "auto" ? "Auto"
                   : m === "Quarter Day" ? "Trimestre"
                   : m === "Month" ? "Mois"
                   : m === "Week" ? "Semaine" : "Jour";
          return (
            <button key={m} className={`toggle ${viewMode === m ? "on" : ""}`}
                    style={{ padding: "3px 9px", fontSize: 11 }}
                    onClick={() => setViewMode(m)}>{lb}</button>
          );
        })}
        <span className="grow" />
        <small style={{ color: "var(--mut)" }}>
          {viewMode === "auto"
            ? `auto → ${effectiveMode === "Quarter Day" ? "trimestre" : effectiveMode === "Month" ? "mois" : effectiveMode === "Week" ? "semaine" : "jour"}`
            : "manuel"} · {rows.length} tâche{rows.length > 1 ? "s" : ""} datée{rows.length > 1 ? "s" : ""}
        </small>
      </div>
      {/* Per-project color legend */}
      <div className="row" style={{ gap: 14, flexWrap: "wrap", marginBottom: 10 }}>
        {Object.entries(projectNames).map(([pid, name]) => (
          <span key={pid} className="row" style={{ gap: 6, alignItems: "center", fontSize: 12 }}>
            <span style={{ width: 14, height: 12, background: palette[pid], border: "1px solid var(--ink)", display: "inline-block" }} />
            <span>{name}</span>
          </span>
        ))}
      </div>
      {/* The Gantt itself — explicit min-height so a single-row plan doesn't
          collapse, and forced horizontal overflow with a visible scrollbar
          so the architect can scroll long timelines. */}
      <div style={{
        overflow: "auto",
        minHeight: Math.max(220, rows.length * 36 + 80),
        border: "1px solid var(--line)",
        background: "var(--surface)",
      }}>
        <div ref={ref} />
      </div>
      {skipped.length > 0 && (
        <p style={{ fontSize: 12, color: "var(--mut)", marginTop: 12 }}>
          {skipped.length} tâche{skipped.length > 1 ? "s" : ""} sans échéance — non affichée{skipped.length > 1 ? "s" : ""}.
        </p>
      )}
    </>
  );
}
