"use client";
import { useMemo, useState } from "react";
import { projectColor, type AtelierTask } from "./GanttView";

// W11.C + W15.A — multi-project Kanban. 4 columns × all atelier tasks.
// Cards carry a project-color strip on the left + the project name as a
// chip, so you can balance Atelier Carré-Neuf vs Atelier Untel at a glance.
// Drag & drop changes the status; the PATCH targets the right project_id.
//
// W15.A scalability pass: search + per-column counts + density toggle so
// the surface stays usable past 50 cards.

const COLS: { id: string; label: string; description: string }[] = [
  { id: "todo", label: "À faire", description: "À démarrer" },
  { id: "doing", label: "En cours", description: "En cours d'exécution" },
  { id: "blocked", label: "Bloquées", description: "En attente d'un déblocage" },
  { id: "done", label: "Faites", description: "Achevées" },
];
const PRIO_CHIP: Record<string, string> = { p0: "is-conflict", p1: "is-assume", p2: "is-sourced" };

export function KanbanView({ tasks, onPatch, onDel }: {
  tasks: AtelierTask[];
  onPatch: (project_id: string, task_id: number, body: any) => Promise<any>;
  onDel: (project_id: string, task_id: number) => Promise<any>;
}) {
  const [dragKey, setDragKey] = useState<string | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [density, setDensity] = useState<"compact" | "spacieux">("spacieux");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return tasks;
    return tasks.filter((t) => {
      const hay = `${t.title} ${t.project_name || ""} ${t.assignee || ""}`.toLowerCase();
      return hay.includes(q);
    });
  }, [tasks, search]);

  async function drop(col: string) {
    if (!dragKey) return;
    const [pid, tidRaw] = dragKey.split("::");
    const tid = parseInt(tidRaw, 10);
    const t = tasks.find((x) => x.project_id === pid && x.id === tid);
    if (!t || t.status === col) { setDragKey(null); setOver(null); return; }
    try { await onPatch(pid, tid, { status: col }); }
    finally { setDragKey(null); setOver(null); }
  }

  const cardPad = density === "compact" ? "5px 8px 5px 10px" : "8px 10px 8px 12px";
  const cardGap = density === "compact" ? 4 : 6;
  const titleSize = density === "compact" ? 12 : 13;

  return (
    <>
      {/* W15.A — toolbar: search + density toggle. Columns flex-wrap so 4-up
          on wide screens, 2x2 on tablet, 1-up on phone (auto-fit minmax 220). */}
      <div className="row" style={{ gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 12 }}>
        <input className="fld" style={{ margin: 0, padding: "5px 9px", flex: "1 1 240px" }}
               placeholder="Filtrer (titre, projet, assignee)…"
               value={search} onChange={(e) => setSearch(e.target.value)} />
        <span className="row" style={{ gap: 4 }}>
          <span className="mono" style={{ fontSize: 11, color: "var(--mut)", letterSpacing: ".08em", textTransform: "uppercase", marginRight: 4 }}>Densité</span>
          {(["spacieux", "compact"] as const).map((m) => (
            <button key={m} className={`toggle ${density === m ? "on" : ""}`} style={{ padding: "3px 9px", fontSize: 11 }} onClick={() => setDensity(m)}>
              {m === "spacieux" ? "Spacieux" : "Compact"}
            </button>
          ))}
        </span>
        <small className="mono" style={{ color: "var(--mut)", marginLeft: "auto" }}>
          {filtered.length}/{tasks.length} tâche{tasks.length > 1 ? "s" : ""}
        </small>
      </div>
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        gap: 12,
      }}>
        {COLS.map((col) => {
          const rows = filtered.filter((t) => t.status === col.id);
          const totalInStatus = tasks.filter((t) => t.status === col.id).length;
          const onOver = over === col.id;
          return (
            <div key={col.id}
                 onDragOver={(e) => { e.preventDefault(); setOver(col.id); }}
                 onDragLeave={() => setOver((c) => c === col.id ? null : c)}
                 onDrop={() => drop(col.id)}
                 style={{ background: onOver ? "rgba(192,57,43,0.06)" : "rgba(0,0,0,0.02)",
                          border: `1px dashed ${onOver ? "var(--accent)" : "var(--line)"}`,
                          padding: 10, minHeight: 220, display: "flex", flexDirection: "column" }}>
              <div className="row" style={{ alignItems: "baseline", marginBottom: 8 }}>
                <span className="mono" style={{ fontSize: 11, letterSpacing: ".08em", textTransform: "uppercase", color: "var(--mut)" }}>
                  {col.label}
                </span>
                <small style={{ color: "var(--mut)", marginLeft: 6 }}>
                  ({rows.length}{search && rows.length !== totalInStatus ? `/${totalInStatus}` : ""})
                </small>
              </div>
              {rows.length === 0 && (
                <div style={{ fontSize: 11, color: "var(--mut)", textAlign: "center", padding: "16px 8px", flex: 1, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {search ? "Aucune tâche ne correspond" : col.description}
                </div>
              )}
              {rows.map((t) => {
                const key = `${t.project_id}::${t.id}`;
                const color = projectColor(t.project_id);
                return (
                  <div key={key}
                       draggable
                       onDragStart={() => setDragKey(key)}
                       onDragEnd={() => { setDragKey(null); setOver(null); }}
                       className="card"
                       style={{ marginBottom: cardGap, padding: cardPad, cursor: "grab",
                                opacity: dragKey === key ? 0.5 : 1, background: "var(--surface-2)",
                                borderLeft: `3px solid ${color}` }}>
                    <div className="row" style={{ alignItems: "flex-start", gap: 6 }}>
                      <span className={`ds-ts ${PRIO_CHIP[t.priority] || "is-unknown"}`}
                            style={{ fontSize: 9 }}>
                        <span className="dot" />{t.priority?.toUpperCase()}
                      </span>
                      <span style={{ flex: 1, fontSize: titleSize, fontWeight: 500, lineHeight: 1.3 }}>
                        {t.title}
                      </span>
                      <button className="signout" style={{ padding: 0, fontSize: 14 }}
                              title="Supprimer"
                              onClick={(e) => { e.stopPropagation(); onDel(t.project_id, t.id); }}>×</button>
                    </div>
                    {density === "spacieux" && (
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
                    )}
                    {density === "compact" && t.project_name && (
                      <small style={{ color: "var(--mut)", fontSize: 10 }}>{t.project_name}{t.due_date ? ` · éch. ${t.due_date}` : ""}</small>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </>
  );
}
