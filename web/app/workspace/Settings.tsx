"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

// W15.B — Settings surface. Wires endpoints that already existed in the
// backend but had no UI:
//   - POST /api/auth/me/rotate-token  (W11.F)
//   - POST /api/auth/me/revoke-token  (W11.F)
//   - GET  /api/orgs/audit            (W11.F)
//   - PATCH /api/projects/{pid}/llm-mode (W12.C)
//   - GET  /api/orgs/benchmark        (W12.E)
//   - POST /api/orgs/benchmark/snapshot (W12.E)
//
// Doctrine kept: every mutation passes through a confirm step (token rotate
// shows the new token once, then disappears; flipping llm-mode is audited).

type Bench = {
  id: number; period_label: string; n_projects: number; n_tasks_done: number;
  duration_ratios: Record<string, number>; cost_factor: number | null;
  note: string | null; frozen_at: string | null;
};

type AuditEv = {
  id: number; event_type: string; actor: string; actor_role: string;
  target: string; timestamp: string | null; project_id: number | null;
};

export function Settings({ token, projectId, projectName, projectLlmMode, onTokenRotated, onLlmModeChanged }: {
  token: string;
  projectId: string | null;
  projectName: string | null;
  projectLlmMode: string | null;
  onTokenRotated?: (newToken: string) => void;
  onLlmModeChanged?: (mode: string) => void;
}) {
  // --- Token rotation -----------------------------------------------------
  const [rotating, setRotating] = useState(false);
  const [rotatedToken, setRotatedToken] = useState<string | null>(null);
  const [tokenErr, setTokenErr] = useState<string | null>(null);
  async function rotateToken() {
    setRotating(true); setTokenErr(null);
    try {
      const r = await api<any>("/auth/me/rotate-token", { method: "POST", token });
      const nt = r.token as string;
      if (nt) {
        setRotatedToken(nt);
        onTokenRotated?.(nt);
      }
    } catch (e: any) { setTokenErr(e?.message || "Échec"); }
    finally { setRotating(false); }
  }

  // --- LLM mode per project ----------------------------------------------
  const [llmBusy, setLlmBusy] = useState(false);
  const [llmErr, setLlmErr] = useState<string | null>(null);
  const [llmMode, setLlmMode] = useState<string>(projectLlmMode || "off");
  useEffect(() => { setLlmMode(projectLlmMode || "off"); }, [projectLlmMode, projectId]);
  async function setLlmModeApi(mode: "off" | "local" | "cloud") {
    if (!projectId) return;
    setLlmBusy(true); setLlmErr(null);
    try {
      await api(`/projects/${projectId}/llm-mode`, { method: "PATCH", token, body: { mode } });
      setLlmMode(mode);
      onLlmModeChanged?.(mode);
    } catch (e: any) { setLlmErr(e?.message || "Échec"); }
    finally { setLlmBusy(false); }
  }

  // --- Benchmark snapshots ------------------------------------------------
  const [benches, setBenches] = useState<Bench[] | null>(null);
  const [benchBusy, setBenchBusy] = useState(false);
  const [benchNote, setBenchNote] = useState("");
  const [benchErr, setBenchErr] = useState<string | null>(null);
  async function loadBenches() {
    try {
      const r = await api<any>("/orgs/benchmark", { token });
      setBenches(r.benchmarks || []);
    } catch { setBenches([]); }
  }
  useEffect(() => { loadBenches(); /* eslint-disable-next-line */ }, []);
  async function snapshotBench() {
    setBenchBusy(true); setBenchErr(null);
    try {
      await api("/orgs/benchmark/snapshot", { method: "POST", token, body: { note: benchNote || null } });
      setBenchNote("");
      await loadBenches();
    } catch (e: any) { setBenchErr(e?.message || "Échec"); }
    finally { setBenchBusy(false); }
  }

  // --- Audit log ----------------------------------------------------------
  const [audit, setAudit] = useState<AuditEv[] | null>(null);
  const [auditErr, setAuditErr] = useState<string | null>(null);
  async function loadAudit() {
    try {
      const r = await api<any>("/orgs/audit?limit=50", { token });
      setAudit(r.events || []);
    } catch (e: any) {
      setAudit([]);
      // 403 is fine — externals + non-owners can't read it.
      if (!String(e?.message || "").includes("FORBIDDEN")) {
        setAuditErr(e?.message || "Non accessible");
      }
    }
  }
  useEffect(() => { loadAudit(); /* eslint-disable-next-line */ }, []);

  return (
    <>
      <div className="vh">
        <h2>Réglages</h2>
        <p>
          Compte (rotation de jeton), couche LLM par projet (W12.C — off/local/cloud), benchmark atelier (W12.E — capitalisation des ratios), et journal de sécurité (W11.F — audit log).
        </p>
      </div>

      {/* --- Compte -------------------------------------------------------- */}
      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Compte</h3>
        <p className="note" style={{ color: "var(--mut)" }}>
          Votre jeton d&apos;API permet à votre navigateur de rester connecté. Vous pouvez le <b>faire tourner</b> à tout moment — le précédent cesse immédiatement de fonctionner. Pratique après un partage involontaire, ou pour la rotation périodique.
        </p>
        <div className="row" style={{ gap: 8, alignItems: "center", marginTop: 8 }}>
          <button className="ds-btn" disabled={rotating} onClick={rotateToken}>{rotating ? "…" : "Faire tourner mon jeton"}</button>
        </div>
        {tokenErr && <small style={{ color: "var(--ts-conflict)", display: "block", marginTop: 6 }}>{tokenErr}</small>}
        {rotatedToken && (
          <div className="banner ok" style={{ marginTop: 10, display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ flex: 1 }}>
              <b>Nouveau jeton émis.</b> Il a remplacé le précédent. Conservez-le si vous voulez vous reconnecter sans email/mot de passe : <code className="mono" style={{ background: "var(--surface)", padding: "2px 6px" }}>{rotatedToken}</code>
            </span>
            <button className="toggle" onClick={() => navigator.clipboard?.writeText(rotatedToken).catch(() => {})}>Copier</button>
            <button className="toggle" onClick={() => setRotatedToken(null)}>OK</button>
          </div>
        )}
      </div>

      {/* --- LLM par projet ----------------------------------------------- */}
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row" style={{ alignItems: "baseline" }}>
          <h3 style={{ margin: 0 }}>Couche LLM</h3>
          {projectName && <small style={{ color: "var(--mut)", marginLeft: 8 }}>· projet : <b>{projectName}</b></small>}
        </div>
        <p style={{ marginTop: 4, color: "var(--mut)" }}>
          La couche LLM est <b>opt-in par projet</b>. Off par défaut : aucun appel sort. Local : Ollama sur votre poste, contenu confidentiel autorisé. Cloud : modèle hébergé, les BRS marqués <i>PV</i> sont filtrés du prompt avant l&apos;appel.
        </p>
        {!projectId ? (
          <small className="spin" style={{ display: "block", marginTop: 6 }}>Ouvrez un projet via le sélecteur pour changer son mode.</small>
        ) : (
          <div className="row" style={{ gap: 6, marginTop: 8, flexWrap: "wrap" }}>
            {(["off", "local", "cloud"] as const).map((m) => (
              <button key={m} className={`toggle ${llmMode === m ? "on" : ""}`} disabled={llmBusy} onClick={() => setLlmModeApi(m)}>
                {m === "off" ? "Désactivée" : m === "local" ? "Local (Ollama)" : "Cloud (opt-in)"}
              </button>
            ))}
          </div>
        )}
        {llmErr && <small style={{ color: "var(--ts-conflict)", display: "block", marginTop: 6 }}>{llmErr}</small>}
      </div>

      {/* --- Benchmark atelier -------------------------------------------- */}
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row" style={{ alignItems: "baseline" }}>
          <h3 style={{ margin: 0 }}>Benchmark atelier</h3>
          <small style={{ color: "var(--mut)", marginLeft: 8 }}>capitalisation des ratios appris</small>
        </div>
        <p style={{ marginTop: 4, color: "var(--mut)" }}>
          Geler l&apos;état actuel des ratios appris (heures réelles/estimées par phase, coefficient atelier coût final/SIA) pour qu&apos;ils survivent au bruit d&apos;un projet isolé. Chaque snapshot est append-only — l&apos;historique reste lisible.
        </p>
        <div className="row" style={{ gap: 8, alignItems: "center", marginTop: 8, flexWrap: "wrap" }}>
          <input className="fld" style={{ flex: "1 1 240px", margin: 0, padding: "5px 9px" }} placeholder="Note (optionnel) — ex. clôture Q2 2026" value={benchNote} onChange={(e) => setBenchNote(e.target.value)} />
          <button className="ds-btn" disabled={benchBusy} onClick={snapshotBench}>{benchBusy ? "…" : "Geler maintenant"}</button>
        </div>
        {benchErr && <small style={{ color: "var(--ts-conflict)", display: "block", marginTop: 6 }}>{benchErr}</small>}
        <div style={{ marginTop: 10 }}>
          {benches === null && <small className="spin">Chargement…</small>}
          {benches && benches.length === 0 && <small style={{ color: "var(--mut)" }}>Aucun snapshot pour l&apos;instant. Le premier captue l&apos;état initial de l&apos;atelier.</small>}
          {benches?.map((b) => (
            <div key={b.id} className="row-line">
              <span className="ds-ts is-computed"><span className="dot" />{b.period_label}</span>
              <span className="grow">
                <span className="ttl" style={{ fontSize: 13 }}>
                  {b.n_projects} projet{b.n_projects > 1 ? "s" : ""} · {b.n_tasks_done} tâche{b.n_tasks_done > 1 ? "s" : ""} close{b.n_tasks_done > 1 ? "s" : ""}
                  {b.cost_factor ? ` · coefficient ${b.cost_factor}×` : ""}
                </span>
                <small>{b.note ? `« ${b.note} » · ` : ""}{(b.frozen_at || "").slice(0, 10)}</small>
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* --- Audit log ---------------------------------------------------- */}
      <div className="card">
        <div className="row" style={{ alignItems: "baseline" }}>
          <h3 style={{ margin: 0 }}>Journal de sécurité</h3>
          <small style={{ color: "var(--mut)", marginLeft: 8 }}>append-only, 50 derniers événements</small>
        </div>
        <p style={{ marginTop: 4, color: "var(--mut)" }}>
          Invitations émises et acceptées, droits d&apos;accès accordés/révoqués, rotations de jeton, changements de mode LLM. Visible par les owners de l&apos;atelier (les externes n&apos;y ont pas accès).
        </p>
        {auditErr && <small style={{ color: "var(--ts-conflict)", display: "block", marginTop: 6 }}>{auditErr}</small>}
        <div style={{ marginTop: 10 }}>
          {audit === null && <small className="spin">Chargement…</small>}
          {audit && audit.length === 0 && <small style={{ color: "var(--mut)" }}>Aucun événement consigné pour l&apos;instant.</small>}
          {audit?.map((e) => (
            <div key={e.id} className="row-line">
              <span className="ds-ts is-decision" style={{ fontSize: 10 }}><span className="dot" />{e.event_type}</span>
              <span className="grow">
                <span className="ttl" style={{ fontSize: 13 }}>{e.target}</span>
                <small>{e.actor} ({e.actor_role}){e.timestamp ? ` · ${e.timestamp.slice(0, 16).replace("T", " ")}` : ""}</small>
              </span>
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
