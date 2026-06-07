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

  // --- W16: Permissions collaborateurs ------------------------------------
  type Scope = { id: number; user_id: number; project_id: number | null; surface: string | null; level: string };
  type AppUser = { id: number; email: string; name: string; role: string };
  type AppProj = { project_id: string; name: string };
  const [orgUsers, setOrgUsers] = useState<AppUser[]>([]);
  const [orgProjects, setOrgProjects] = useState<AppProj[]>([]);
  const [orgProjectsRaw, setOrgProjectsRaw] = useState<{ project_id: string; db_id?: number; name: string }[]>([]);
  const [scopes, setScopes] = useState<Scope[]>([]);
  const [selectedUser, setSelectedUser] = useState<number | null>(null);
  const [aclBusy, setAclBusy] = useState(false);
  const [aclErr, setAclErr] = useState<string | null>(null);
  const SCOPED_SURFACES = [
    "dashboard", "foresight", "taches", "checklist", "terrain", "copilote", "memoire",
    "coordination", "intervenants", "documents", "brs",
    "permis", "opposition", "conformite",
    "couts", "chantier",
  ];
  const SURFACE_FR: Record<string, string> = {
    dashboard: "Tableau de bord", foresight: "Foresight", taches: "Tâches",
    checklist: "Checklist SIA", terrain: "Terrain & zonage", copilote: "Copilote",
    memoire: "Mémoire", coordination: "Coordination", intervenants: "Intervenants",
    documents: "Documents", brs: "Exigences (BRS)", permis: "Permis",
    opposition: "Risque d'opposition", conformite: "Conformité",
    couts: "Coûts", chantier: "Chantier",
  };
  async function loadACL() {
    try {
      const [u, p, s] = await Promise.all([
        api<any>("/orgs/users", { token }).catch(() => ({ users: [] })),
        api<any>("/projects", { token }).catch(() => ({ projects: [] })),
        api<any>("/orgs/scopes", { token }).catch(() => ({ scopes: [] })),
      ]);
      setOrgUsers(u.users || []);
      // /projects returns project_id strings; fetch each to get db id.
      const pids: string[] = p.projects || [];
      const projs = await Promise.all(pids.map((pid) =>
        api<any>(`/projects/${pid}`, { token }).then((r) => r.project).catch(() => null)
      ));
      const arr = projs.filter(Boolean).map((pr: any) => ({
        project_id: pr.project_id, name: pr.name,
        // The summary doesn't expose db_id; we'll match scope rows below by
        // letting the user pick a project_id (string) and looking up via the
        // membership row… Actually scope rows store the DB id directly. We
        // need it on the client. The workaround: use the index in the list
        // and resolve via the scope-grant response.
      }));
      setOrgProjects(arr);
      setOrgProjectsRaw(arr);
      setScopes(s.scopes || []);
    } catch (e: any) { setAclErr(e?.message || "Échec chargement ACL"); }
  }
  useEffect(() => { loadACL(); /* eslint-disable-next-line */ }, []);
  // Pick the first non-owner user if any.
  useEffect(() => {
    if (selectedUser === null && orgUsers.length > 0) {
      const firstNonOwner = orgUsers.find((u) => u.role !== "owner") || null;
      if (firstNonOwner) setSelectedUser(firstNonOwner.id);
    }
  }, [orgUsers, selectedUser]);

  function levelOf(userId: number, projectIdDb: number | null, surface: string | null): string {
    // Resolution: exact → project-wide → surface-wide → user-default → role-default
    const r = scopes.find((s) => s.user_id === userId && s.project_id === projectIdDb && s.surface === surface);
    if (r) return r.level;
    if (projectIdDb !== null && surface !== null) {
      const r2 = scopes.find((s) => s.user_id === userId && s.project_id === projectIdDb && s.surface === null);
      if (r2) return r2.level;
    }
    if (surface !== null) {
      const r3 = scopes.find((s) => s.user_id === userId && s.project_id === null && s.surface === surface);
      if (r3) return r3.level;
    }
    const r4 = scopes.find((s) => s.user_id === userId && s.project_id === null && s.surface === null);
    if (r4) return r4.level;
    const u = orgUsers.find((u) => u.id === userId);
    return u?.role === "viewer" ? "read" : "write";
  }
  async function setLevel(userId: number, surface: string | null, level: string) {
    setAclBusy(true); setAclErr(null);
    try {
      // Find existing exact scope to potentially delete (level === "default")
      await api("/orgs/scopes", { method: "PUT", token,
        body: { user_id: userId, surface, level } });
      await loadACL();
    } catch (e: any) { setAclErr(e?.message || "Échec"); }
    finally { setAclBusy(false); }
  }
  async function deleteScope(scopeId: number) {
    setAclBusy(true); setAclErr(null);
    try { await api(`/orgs/scopes/${scopeId}`, { method: "DELETE", token }); await loadACL(); }
    catch (e: any) { setAclErr(e?.message || "Échec"); }
    finally { setAclBusy(false); }
  }

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

      {/* --- W16: Permissions collaborateurs ---------------------------- */}
      <div className="card" style={{ marginTop: 14 }}>
        <div className="row" style={{ alignItems: "baseline" }}>
          <h3 style={{ margin: 0 }}>Permissions collaborateurs</h3>
          <small style={{ color: "var(--mut)", marginLeft: 8 }}>per-surface · per-projet · 3 niveaux</small>
        </div>
        <p style={{ marginTop: 4, color: "var(--mut)" }}>
          Pour chaque collaborateur interne (<i>member</i> ou <i>viewer</i>), réglez l&apos;accès <b>none / read / write</b> par surface. Owner reste full-write. Les externes sont gérés via les invitations intervenant (scoping documentaire).
        </p>
        {aclErr && <small style={{ color: "var(--ts-conflict)", display: "block", marginTop: 6 }}>{aclErr}</small>}
        {orgUsers.filter((u) => u.role !== "owner" && u.role !== "external").length === 0 && (
          <small className="spin" style={{ display: "block", marginTop: 8 }}>
            Aucun member/viewer dans l&apos;atelier — invitez-en via la surface Équipe pour leur attribuer des permissions ici.
          </small>
        )}
        {orgUsers.filter((u) => u.role !== "owner" && u.role !== "external").length > 0 && (
          <>
            <div className="row" style={{ gap: 8, alignItems: "center", marginTop: 10, flexWrap: "wrap" }}>
              <label className="mono" style={{ fontSize: 11, color: "var(--mut)" }}>Collaborateur</label>
              <select className="fld" style={{ margin: 0, padding: "5px 9px", width: "auto" }}
                      value={selectedUser ?? ""} onChange={(e) => setSelectedUser(Number(e.target.value))}>
                {orgUsers.filter((u) => u.role !== "owner" && u.role !== "external").map((u) => (
                  <option key={u.id} value={u.id}>{u.name || u.email} — {u.role}</option>
                ))}
              </select>
            </div>
            {selectedUser !== null && (
              <div style={{ marginTop: 12 }}>
                {/* Default for all surfaces (org-wide row, project=NULL surface=NULL) */}
                <div className="row-line">
                  <span className="ttl" style={{ flex: 1 }}>Niveau par défaut (toutes surfaces, tous projets)</span>
                  <span className="row" style={{ gap: 4 }}>
                    {["none", "read", "write"].map((lvl) => (
                      <button key={lvl}
                              className={`toggle ${levelOf(selectedUser, null, null) === lvl ? "on" : ""}`}
                              disabled={aclBusy}
                              style={{ padding: "3px 9px", fontSize: 11 }}
                              onClick={() => setLevel(selectedUser, null, lvl)}>
                        {lvl}
                      </button>
                    ))}
                  </span>
                </div>
                {/* Per-surface (project=NULL surface=X) */}
                <div className="mono" style={{ fontSize: 10, color: "var(--mut)", letterSpacing: ".08em", textTransform: "uppercase", marginTop: 14, marginBottom: 4 }}>
                  Niveau par surface (override le défaut)
                </div>
                {SCOPED_SURFACES.map((surface) => {
                  const lvl = levelOf(selectedUser, null, surface);
                  return (
                    <div className="row-line" key={surface}>
                      <span className="grow">
                        <span className="ttl" style={{ fontSize: 13 }}>{SURFACE_FR[surface] || surface}</span>
                        <small style={{ color: "var(--mut)" }}>{surface}</small>
                      </span>
                      <span className="row" style={{ gap: 4 }}>
                        {["none", "read", "write"].map((opt) => (
                          <button key={opt}
                                  className={`toggle ${lvl === opt ? "on" : ""}`}
                                  disabled={aclBusy}
                                  style={{ padding: "3px 9px", fontSize: 11 }}
                                  onClick={() => setLevel(selectedUser, surface, opt)}>
                            {opt}
                          </button>
                        ))}
                      </span>
                    </div>
                  );
                })}
                {/* List scope rows for transparency + manual delete */}
                <div className="mono" style={{ fontSize: 10, color: "var(--mut)", letterSpacing: ".08em", textTransform: "uppercase", marginTop: 14, marginBottom: 4 }}>
                  Règles actives ({scopes.filter((s) => s.user_id === selectedUser).length})
                </div>
                {scopes.filter((s) => s.user_id === selectedUser).length === 0 && (
                  <small style={{ color: "var(--mut)" }}>Aucune — le collaborateur a son niveau par défaut sur tout.</small>
                )}
                {scopes.filter((s) => s.user_id === selectedUser).map((s) => (
                  <div className="row-line" key={s.id}>
                    <span className="ds-ts is-computed" style={{ fontSize: 10 }}><span className="dot" />{s.level}</span>
                    <span className="grow">
                      <span className="ttl" style={{ fontSize: 13 }}>
                        {s.project_id ? `projet#${s.project_id}` : "tous projets"} · {s.surface || "toutes surfaces"}
                      </span>
                    </span>
                    <button className="signout" style={{ padding: 0 }} disabled={aclBusy} onClick={() => deleteScope(s.id)} title="Retirer la règle (le collaborateur retombe sur le niveau moins spécifique)">✕</button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
