"use client";
import { useEffect, useRef } from "react";
// frappe-gantt's package.json exports the CSS under the package style key, but
// not as a direct CSS sub-path import. We pull it from the dist folder directly.
import "../../node_modules/frappe-gantt/dist/frappe-gantt.css";

// W11.C: multi-project Gantt over the atelier's task pool. Powered by
// MIT-licensed `frappe-gantt` (vanilla JS) mounted on an SVG via ref. Each
// bar carries the project's color so cross-project collisions are visible
// at a glance. Status → progress: todo 0, doing 50, blocked 30, done 100.
// Tasks without a due_date can't be plotted; they're noted with a banner.

export type AtelierTask = {
  id: number; title: string; status: string; priority: string;
  estimate_hours?: number | null; due_date?: string | null;
  blocked_by?: number[]; is_quick_win?: boolean; is_blocked?: boolean;
  project_id: string; project_name: string; assignee?: string | null;
};

const PROGRESS: Record<string, number> = { todo: 0, doing: 50, blocked: 30, done: 100 };

function addDays(d: Date, days: number): Date {
  const x = new Date(d); x.setDate(x.getDate() + days); return x;
}
function toISODate(d: Date): string {
  return d.toISOString().slice(0, 10);
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

  const plotted = tasks.filter((t) => !!t.due_date);
  const skipped = tasks.filter((t) => !t.due_date);

  // Group projects so we can stamp per-project CSS rules into the doc head.
  const palette: Record<string, string> = {};
  for (const t of tasks) palette[t.project_id] = projectColor(t.project_id);

  const rows = plotted.map((t) => ({
    id: `${t.project_id}::${t.id}`,
    name: `${t.title}  ·  ${t.project_name}`,
    start: toISODate(addDays(new Date(t.due_date!), -(Math.max(1, Math.ceil((t.estimate_hours || 8) / 8))) + 1)),
    end: toISODate(new Date(t.due_date!)),
    progress: PROGRESS[t.status] ?? 0,
    dependencies: (t.blocked_by || []).map((d) => `${t.project_id}::${d}`).join(","),
    custom_class: `gp-${t.project_id.replace(/[^A-Za-z0-9_-]/g, "_")}`,
  }));

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
  }, [JSON.stringify(palette)]);

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
        view_mode: "Week",
        bar_height: 22,
        padding: 16,
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
    })();
    return () => { cancelled = true; };
  }, [JSON.stringify(rows)]);

  return (
    <>
      {rows.length === 0 ? (
        <p className="spin">Aucune tâche datée dans l&apos;atelier. Renseignez une <b>échéance</b> sur les tâches pour les voir sur le Gantt.</p>
      ) : (
        <div ref={ref} style={{ overflow: "auto" }} />
      )}
      {skipped.length > 0 && (
        <p style={{ fontSize: 12, color: "var(--mut)", marginTop: 12 }}>
          {skipped.length} tâche{skipped.length > 1 ? "s" : ""} sans échéance — non affichée{skipped.length > 1 ? "s" : ""}.
        </p>
      )}
    </>
  );
}
