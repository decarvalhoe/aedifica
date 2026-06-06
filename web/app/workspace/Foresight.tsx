"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

// W12.B — Foresight surface. Shows the deterministic IA proposals computed
// server-side (`GET /api/projects/{pid}/foresight`) and lets the architect
// accept / defer / refuse each one. Doctrine: every proposal carries its
// basis (named sources), a confidence number derived from the comparable
// count (not vibed), and an apply_payload describing what would change if
// accepted. The architect always decides.

type Proposal = {
  id: number;
  kind: string;
  title: string;
  detail: string;
  basis: { source_kind: string; source_id: number | string; ref: string }[];
  confidence: number;
  decision: string;
  apply_payload: any;
  proposed_at?: string | null;
  decided_at?: string | null;
  decided_by?: string | null;
  decision_basis?: string | null;
};

type Comparable = { project_id: number; label: string; score: number; reasons: string[] };

type Thresholds = {
  duration_adjust?: { rule?: string; need_per_phase: number; explanation?: string;
                     samples_by_phase: Record<string, { have: number; need: number; ready: boolean }> };
  cost_factor?: { rule?: string; have: number; need: number; ready: boolean; explanation?: string };
  risk_alert?: { rule?: string; explanation?: string };
};

type FS = {
  proposals: Proposal[];
  summary: { predictions: number; risks: number; suggestions: number; confidence_avg: number };
  comparables: Comparable[];
  thresholds?: Thresholds;
  freshness: string | null;
};

const KIND_LABEL: Record<string, string> = {
  duration_adjust: "Estimation durée",
  cost_factor: "Coefficient atelier",
  risk_alert: "Alerte risque",
  reuse_brs: "Réutilisation BRS",
  reuse_checklist: "Réutilisation checklist",
  rebalance: "Rééquilibrage charge",
  next_step_ranked: "Prochain pas ranké",
};

const KIND_TS: Record<string, string> = {
  duration_adjust: "is-computed",
  cost_factor: "is-computed",
  risk_alert: "is-conflict",
  reuse_brs: "is-sourced",
  reuse_checklist: "is-sourced",
  rebalance: "is-assume",
  next_step_ranked: "is-decision",
};

function confidencePill(c: number): string {
  if (c >= 0.7) return "is-sourced";
  if (c >= 0.4) return "is-computed";
  return "is-assume";
}

// W14.A — when no prediction fires, show CONCRETELY what's missing.
// "Pas assez de comparables" → "Il vous faut 5 tâches comparables, vous en avez 2".
function ThresholdHint({ thresholds: t }: { thresholds: Thresholds }) {
  const dur = t.duration_adjust;
  const cost = t.cost_factor;
  const phases = dur ? Object.entries(dur.samples_by_phase || {}) : [];
  const phasesReady = phases.filter(([_, s]) => s.ready).length;
  return (
    <div style={{ background: "var(--surface-2)", padding: 12, borderLeft: "3px solid var(--ts-assume)" }}>
      <div className="mono" style={{ fontSize: 10, color: "var(--mut)", marginBottom: 8 }}>SEUILS DE DÉCLENCHEMENT</div>
      <p style={{ margin: 0 }}>
        <b>Aedifica reste silencieuse</b> plutôt que d&apos;inventer un chiffre. Voici ce qu&apos;il manque pour qu&apos;une prédiction puisse émerger :
      </p>
      {dur && (
        <div style={{ marginTop: 10 }}>
          <div className="ttl" style={{ fontSize: 13 }}>Prédiction durée par phase</div>
          <small style={{ color: "var(--mut)" }}>{dur.explanation}</small>
          {phases.length === 0 ? (
            <p className="note" style={{ marginTop: 6 }}>Aucune tâche close avec heures réelles renseignées sur tout l&apos;atelier — la prédiction durée se déverrouille dès la <b>{dur.need_per_phase}<sup>e</sup> tâche close</b> d&apos;une même phase.</p>
          ) : (
            <ul style={{ margin: "6px 0 0 18px", padding: 0 }}>
              {phases.map(([ph, s]) => (
                <li key={ph} style={{ marginBottom: 2 }}>
                  Phase <b>{ph}</b> : <span className={s.ready ? "" : "mono"}>{s.have}/{s.need}</span>
                  {s.ready ? <small style={{ color: "var(--ts-sourced)", marginLeft: 6 }}>✓ seuil atteint</small> : null}
                </li>
              ))}
            </ul>
          )}
          {phasesReady > 0 && phases.some(([_, s]) => !s.ready) && (
            <small style={{ color: "var(--mut)", marginTop: 4, display: "block" }}>
              {phasesReady} phase{phasesReady > 1 ? "s ont" : " a"} atteint le seuil mais aucune tâche ouverte n&apos;y est rattachée à re-estimer.
            </small>
          )}
        </div>
      )}
      {cost && (
        <div style={{ marginTop: 12 }}>
          <div className="ttl" style={{ fontSize: 13 }}>Coefficient atelier de coût</div>
          <small style={{ color: "var(--mut)" }}>{cost.explanation}</small>
          <p className="note" style={{ marginTop: 6 }}>
            Projets clos avec coût final + estimation SIA renseignés : <b>{cost.have}/{cost.need}</b>
            {cost.ready ? <small style={{ color: "var(--ts-sourced)", marginLeft: 6 }}>✓ seuil atteint</small> : null}
          </p>
        </div>
      )}
    </div>
  );
}

// W15.A — calmer proposal card: lighter spacing, confidence as a discreet
// inline caption rather than a chip, header on one row, decision buttons
// only when relevant. The card felt heavy when there were 5+ predictions
// stacked; this version stays readable past 20.
function ProposalCard({ p, onDecide }: { p: Proposal; onDecide: (id: number, decision: string, basis?: string) => Promise<void> }) {
  const [basis, setBasis] = useState("");
  const [busy, setBusy] = useState(false);
  const [showBasis, setShowBasis] = useState(false);
  const decide = async (decision: string) => {
    setBusy(true);
    try { await onDecide(p.id, decision, basis || undefined); } finally { setBusy(false); }
  };
  const conf = Math.round(p.confidence * 100);
  return (
    <div style={{
      borderTop: "1px solid var(--line)", paddingTop: 12, marginTop: 12,
      opacity: p.decision !== "pending" ? 0.7 : 1,
    }}>
      <div className="row" style={{ alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
        <span className={`ds-ts ${KIND_TS[p.kind] || "is-computed"}`} style={{ fontSize: 10 }}>
          <span className="dot" />{KIND_LABEL[p.kind] || p.kind}
        </span>
        <span className="ttl" style={{ flex: "1 1 220px", fontSize: 13 }}>{p.title}</span>
        {p.confidence > 0 && (
          <small style={{ color: "var(--mut)" }} title="Confiance dérivée du nombre de comparables, pas une intuition">
            confiance <b style={{ color: `var(--ts-${conf >= 70 ? "sourced" : conf >= 40 ? "computed" : "assume"})` }}>{conf}%</b>
          </small>
        )}
      </div>
      <small style={{ color: "var(--ink-90)", lineHeight: 1.5, display: "block", marginTop: 4 }}>{p.detail}</small>
      <div className="row" style={{ alignItems: "center", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
        <button className="signout" style={{ padding: 0, fontSize: 11 }} onClick={() => setShowBasis(v => !v)}>
          {showBasis ? "Masquer" : "Pourquoi ?"} <small>({p.basis.length} source{p.basis.length > 1 ? "s" : ""})</small>
        </button>
        {p.decision === "pending" ? (
          <span className="row" style={{ gap: 6, marginLeft: "auto", flexWrap: "wrap" }}>
            <input className="fld" style={{ width: 180, margin: 0, padding: "4px 8px", fontSize: 12 }}
                   placeholder="Basis (optionnel)" value={basis} onChange={(e) => setBasis(e.target.value)} />
            <button className="ds-btn" style={{ padding: "4px 10px" }} disabled={busy} onClick={() => decide("accepted")}>{busy ? "…" : "Accepter"}</button>
            <button className="toggle" style={{ padding: "4px 8px" }} disabled={busy} onClick={() => decide("deferred")}>Différer</button>
            <button className="signout" style={{ padding: 0 }} disabled={busy} onClick={() => decide("refused")}>Refuser</button>
          </span>
        ) : (
          <small style={{ color: "var(--mut)", marginLeft: "auto" }}>
            {p.decision === "accepted" ? "Acceptée" : p.decision === "deferred" ? "Différée" : "Refusée"}
            {p.decided_by ? ` par ${p.decided_by}` : ""}{p.decided_at ? ` le ${p.decided_at.slice(0, 10)}` : ""}
          </small>
        )}
      </div>
      {showBasis && (
        <div style={{ background: "var(--surface-2)", padding: 8, marginTop: 6, fontSize: 11 }}>
          <div className="mono" style={{ fontSize: 9, color: "var(--mut)", marginBottom: 4, letterSpacing: ".08em" }}>SOURCES NOMMÉES</div>
          {p.basis.map((b, i) => (
            <div key={i} style={{ paddingTop: 2 }}>
              <span className="mono" style={{ fontSize: 10, color: "var(--mut)" }}>{b.source_kind}#{b.source_id}</span>{" "}{b.ref}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function Foresight({ token, pid }: { token: string; pid: string }) {
  const [data, setData] = useState<FS | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = async (refresh: boolean) => {
    try {
      setRefreshing(refresh);
      const d = await api<FS>(`/projects/${pid}/foresight${refresh ? "?refresh=true" : ""}`, { token });
      setData(d); setErr(null);
    } catch (e: any) { setErr(e?.message || "Chargement impossible"); }
    finally { setRefreshing(false); }
  };
  useEffect(() => { load(false); /* eslint-disable-next-line */ }, [pid]);

  const decide = async (id: number, decision: string, basis?: string) => {
    await api(`/projects/${pid}/foresight/${id}/decide`,
              { method: "POST", token, body: { decision, basis: basis || null } });
    await load(false);
  };

  const predictions = (data?.proposals || []).filter(p => p.kind === "duration_adjust" || p.kind === "cost_factor");
  const risks = (data?.proposals || []).filter(p => p.kind === "risk_alert");
  const suggestions = (data?.proposals || []).filter(p => p.kind === "reuse_brs" || p.kind === "reuse_checklist" || p.kind === "rebalance");

  return (
    <>
      <div className="vh">
        <div className="row" style={{ gap: 10, alignItems: "center" }}>
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" style={{ color: "var(--ink-60)" }}>
            <use href="/assets/functional-icons.svg#ic-datum-target" />
          </svg>
          <h2 style={{ margin: 0 }}>Foresight · prédictions et suggestions</h2>
          <span className="grow" />
          <button className="toggle" disabled={refreshing} onClick={() => load(true)}>{refreshing ? "Recalcul…" : "Recalculer"}</button>
        </div>
        <p>L&apos;IA <b>propose</b>, vous <b>décidez</b>. Chaque proposition liste ses sources et une confiance dérivée (jamais une intuition). Rien ne mute sans votre accord.</p>
      </div>

      {err && <div className="banner bad">{err}</div>}

      {data && (
        <div className="kpis" style={{ marginBottom: 14 }}>
          <div className="kpi"><div className="lab">Prédictions</div><div className="num">{data.summary.predictions}</div><div className="sub">durée · coût</div></div>
          <div className="kpi"><div className="lab">Risques</div><div className="num">{data.summary.risks}</div><div className="sub">anomalies cross-surface</div></div>
          <div className="kpi"><div className="lab">Suggestions</div><div className="num">{data.summary.suggestions}</div><div className="sub">réutilisation · charge</div></div>
          <div className="kpi"><div className="lab">Confiance moy.</div><div className="num">{Math.round((data.summary.confidence_avg || 0) * 100)}%</div><div className="sub">dérivée des comparables</div></div>
        </div>
      )}

      {data?.comparables && data.comparables.length > 0 && (
        <div className="card" style={{ marginBottom: 14 }}>
          <h3>Projets comparables ({data.comparables.length})</h3>
          {data.comparables.map((c, i) => (
            <div className="row-line" key={i}>
              <span className="ds-ts is-computed"><span className="dot" />score {c.score}</span>
              <span className="grow"><span className="ttl">{c.label}</span><small>{c.reasons.join(" · ")}</small></span>
            </div>
          ))}
        </div>
      )}

      <div className="g2">
        <div className="card">
          <h3>Prédictions ({predictions.length})</h3>
          {predictions.length === 0 && data?.thresholds && (
            <ThresholdHint thresholds={data.thresholds} />
          )}
          {predictions.map(p => <ProposalCard key={p.id} p={p} onDecide={decide} />)}
        </div>
        <div className="card">
          <h3>Risques ({risks.length})</h3>
          {risks.length === 0 && <p className="spin">Aucune anomalie cross-surface détectée.</p>}
          {risks.map(p => <ProposalCard key={p.id} p={p} onDecide={decide} />)}
        </div>
      </div>

      {suggestions.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <h3>Suggestions ({suggestions.length})</h3>
          {suggestions.map(p => <ProposalCard key={p.id} p={p} onDecide={decide} />)}
        </div>
      )}

      {data?.freshness && <small style={{ color: "var(--mut)", display: "block", marginTop: 10 }}>
        Recalculé le {data.freshness.slice(0, 16).replace("T", " ")}.
      </small>}
    </>
  );
}
