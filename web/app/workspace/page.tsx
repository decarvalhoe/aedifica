"use client";

import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";

const DEMO_ID = "DEMO-LAUSANNE-PALUD";
const META = { name: "Place de la Palud", commune: "Lausanne", phase: "Faisabilité · SIA 0–31" };

type View = "dashboard" | "terrain" | "permis" | "opposition" | "conformite" | "copilote" | "memoire";

const NAV: { id: View; lb: string; ds: string; ico: string }[] = [
  { id: "dashboard", lb: "Tableau de bord", ds: "Vue d'ensemble du projet", ico: "grid" },
  { id: "terrain", lb: "Terrain & zonage", ds: "Ce que la parcelle autorise", ico: "pin" },
  { id: "permis", lb: "Dossier de permis", ds: "Complétude pièce par pièce", ico: "doc" },
  { id: "opposition", lb: "Risque d'opposition", ds: "Motifs probables, sur les faits", ico: "shield" },
  { id: "conformite", lb: "Conformité", ds: "Obligations à lever avant dépôt", ico: "check" },
  { id: "copilote", lb: "Copilote IA · maquette", ds: "L'IA agit sur Archicad, sous contrôle", ico: "spark" },
  { id: "memoire", lb: "Mémoire du projet", ds: "Tout ce qui est su, décidé, modifié", ico: "clock" },
];

const TRUST: Record<string, [string, string]> = {
  sourced: ["is-sourced", "Source officielle"], computed: ["is-computed", "Calculé"],
  assumption: ["is-assume", "Hypothèse"], unknown: ["is-unknown", "À vérifier"],
  conflict: ["is-conflict", "Conflit"], present: ["is-sourced", "Fourni"],
  missing: ["is-assume", "Manquant"], satisfied: ["is-sourced", "Satisfait"],
  action_required: ["is-assume", "Action requise"], decision: ["is-computed", "Décision"],
};
function Trust({ state, label }: { state: string; label?: string }) {
  const [c, l] = TRUST[state] || ["is-unknown", state];
  return <span className={`ds-ts ${c}`}><span className="dot" />{label || l}</span>;
}
const EVENT: Record<string, string> = {
  adapter_dry_run: "Aperçu de modification", approval: "Validation accordée",
  adapter_execution: "Modification appliquée", decision: "Décision", brief: "Brief généré",
};
function human(e: any): string {
  if (e.event_type === "adapter_dry_run") return "Aperçu d'une modification préparé — aucune mutation de la maquette.";
  if (e.event_type === "approval") return "Exécution validée par l'architecte.";
  if (e.event_type === "adapter_execution") return "Modification appliquée à la maquette Archicad — réversible.";
  return e.summary;
}

// UI localisation of engine-sourced labels (engine fixtures stay language-neutral).
const FR: Record<string, string> = {
  architect: "Architecte", architect_or_surveyor: "Architecte / géomètre", specialist: "Spécialiste",
  architect_or_specialist: "Architecte / spécialiste", aedifica: "Aedifica",
  platform: "Plateforme", plans: "Plans", parcel: "Parcelle", project: "Projet", compliance: "Conformité",
  special_authorizations: "Autorisations spéciales",
  energy: "Énergie", fire: "Incendie", accessibility: "Accessibilité", structure: "Structure", bim: "BIM",
  heritage: "patrimoine", alignment: "alignements", neighbor: "voisinage", shadow: "ombres", visibility: "vues",
  "Questionnaire general ACTIS-CAMAC": "Questionnaire général ACTIS-CAMAC",
  "Plan de situation / geometre when required": "Plan de situation / géomètre (si requis)",
  "Signed permit plans": "Plans d'enquête signés",
  "Parcel identity and RDPPF/OEREB evidence": "Identité de la parcelle et extrait RDPPF/OEREB",
  "Project description and works type": "Description du projet et nature des travaux",
  "Energy forms and SIA 380/1 justification when applicable": "Formulaires énergie et justificatif SIA 380/1 (si applicable)",
  "Fire-safety evidence / ECA-AEAI position when applicable": "Justificatif incendie / position ECA-AEAI (si applicable)",
  "Special questionnaires triggered by project scope": "Questionnaires particuliers selon le projet",
  "Phase-aware constraints and unknowns handoff": "Matrice de contraintes par phase et inconnues restantes",
  "Energy dossier and SIA 380/1 justification": "Dossier énergie et justificatif SIA 380/1",
  "Fire-safety evidence under AEAI/ECA Vaud framework": "Justificatif incendie (cadre AEAI/ECA Vaud)",
  "Accessibility / construction without obstacles": "Accessibilité / construction sans obstacles",
  "Structural and seismic basis": "Bases structurales et sismiques",
  "BIM / digital information convention is contractual, not a legal permit gate": "Convention BIM / information numérique (contractuelle, non exigée par le permis)",
};
function fr(s?: string): string { if (!s) return s || ""; return FR[s] ?? FR[s.toLowerCase()] ?? s; }

function Icon({ n }: { n: string }) {
  const p: Record<string, ReactNode> = {
    grid: <><rect x="2" y="2" width="5" height="5" /><rect x="9" y="2" width="5" height="5" /><rect x="2" y="9" width="5" height="5" /><rect x="9" y="9" width="5" height="5" /></>,
    pin: <><path d="M8 14s5-4.2 5-8A5 5 0 1 0 3 6c0 3.8 5 8 5 8Z" /><circle cx="8" cy="6" r="1.6" /></>,
    doc: <><path d="M4 1.5h5L12.5 5v9.5h-9Z" /><path d="M9 1.5V5h3.5" /><path d="M6 8.5h4M6 11h4" /></>,
    shield: <><path d="M8 1.5 13 3.5v4c0 3.5-2.4 6-5 7-2.6-1-5-3.5-5-7v-4Z" /><path d="M8 6v3" /></>,
    check: <><path d="M2.5 8.5 6 12l7.5-8.5" /></>,
    spark: <><path d="M8 1.5v3M8 11.5v3M1.5 8h3M11.5 8h3M3.5 3.5l2 2M10.5 10.5l2 2M12.5 3.5l-2 2M5.5 10.5l-2 2" /></>,
    clock: <><circle cx="8" cy="8" r="6.2" /><path d="M8 4.5V8l2.5 1.6" /></>,
  };
  return <svg className="ico" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round">{p[n]}</svg>;
}

export default function App() {
  const [token, setToken] = useState("");
  const [opened, setOpened] = useState(false);
  const [view, setView] = useState<View>("dashboard");
  const [d, setD] = useState<Record<string, any>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("aedifica_token") || "" : "";
    if (t) setToken(t);
  }, []);

  async function loadAll(tk: string) {
    const g = (p: string) => api<any>(`/projects/${DEMO_ID}${p}`, { token: tk });
    const [claims, permit, opposition, compliance, ledger, next, unknowns] = await Promise.all([
      g("/claims"), g("/permit"), g("/opposition"), g("/compliance"), g("/ledger"), g("/next-step"), g("/memory/unknowns"),
    ]);
    setD({
      claims: claims.claims, permit: permit.permit, opposition: opposition.opposition,
      compliance: compliance.compliance, ledger: ledger.ledger, next: next.steps, unknowns: unknowns.unknowns,
    });
  }

  async function bootstrap(): Promise<string> {
    const tk = (await api<any>("/orgs", { method: "POST", body: { org_name: "Atelier démo", user_email: "demo@aedifica.ch" } })).token;
    localStorage.setItem("aedifica_token", tk); setToken(tk);
    return tk;
  }
  async function ensure(tk: string) {
    try { await api("/projects", { method: "POST", token: tk, body: { project_id: DEMO_ID, name: META.name, commune: META.commune } }); } catch { /* exists */ }
    // Ingest the brief once only — repeat demo starts must not duplicate claims.
    let hasClaims = false;
    try { hasClaims = (((await api<any>(`/projects/${DEMO_ID}/claims`, { token: tk })).claims) || []).length > 0; } catch { /* new project */ }
    if (!hasClaims) await api(`/projects/${DEMO_ID}/intake`, { method: "POST", token: tk, body: { query: `${META.name}, ${META.commune}`, live: false } });
    await loadAll(tk);
  }
  async function startDemo() {
    setBusy(true); setErr("");
    try {
      let tk = token || (await bootstrap());
      try { await ensure(tk); }
      catch { tk = await bootstrap(); await ensure(tk); } // stale/invalid token → fresh org, retry once
      setOpened(true); setView("dashboard");
    } catch (e: any) { setErr(e.message); }
    finally { setBusy(false); }
  }

  async function refreshLedger() {
    const [ledger, unknowns] = await Promise.all([
      api<any>(`/projects/${DEMO_ID}/ledger`, { token }), api<any>(`/projects/${DEMO_ID}/memory/unknowns`, { token }),
    ]);
    setD((x) => ({ ...x, ledger: ledger.ledger, unknowns: unknowns.unknowns }));
  }

  if (!opened) {
    return (
      <div className="empty">
        <div className="box">
          <span className="eyebrow">Æ Aedifica · ArchiOS Suisse</span>
          <h1>Le copilote de l&apos;architecte suisse</h1>
          <p>Il maîtrise la réglementation (et avoue ce qu&apos;il ignore), prépare vos dossiers de permis, et agit sur vos maquettes BIM — toujours sous votre contrôle.</p>
          <button className="ds-btn" onClick={startDemo} disabled={busy}>{busy ? "Ouverture…" : "Démarrer la démo"}</button>
          <p className="note">Projet de démonstration : {META.name}, {META.commune}. Aucune donnée inventée — chaque chiffre est sourcé ou marqué « à vérifier ».</p>
          {err && <p className="note" style={{ color: "var(--ts-conflict)" }}>{err}</p>}
        </div>
      </div>
    );
  }

  const cur = NAV.find((n) => n.id === view)!;
  return (
    <div className="app">
      <aside className="side">
        <div className="brand"><span className="wordmark"><span className="ae">Æ</span>DIFICA</span><span className="ar">ArchiOS</span></div>
        <div className="pcard">
          <div className="k">Projet ouvert</div>
          <div className="nm">{META.name}</div>
          <div className="meta">{META.commune} · VD<br />{META.phase}</div>
        </div>
        <nav className="nav">
          <div className="grp">Analyse réglementaire</div>
          {NAV.slice(0, 5).map((n) => (
            <button key={n.id} className={`navitem ${view === n.id ? "on" : ""}`} onClick={() => setView(n.id)}>
              <Icon n={n.ico} /><span><span className="lb">{n.lb}</span><span className="ds">{n.ds}</span></span>
            </button>
          ))}
          <div className="grp">Action & mémoire</div>
          {NAV.slice(5).map((n) => (
            <button key={n.id} className={`navitem ${view === n.id ? "on" : ""}`} onClick={() => setView(n.id)}>
              <Icon n={n.ico} /><span><span className="lb">{n.lb}</span><span className="ds">{n.ds}</span></span>
            </button>
          ))}
        </nav>
        <div className="foot"><span className="d" />Connecté · démo locale</div>
      </aside>

      <main className="main">
        <div className="top">
          <span className="t-nm">{cur.lb}</span>
          <span className="chip">{META.commune}</span>
          <span className="chip">{META.phase}</span>
          <span className="sp" />
          <span className="chip">L&apos;IA propose — l&apos;architecte décide</span>
        </div>
        <div className="view">
          {view === "dashboard" && <Dashboard d={d} go={setView} />}
          {view === "terrain" && <Terrain claims={d.claims} />}
          {view === "permis" && <Permis d={d.permit} />}
          {view === "opposition" && <Opposition d={d.opposition} />}
          {view === "conformite" && <Conformite d={d.compliance} />}
          {view === "copilote" && <Copilote token={token} ledger={d.ledger} onChange={refreshLedger} />}
          {view === "memoire" && <Memoire unknowns={d.unknowns} ledger={d.ledger} />}
        </div>
      </main>
    </div>
  );
}

/* ---- Dashboard ------------------------------------------------------- */
function Dashboard({ d, go }: { d: any; go: (v: View) => void }) {
  if (!d.claims) return <p className="spin">Chargement…</p>;
  const sourced = d.claims.filter((c: any) => c.state === "sourced" || c.state === "computed").length;
  const verify = d.claims.filter((c: any) => c.state === "unknown" || c.state === "assumption").length;
  const blockers = d.permit?.summary?.required_blockers ?? 0;
  const opp = d.opposition?.overall ?? "—";
  const mut = (d.ledger || []).filter((e: any) => e.mutating).length;
  return (
    <>
      <div className="vhead">
        <h2>Vue d&apos;ensemble</h2>
        <p>L&apos;état du projet en un coup d&apos;œil : ce qui est fiable, ce qui manque, et ce qu&apos;il faut traiter ensuite.</p>
      </div>
      <div className="banner"><b>Comment lire cet outil :</b> chaque donnée réglementaire est soit <b>sourcée</b> (lien officiel), soit honnêtement marquée <b>« à vérifier »</b>. L&apos;outil n&apos;invente jamais et ne décide jamais à votre place.</div>
      <div className="kpis">
        <button className="kpi" onClick={() => go("terrain")}>
          <div className="lab">Contraintes terrain</div>
          <div className="num">{sourced}<small> / {sourced + verify}</small></div>
          <div className="sub"><span className="dot" style={{ background: "var(--ts-assume)" }} />{verify} à vérifier</div>
        </button>
        <button className="kpi" onClick={() => go("permis")}>
          <div className="lab">Dossier de permis</div>
          <div className="num">{blockers === 0 ? "Prêt" : blockers}</div>
          <div className="sub">{blockers === 0 ? "aucun blocage" : "pièces requises manquantes"}</div>
        </button>
        <button className="kpi" onClick={() => go("opposition")}>
          <div className="lab">Risque d&apos;opposition</div>
          <div className="num" style={{ textTransform: "capitalize" }}>{opp}</div>
          <div className="sub">score {d.opposition?.score ?? "—"}</div>
        </button>
        <button className="kpi" onClick={() => go("copilote")}>
          <div className="lab">Actions sur maquette</div>
          <div className="num">{mut}</div>
          <div className="sub">appliquées &amp; tracées</div>
        </button>
      </div>
      <div className="grid2">
        <div className="card">
          <h3>À traiter maintenant</h3>
          {(d.next || []).slice(0, 5).map((s: any, i: number) => (
            <div className="attn" key={i}>
              <span className="ix">{String(i + 1).padStart(2, "0")}</span>
              <span><span className="tx">{fr(s.title)}</span><span className="mt">{s.action || s.kind} · phase {s.phase}</span></span>
            </div>
          ))}
          {(d.next || []).length === 0 && <p className="spin">Rien en attente.</p>}
        </div>
        <div className="card">
          <h3>Activité récente</h3>
          {[...(d.ledger || [])].reverse().slice(0, 6).map((e: any, i: number) => (
            <div className="attn" key={i} style={{ alignItems: "center" }}>
              <Trust state={e.mutating ? "conflict" : e.event_type === "approval" ? "sourced" : "computed"} label={EVENT[e.event_type] || e.event_type} />
              <span className="mt" style={{ marginTop: 0 }}>{human(e)}</span>
            </div>
          ))}
          {(d.ledger || []).length === 0 && <p className="spin">Aucune action pour l&apos;instant — voir le Copilote IA.</p>}
        </div>
      </div>
    </>
  );
}

/* ---- Terrain --------------------------------------------------------- */
function Terrain({ claims }: { claims?: any[] }) {
  if (!claims) return <p className="spin">Chargement…</p>;
  return (
    <>
      <div className="vhead"><h2>Terrain &amp; zonage</h2><p>Ce que la parcelle autorise — gabarit, distances, indices. Chaque ligne est sourcée sur une base officielle, ou marquée « à vérifier » quand la donnée n&apos;est pas publiée en ligne.</p></div>
      <div className="card">
        {claims.map((c) => (
          <div className="claim" key={c.claim_id}><Trust state={c.state} />
            <div><div className="ttl">{c.title}</div><div className="val">{c.value == null ? "Non disponible — à confirmer sur le règlement communal" : String(c.value)}</div></div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ---- Permis ---------------------------------------------------------- */
function Permis({ d }: { d?: any }) {
  if (!d) return <p className="spin">Chargement…</p>;
  return (
    <>
      <div className="vhead"><h2>Dossier de permis</h2><p>L&apos;état de complétude de votre demande, pièce par pièce et par intervenant — pour ne plus déposer un dossier incomplet.</p></div>
      <div className="banner" style={{ borderLeftColor: d.ready_for_review ? "var(--ts-sourced)" : "var(--ts-assume)" }}>
        {d.ready_for_review ? <b>Dossier prêt à déposer.</b> : <><b>Pas encore prêt — {d.summary.required_blockers} pièce(s) requise(s) manquante(s).</b> Détail ci-dessous.</>}
      </div>
      {d.groups?.map((g: any, i: number) => (
        <div className="card" key={i} style={{ marginBottom: 14 }}>
          <h3>{fr(g.actor)} · {fr(g.category)}</h3>
          {g.items.map((it: any, j: number) => (
            <div className="claim" key={j}><Trust state={it.status} />
              <div><div className="ttl">{fr(it.title)}</div>{it.missing_message && (it.status === "missing" || it.status === "assumption") && <small>{it.missing_message}</small>}</div></div>
          ))}
        </div>
      ))}
    </>
  );
}

/* ---- Opposition ------------------------------------------------------ */
function Opposition({ d }: { d?: any }) {
  if (!d) return <p className="spin">Chargement…</p>;
  const cls = (s: string) => (s || "").normalize("NFD").replace(/[̀-ͯ]/g, "");
  return (
    <>
      <div className="vhead"><h2>Risque d&apos;opposition</h2><p>Les motifs d&apos;opposition les plus probables, évalués sur les faits du dossier — pour les désamorcer avant l&apos;enquête publique.</p></div>
      <div className="banner">Niveau global : <b style={{ textTransform: "capitalize" }}>{d.overall}</b> (score {d.score}). {d.disclaimer}</div>
      <div className="card">
        {d.signals?.map((s: any, i: number) => (
          <div className="claim" key={i}><span className={`lvl ${cls(s.level)}`}>{s.level}</span>
            <div><div className="ttl">{fr(s.ground)} <small style={{ display: "inline" }}>· {fr(s.category)}</small></div>
              <div className="val" style={{ fontFamily: "var(--font-ui)", fontWeight: 400 }}>{s.basis}</div></div></div>
        ))}
      </div>
    </>
  );
}

/* ---- Conformité ------------------------------------------------------ */
function Conformite({ d }: { d?: any }) {
  if (!d) return <p className="spin">Chargement…</p>;
  const gate = (g: any, i: number) => (
    <div className="claim" key={i}><Trust state={g.status === "satisfied" ? "satisfied" : g.status === "unknown" ? "unknown" : "action_required"} />
      <div><div className="ttl">{fr(g.title)} <small style={{ display: "inline" }}>({fr(g.domain)})</small></div>{g.next_action && <small>{g.next_action}</small>}</div></div>
  );
  return (
    <>
      <div className="vhead"><h2>Conformité</h2><p>Les obligations légales et conventions à lever avant le dépôt — distinguées entre ce qui est contraignant et ce qui est contractuel.</p></div>
      <div className="banner" style={{ borderLeftColor: d.summary.legal_blockers ? "var(--ts-assume)" : "var(--ts-sourced)" }}><b>{d.summary.legal_blockers}</b> obligation(s) légale(s) encore à lever.</div>
      <div className="card" style={{ marginBottom: 14 }}><h3>Obligations légales</h3>{d.legal?.map(gate)}</div>
      <div className="card"><h3>Conventions contractuelles (BIM)</h3>{d.contractual?.map(gate)}</div>
    </>
  );
}

/* ---- Copilote IA (hero) ---------------------------------------------- */
function Copilote({ token, ledger, onChange }: { token: string; ledger?: any[]; onChange: () => void }) {
  const [txn, setTxn] = useState<any>(null);
  const [approved, setApproved] = useState(false);
  const [executed, setExecuted] = useState(false);
  const [msg, setMsg] = useState("");
  const [blocked, setBlocked] = useState(false);

  async function dryRun() {
    setMsg(""); setBlocked(false);
    try {
      const r = await api<any>(`/projects/${DEMO_ID}/adapter/dry-run`, { method: "POST", token, body: { adapter_id: "archicad_json", operations: [{ op_id: "O1", kind: "set_property", target: "AC-SPACE-101", before: "", after: "bureau", undo: "restore" }] } });
      setTxn(r.transaction); setExecuted(false); setApproved(false);
      setMsg("Aperçu prêt. Rien n'a encore changé dans votre maquette."); onChange();
    } catch (e: any) { setMsg(e.message); }
  }
  async function approve() {
    try { await api(`/projects/${DEMO_ID}/approvals`, { method: "POST", token, body: { scope: "adapter_execution", basis: "validation architecte" } }); setApproved(true); setBlocked(false); setMsg("Exécution validée par l'architecte."); onChange(); }
    catch (e: any) { setMsg(e.message); }
  }
  async function execute() {
    if (!txn) { setMsg("Demandez d'abord un aperçu."); return; }
    try {
      const r = await api<any>(`/projects/${DEMO_ID}/adapter/execute`, { method: "POST", token, body: { transaction: txn } });
      if (r.executed) { setExecuted(true); setBlocked(false); setMsg("Modification appliquée à la maquette et inscrite à l'historique — réversible."); }
      else { setBlocked(true); setMsg(r.reason || "Bloqué : validation d'exécution requise."); }
      onChange();
    } catch (e: any) { setMsg(e.message); }
  }

  const s1 = !!txn, s2 = approved, s3 = executed;
  return (
    <>
      <div className="vhead"><h2>Copilote IA · maquette Archicad</h2><p>L&apos;IA prépare une modification de votre maquette, vous la prévisualisez, vous la validez, elle l&apos;applique — et tout reste tracé et réversible. <b>Rien ne change sans votre accord.</b></p></div>

      <div className="banner">Demande simulée : <b>« Classe l&apos;espace AC-SPACE-101 en bureau et mets à jour ses propriétés. »</b> Adapter : maquette Archicad (archicad_json).</div>

      <div className="stepper">
        <div className={`step ${s3 ? "done" : s1 && !s3 ? "act" : ""}`}><div className="idx">Étape 1</div><div className="nm">Aperçu (simulation)</div></div>
        <div className={`step ${s2 ? "done" : s1 && !s2 ? "act" : ""}`}><div className="idx">Étape 2</div><div className="nm">Votre validation</div></div>
        <div className={`step ${s3 ? "done act" : ""}`}><div className="idx">Étape 3</div><div className="nm">Appliqué &amp; tracé</div></div>
      </div>

      <div className="row" style={{ gap: 10, marginBottom: 14 }}>
        <button className="ds-btn" onClick={dryRun}>Demander un aperçu</button>
        <button className="ds-btn ghost" onClick={approve} disabled={!s1}>Valider l&apos;exécution</button>
        <button className="ds-btn ghost" onClick={execute} disabled={!s1}>Appliquer à la maquette</button>
      </div>
      {msg && <div className="banner" style={{ borderLeftColor: blocked ? "var(--ts-conflict)" : s3 ? "var(--ts-sourced)" : "var(--accent)" }}>{blocked && <b>Garde-fou · </b>}{msg}</div>}

      {txn && (
        <div className="card" style={{ marginBottom: 14 }}>
          <h3>Aperçu de la transaction</h3>
          <div className="claim"><Trust state={executed ? "conflict" : "computed"} label={executed ? "Appliquée" : "Simulation"} />
            <div><div className="ttl">{txn.operation_count} opération · espace AC-SPACE-101 → « bureau »</div><div className="val">statut : {executed ? "appliqué à la maquette" : "aperçu — aucune mutation"}</div></div></div>
        </div>
      )}

      <div className="card">
        <h3>Historique du projet — horodaté, signé, réversible</h3>
        {[...(ledger || [])].map((e, i) => (
          <div className="claim" key={i}><Trust state={e.mutating ? "conflict" : e.event_type === "approval" ? "sourced" : "computed"} label={EVENT[e.event_type] || e.event_type} />
            <div><div className="ttl">{human(e)}</div>{e.mutating && <small>réf. {e.ledger_id} · réversible</small>}</div></div>
        ))}
        {(ledger || []).length === 0 && <p className="spin">Aucune action encore. Commencez par « Demander un aperçu ».</p>}
      </div>
    </>
  );
}

/* ---- Mémoire --------------------------------------------------------- */
function Memoire({ unknowns, ledger }: { unknowns?: any[]; ledger?: any[] }) {
  if (!unknowns) return <p className="spin">Chargement…</p>;
  return (
    <>
      <div className="vhead"><h2>Mémoire du projet</h2><p>Tout ce que le projet sait, ignore, ou a décidé — conservé et interrogeable. C&apos;est la mémoire durable qui permet à l&apos;IA de répondre « où en est-on ? » à tout moment.</p></div>
      <div className="grid2">
        <div className="card">
          <h3>Inconnues résiduelles ({unknowns.length})</h3>
          {unknowns.map((c: any, i: number) => (
            <div className="claim" key={i}><Trust state={c.state} /><div><div className="ttl">{c.title}</div>{c.next_action && <small>{c.next_action}</small>}</div></div>
          ))}
          {unknowns.length === 0 && <p className="spin">Aucune inconnue.</p>}
        </div>
        <div className="card">
          <h3>Journal du projet ({(ledger || []).length})</h3>
          {[...(ledger || [])].reverse().map((e: any, i: number) => (
            <div className="claim" key={i}><Trust state={e.mutating ? "conflict" : e.event_type === "approval" ? "sourced" : "computed"} label={EVENT[e.event_type] || e.event_type} />
              <div><div className="ttl">{human(e)}</div></div></div>
          ))}
          {(ledger || []).length === 0 && <p className="spin">Aucune entrée.</p>}
        </div>
      </div>
    </>
  );
}
