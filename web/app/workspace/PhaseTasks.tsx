"use client";

// W11.C: embed in every phase-bound surface (Permis = phase 33, Conformité = 33,
// Chantier = 52, Coûts = current phase…) — shows THIS project's tasks for the
// relevant phase, with a one-click deep-link to the Atelier planning filtered by
// this project. Keeps the per-surface lens narrow while connecting it to the
// multi-project view at all times.

type Task = {
  id: number; title: string; status: string; priority: string;
  estimate_hours?: number | null; due_date?: string | null;
  assignee?: string | null; is_blocked?: boolean; phase_code?: string | null;
};

const PRIO_CHIP: Record<string, string> = { p0: "is-conflict", p1: "is-assume", p2: "is-sourced" };
const STATUS_LABEL: Record<string, string> = { todo: "à faire", doing: "en cours", done: "fait", blocked: "bloquée" };

export function PhaseTasks({
  phase, tasks, projectId, onOpenAtelierPlanning, label,
}: {
  phase: string | string[]; // a single phase code or a set ("52" or ["52","53"])
  tasks: Task[];
  projectId: string;
  onOpenAtelierPlanning?: (pid: string) => void;
  label?: string;
}) {
  const phases = Array.isArray(phase) ? phase : [phase];
  const phaseLabel = label || (phases.length === 1 ? `phase ${phases[0]}` : `phases ${phases.join("/")}`);
  const all = (tasks || []).filter((t) => t.phase_code && phases.includes(t.phase_code));
  const open = all.filter((t) => t.status !== "done");
  const totalH = all.reduce((s, t) => s + (t.estimate_hours || 0), 0);
  return (
    <div className="card" style={{ marginTop: 14 }}>
      <div className="row" style={{ alignItems: "baseline", gap: 8 }}>
        <h3 style={{ margin: 0 }}>Tâches · {phaseLabel}</h3>
        <small style={{ color: "var(--mut)" }}>{all.length} tâche{all.length > 1 ? "s" : ""}{totalH ? ` · ${totalH} h estimées` : ""}</small>
        <span className="grow" />
        {onOpenAtelierPlanning && all.length > 0 && (
          <button className="toggle" onClick={() => onOpenAtelierPlanning(projectId)}>
            Voir dans le planning Atelier →
          </button>
        )}
      </div>
      {all.length === 0 && (
        <p className="spin" style={{ marginTop: 8 }}>
          Aucune tâche n&apos;est rattachée à {phaseLabel} pour ce projet. Créez-en dans <i>Tâches &amp; priorités</i> en choisissant la phase correspondante.
        </p>
      )}
      {open.length > 0 && (
        <div style={{ marginTop: 8 }}>
          {open.slice(0, 8).map((t) => { const [pc] = PRIO_CHIP[t.priority] ? [PRIO_CHIP[t.priority]] : ["is-unknown"]; return (
            <div className="row-line" key={t.id}>
              <span className={`ds-ts ${pc}`} style={{ fontSize: 9 }}><span className="dot" />{t.priority?.toUpperCase()}</span>
              <span className="grow"><span className="ttl">{t.title}{t.is_blocked && <small style={{ display: "inline", color: "var(--ts-conflict)" }}> · bloquée</small>}</span><small>{[STATUS_LABEL[t.status] || t.status, t.assignee ? "→ " + t.assignee : null, t.estimate_hours ? t.estimate_hours + " h" : null, t.due_date ? "éch. " + t.due_date : null].filter(Boolean).join(" · ")}</small></span>
            </div>
          ); })}
          {open.length > 8 && <small style={{ color: "var(--mut)" }}>+{open.length - 8} de plus — visibles dans Tâches &amp; priorités.</small>}
        </div>
      )}
    </div>
  );
}
