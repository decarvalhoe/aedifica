"use client";
import { useState } from "react";
import { projectColor, type AtelierTask } from "./GanttView";

// W11.C: multi-project Kanban — 4 columns × all-projects tasks. Cards carry
// a small project-color strip on the left + the project name as a chip, so
// you can balance Atelier Carré-Neuf vs Atelier Untel at a glance. Drag &
// drop changes the status; the PATCH targets the right project_id.

const COLS: { id: string; label: string }[] = [
  { id: "todo", label: "À faire" },
  { id: "doing", label: "En cours" },
  { id: "blocked", label: "Bloquées" },
  { id: "done", label: "Faites" },
];
const PRIO_CHIP: Record<string, string> = { p0: "is-conflict", p1: "is-assume", p2: "is-sourced" };

export function KanbanView({ tasks, onPatch, onDel }: {
  tasks: AtelierTask[];
  onPatch: (project_id: string, task_id: number, body: any) => Promise<any>;
  onDel: (project_id: string, task_id: number) => Promise<any>;
}) {
  const [dragKey, setDragKey] = useState<string | null>(null);
  const [over, setOver] = useState<string | null>(null);

  async function drop(col: string) {
    if (!dragKey) return;
    const [pid, tidRaw] = dragKey.split("::");
    const tid = parseInt(tidRaw, 10);
    const t = tasks.find((x) => x.project_id === pid && x.id === tid);
    if (!t || t.status === col) { setDragKey(null); setOver(null); return; }
    try { await onPatch(pid, tid, { status: col }); }
    finally { setDragKey(null); setOver(null); }
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
      {COLS.map((col) => {
        const rows = tasks.filter((t) => t.status === col.id);
        const onOver = over === col.id;
        return (
          <div key={col.id}
               onDragOver={(e) => { e.preventDefault(); setOver(col.id); }}
               onDragLeave={() => setOver((c) => c === col.id ? null : c)}
               onDrop={() => drop(col.id)}
               style={{ background: onOver ? "rgba(192,57,43,0.06)" : "rgba(0,0,0,0.02)",
                        border: `1px dashed ${onOver ? "var(--accent)" : "var(--line)"}`,
                        padding: 10, minHeight: 200 }}>
            <div className="mono" style={{ fontSize: 11, letterSpacing: ".08em",
                                            textTransform: "uppercase",
                                            color: "var(--mut)", marginBottom: 6 }}>
              {col.label} <small>({rows.length})</small>
            </div>
            {rows.length === 0 && <div className="spin" style={{ fontSize: 12 }}>—</div>}
            {rows.map((t) => {
              const key = `${t.project_id}::${t.id}`;
              const color = projectColor(t.project_id);
              return (
                <div key={key}
                     draggable
                     onDragStart={() => setDragKey(key)}
                     onDragEnd={() => { setDragKey(null); setOver(null); }}
                     className="card"
                     style={{ marginBottom: 6, padding: "8px 10px 8px 12px", cursor: "grab",
                              opacity: dragKey === key ? 0.5 : 1, background: "var(--surface-2)",
                              borderLeft: `3px solid ${color}` }}>
                  <div className="row" style={{ alignItems: "flex-start", gap: 6 }}>
                    <span className={`ds-ts ${PRIO_CHIP[t.priority] || "is-unknown"}`}
                          style={{ fontSize: 9 }}>
                      <span className="dot" />{t.priority?.toUpperCase()}
                    </span>
                    <span style={{ flex: 1, fontSize: 13, fontWeight: 500 }}>{t.title}</span>
                    <button className="signout" style={{ padding: 0, fontSize: 14 }}
                            title="Supprimer"
                            onClick={(e) => { e.stopPropagation(); onDel(t.project_id, t.id); }}>×</button>
                  </div>
                  <small style={{ color: "var(--mut)", fontSize: 11, display: "block", marginTop: 2 }}>
                    <span className="chip" style={{ marginRight: 4, fontSize: 9 }}>{t.project_name}</span>
                    {[
                      t.assignee ? "→ " + t.assignee : null,
                      t.estimate_hours ? t.estimate_hours + " h" : null,
                      t.due_date ? "éch. " + t.due_date : null,
                      t.is_quick_win ? "quick win" : null,
                      t.is_blocked ? "dépend de…" : null,
                    ].filter(Boolean).join(" · ")}
                  </small>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
