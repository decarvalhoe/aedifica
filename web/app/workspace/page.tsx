"use client";

import { useEffect, useState, type ReactNode } from "react";
import { api } from "@/lib/api";

const REF_ID = "DEMO-LAUSANNE-PALUD";
const REF = { name: "Place de la Palud", commune: "Lausanne" };

const PHASE: Record<string, string> = {
  "0": "Faisabilité · SIA 0–31", "32": "Projet · SIA 32", "33": "Permis · SIA 33",
  "41": "Appel d'offres · SIA 41", "51": "Exécution · SIA 51",
};
const phaseLabel = (c?: string) => (c && PHASE[c]) || (c ? `SIA ${c}` : "—");

type Project = {
  project_id: string; name: string; phase_code: string;
  jurisdiction: { commune: string; canton: string; country: string };
  claims: number; ledger_entries: number; reports: number;
};

type View = "dashboard" | "terrain" | "permis" | "opposition" | "conformite" | "copilote" | "memoire" | "couts" | "chantier";
type Status = "live" | "preview" | "soon";

const NAV: { id: View; lb: string; ds: string; ico: string; st: Status }[] = [
  { id: "dashboard", lb: "Tableau de bord", ds: "Vue d'ensemble du projet", ico: "grid", st: "live" },
  { id: "terrain", lb: "Terrain & zonage", ds: "Ce que la parcelle autorise", ico: "pin", st: "live" },
  { id: "copilote", lb: "Copilote IA · maquette", ds: "Agit sur la maquette, sous contrôle", ico: "spark", st: "live" },
  { id: "memoire", lb: "Mémoire du projet", ds: "Su, décidé, modifié — interrogeable", ico: "clock", st: "live" },
  { id: "permis", lb: "Dossier de permis", ds: "Complétude pièce par pièce", ico: "doc", st: "live" },
  { id: "opposition", lb: "Risque d'opposition", ds: "Motifs probables, sur les faits", ico: "shield", st: "live" },
  { id: "conformite", lb: "Conformité", ds: "Obligations à lever avant dépôt", ico: "check", st: "live" },
  { id: "couts", lb: "Coûts & appels d'offres", ds: "Honoraires, rentabilité, soumissions", ico: "coin", st: "live" },
  { id: "chantier", lb: "Chantier & remise", ds: "Réserves et check-list de remise", ico: "cone", st: "live" },
];
const STATUS: Record<Status, [string, string]> = {
  live: ["live", "Opérationnel"], preview: ["preview", "Données de référence"], soon: ["soon", "À venir"],
};
const GROUPS: { title: string; st: Status }[] = [
  { title: "Opérationnel", st: "live" }, { title: "Données de référence", st: "preview" }, { title: "À venir", st: "soon" },
];
function Badge({ st }: { st: Status }) { const [c, l] = STATUS[st]; return <span className={`badge ${c}`}><span className="d" />{l}</span>; }

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
    coin: <><circle cx="8" cy="8" r="6.2" /><path d="M8 4.3v7.4M6.2 6.3h3M6.2 8.3h3" /></>,
    cone: <><path d="M8 2.2 12 13H4Z" /><path d="M6 8.5h4M3 13h10" /></>,
    plus: <><path d="M8 3v10M3 8h10" /></>,
  };
  return <svg className="ico" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round">{p[n]}</svg>;
}

export default function App() {
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [active, setActive] = useState<Project | null>(null);
  const [view, setView] = useState<View>("dashboard");
  const [d, setD] = useState<Record<string, any>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [flashKey, setFlashKey] = useState<string | null>(null);
  const [users, setUsers] = useState<any[] | null>(null);

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("aedifica_token") : null;
    if (t) verify(t); else setReady(true);
  }, []);

  async function verify(t: string) {
    try { await loadProjects(t); await loadUsers(t); setToken(t); }
    catch { localStorage.removeItem("aedifica_token"); }
    finally { setReady(true); }
  }
  async function loadProjects(t: string): Promise<Project[]> {
    const ids = (await api<any>("/projects", { token: t })).projects as string[];
    const sums = await Promise.all(ids.map((id) => api<any>(`/projects/${id}`, { token: t }).then((r) => r.project as Project)));
    setProjects(sums);
    return sums;
  }
  async function loadUsers(t: string) {
    try { setUsers((await api<any>("/orgs/users", { token: t })).users); }
    catch { setUsers(null); } // caller is not an owner — team panel hidden
  }
  async function addUser(email: string, name: string, role: string): Promise<string> {
    const r = await api<any>("/orgs/users", { method: "POST", token: token!, body: { email, name, role } });
    await loadUsers(token!);
    return r.token;
  }
  async function setUserRole(id: number, role: string) {
    await api(`/orgs/users/${id}`, { method: "PATCH", token: token!, body: { role } });
    await loadUsers(token!);
  }

  async function seedReference(t: string) {
    try { await api("/projects", { method: "POST", token: t, body: { project_id: REF_ID, name: REF.name, commune: REF.commune, seed_reports: true } }); } catch { /* exists */ }
    try {
      const c = ((await api<any>(`/projects/${REF_ID}/claims`, { token: t })).claims) || [];
      if (!c.length) await api(`/projects/${REF_ID}/intake`, { method: "POST", token: t, body: { query: `${REF.name}, ${REF.commune}`, live: false } });
    } catch { /* ignore */ }
  }

  async function register(orgName: string, email: string) {
    setBusy(true); setErr("");
    try {
      const t = (await api<any>("/orgs", { method: "POST", body: { org_name: orgName, user_email: email } })).token as string;
      localStorage.setItem("aedifica_token", t);
      await seedReference(t);
      await loadProjects(t); await loadUsers(t);
      setFlashKey(t); setToken(t);
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }
  async function signIn(key: string) {
    setBusy(true); setErr("");
    try { await loadProjects(key); await loadUsers(key); localStorage.setItem("aedifica_token", key); setToken(key); }
    catch { setErr("Clé d'accès invalide."); } finally { setBusy(false); }
  }
  function signOut() {
    localStorage.removeItem("aedifica_token");
    setToken(null); setProjects(null); setActive(null); setD({}); setFlashKey(null);
  }

  async function createProject(name: string, commune: string) {
    const id = (name.trim().toUpperCase().replace(/[^A-Z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40)) || `PROJ-${(projects?.length ?? 0) + 1}`;
    setBusy(true); setErr("");
    try {
      await api("/projects", { method: "POST", token: token!, body: { project_id: id, name, commune } });
      const sums = await loadProjects(token!);
      const p = sums.find((s) => s.project_id === id);
      if (p) await openProject(p);
    } catch (e: any) { setErr(e.message?.includes("exists") ? "Un projet porte déjà ce nom." : e.message); } finally { setBusy(false); }
  }
  async function openProject(p: Project) {
    setActive(p); setView("dashboard"); setD({}); setFlashKey(null);
    try { await loadAll(p, token!); } catch (e: any) { setErr(e.message); }
  }

  async function loadAll(p: Project, t: string) {
    const pid = p.project_id;
    const g = (path: string) => api<any>(`/projects/${pid}${path}`, { token: t });
    const sup = api<any>(`/communes/${p.jurisdiction.commune}/${p.jurisdiction.canton}/support`, { token: t }).then((r) => r.support).catch(() => null);
    const [claims, permit, opposition, compliance, cost, site, ledger, next, unknowns, support] = await Promise.all([
      g("/claims"), g("/permit"), g("/opposition"), g("/compliance"), g("/cost"), g("/site"), g("/ledger"), g("/next-step"), g("/memory/unknowns"), sup,
    ]);
    setD({
      claims: claims.claims, permit: permit.permit, opposition: opposition.opposition, compliance: compliance.compliance,
      cost: cost.cost, site: site.site, ledger: ledger.ledger, next: next.steps, unknowns: unknowns.unknowns, support,
    });
  }
  async function lookup(query: string) {
    if (!active) return;
    const r = await api<any>(`/projects/${active.project_id}/intake`, { method: "POST", token: token!, body: { query, live: true } });
    await loadAll(active, token!);
    setD((x) => ({ ...x, intakeMode: r.mode, intakeReason: r.reason }));
  }
  async function requestCommune() {
    if (!active) return;
    await api("/communes", { method: "POST", token: token!, body: { commune: active.jurisdiction.commune, canton: active.jurisdiction.canton } });
    await loadAll(active, token!);
  }
  async function submitPermit(itemId: string, present: boolean) {
    if (!active) return;
    const r = await api<any>(`/projects/${active.project_id}/permit/dossier`, { method: "POST", token: token!, body: { item_id: itemId, present } });
    setD((x) => ({ ...x, permit: r.permit }));
  }
  async function refreshLedger() {
    if (!active) return;
    const [ledger, unknowns] = await Promise.all([
      api<any>(`/projects/${active.project_id}/ledger`, { token: token! }),
      api<any>(`/projects/${active.project_id}/memory/unknowns`, { token: token! }),
    ]);
    setD((x) => ({ ...x, ledger: ledger.ledger, unknowns: unknowns.unknowns }));
  }

  if (!ready) return <div className="empty"><div className="spin">Chargement…</div></div>;
  if (!token) return <Auth busy={busy} err={err} onRegister={register} onSignIn={signIn} />;
  if (!active) return (
    <ProjectsScreen projects={projects} busy={busy} err={err} flashKey={flashKey} users={users}
      onOpen={openProject} onCreate={createProject} onSignOut={signOut} dismissFlash={() => setFlashKey(null)}
      onAddUser={addUser} onSetRole={setUserRole} />
  );

  const cur = NAV.find((n) => n.id === view)!;
  const j = active.jurisdiction;
  return (
    <div className="app">
      <aside className="side">
        <div className="brand"><span className="wordmark"><span className="ae">Æ</span>DIFICA</span><span className="ar">ArchiOS</span></div>
        <button className="back" onClick={() => { setActive(null); setD({}); }}>← Tous les projets</button>
        <div className="pcard">
          <div className="k">Projet ouvert</div>
          <div className="nm">{active.name}</div>
          <div className="meta">{j.commune} · {j.canton}<br />{phaseLabel(active.phase_code)}</div>
        </div>
        <nav className="nav">
          {GROUPS.filter((grp) => NAV.some((n) => n.st === grp.st)).map((grp) => (
            <div key={grp.st}>
              <div className="grp">{grp.title}</div>
              {NAV.filter((n) => n.st === grp.st).map((n) => (
                <button key={n.id} className={`navitem ${view === n.id ? "on" : ""} ${n.st}`} onClick={() => setView(n.id)}>
                  <Icon n={n.ico} /><span className="lbwrap"><span className="lb">{n.lb}</span><span className="ds">{n.ds}</span></span>
                  {n.st === "preview" && <span className="tag">Aperçu</span>}
                  {n.st === "soon" && <span className="tag">Bientôt</span>}
                </button>
              ))}
            </div>
          ))}
        </nav>
        <div className="foot"><span className="d" /><button className="signout" onClick={signOut}>Se déconnecter</button></div>
      </aside>

      <main className="main">
        <div className="top">
          <span className="t-nm">{cur.lb}</span>
          <Badge st={cur.st} />
          <span className="sp" />
          <span className="chip">{j.commune}</span>
          <span className="chip">L&apos;IA propose — l&apos;architecte décide</span>
        </div>
        <div className="view">
          {cur.st === "preview" && (
            <div className="banner" style={{ borderLeftColor: "var(--ts-assume)" }}>
              <b>Données de référence.</b> Cette surface tourne sur un dossier de référence (Place de la Palud) : les règles, la structure et les états « fourni / manquant » sont en place. Le branchement au dossier réel de votre projet est la prochaine étape — rien n&apos;est inventé ici.
            </div>
          )}
          {view === "dashboard" && <Dashboard d={d} go={setView} />}
          {view === "terrain" && <Terrain claims={d.claims} mode={d.intakeMode} reason={d.intakeReason} support={d.support} commune={j.commune} onLookup={lookup} onRequest={requestCommune} />}
          {view === "permis" && <Permis d={d.permit} onSubmit={submitPermit} />}
          {view === "opposition" && <Opposition d={d.opposition} />}
          {view === "conformite" && <Conformite d={d.compliance} />}
          {view === "copilote" && <Copilote token={token} pid={active.project_id} ledger={d.ledger} onChange={refreshLedger} />}
          {view === "memoire" && <Memoire unknowns={d.unknowns} ledger={d.ledger} />}
          {view === "couts" && <Couts d={d.cost} />}
          {view === "chantier" && <Chantier d={d.site} />}
        </div>
      </main>
    </div>
  );
}

/* ---- Auth (register / sign-in) --------------------------------------- */
function Auth({ busy, err, onRegister, onSignIn }: { busy: boolean; err: string; onRegister: (o: string, e: string) => void; onSignIn: (k: string) => void; }) {
  const [mode, setMode] = useState<"register" | "signin">("register");
  const [org, setOrg] = useState(""); const [email, setEmail] = useState(""); const [key, setKey] = useState("");
  return (
    <div className="empty">
      <div className="box">
        <span className="eyebrow">Æ Aedifica · ArchiOS Suisse</span>
        <h1>Le copilote de l&apos;architecte suisse</h1>
        <p>Il maîtrise la réglementation (et avoue ce qu&apos;il ignore), prépare vos dossiers, et agit sur vos maquettes BIM — toujours sous votre contrôle.</p>
        <div className="seg">
          <button className={mode === "register" ? "on" : ""} onClick={() => setMode("register")}>Créer un atelier</button>
          <button className={mode === "signin" ? "on" : ""} onClick={() => setMode("signin")}>Se connecter</button>
        </div>
        {mode === "register" ? (
          <div className="fields">
            <input className="field" placeholder="Nom de l'atelier" value={org} onChange={(e) => setOrg(e.target.value)} />
            <input className="field" placeholder="Votre e-mail" value={email} onChange={(e) => setEmail(e.target.value)} />
            <button className="ds-btn" disabled={busy || !org || !email} onClick={() => onRegister(org, email)}>{busy ? "Création…" : "Créer l'atelier"}</button>
            <p className="note">Une clé d&apos;accès vous sera attribuée à la création — conservez-la pour vous reconnecter (pas encore de mot de passe : voir #209).</p>
          </div>
        ) : (
          <div className="fields">
            <input className="field" placeholder="Clé d'accès" value={key} onChange={(e) => setKey(e.target.value)} />
            <button className="ds-btn" disabled={busy || !key} onClick={() => onSignIn(key.trim())}>{busy ? "Connexion…" : "Se connecter"}</button>
            <p className="note">Collez la clé d&apos;accès reçue à la création de votre atelier.</p>
          </div>
        )}
        {err && <p className="note" style={{ color: "var(--ts-conflict)" }}>{err}</p>}
      </div>
    </div>
  );
}

/* ---- Projects hub ---------------------------------------------------- */
function ProjectsScreen({ projects, busy, err, flashKey, users, onOpen, onCreate, onSignOut, dismissFlash, onAddUser, onSetRole }: {
  projects: Project[] | null; busy: boolean; err: string; flashKey: string | null; users: any[] | null;
  onOpen: (p: Project) => void; onCreate: (n: string, c: string) => void; onSignOut: () => void; dismissFlash: () => void;
  onAddUser: (e: string, n: string, r: string) => Promise<string>; onSetRole: (id: number, r: string) => Promise<void>;
}) {
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState(""); const [commune, setCommune] = useState("Lausanne");
  return (
    <div className="hub">
      <div className="hubwrap">
        <div className="hubhead">
          <span className="wordmark"><span className="ae">Æ</span>DIFICA</span>
          <span className="eyebrow">ArchiOS Suisse</span>
          <span className="sp" />
          <button className="linkbtn" onClick={onSignOut}>Se déconnecter</button>
        </div>
        <h1>Vos projets</h1>
        <p className="lead">Ouvrez un projet, ou créez-en un nouveau. Chaque projet a sa propre parcelle, sa mémoire et son historique d&apos;actions.</p>

        {flashKey && (
          <div className="flash">
            <b>Atelier créé.</b> Voici votre clé d&apos;accès — conservez-la pour vous reconnecter :
            <code>{flashKey}</code>
            <button className="linkbtn" style={{ paddingLeft: 0 }} onClick={dismissFlash}>J&apos;ai noté ma clé</button>
          </div>
        )}

        <div className="plist">
          {(projects || []).map((p) => (
            <button className="proj-row" key={p.project_id} onClick={() => onOpen(p)}>
              <Icon n="pin" />
              <span style={{ flex: 1 }}>
                <span className="nm" style={{ display: "block" }}>{p.name}</span>
                <span className="me">{p.jurisdiction.commune} · {p.jurisdiction.canton} · {phaseLabel(p.phase_code)} — {p.claims} contraintes · {p.ledger_entries} actions</span>
              </span>
              <span className="chip">Ouvrir</span>
            </button>
          ))}
          {projects && projects.length === 0 && <p className="note" style={{ textAlign: "left" }}>Aucun projet pour l&apos;instant — créez-en un ci-dessous.</p>}

          {creating ? (
            <div className="proj-row" style={{ flexDirection: "column", alignItems: "stretch", gap: 10 }}>
              <div className="fields" style={{ marginBottom: 0 }}>
                <input className="field" placeholder="Nom du projet" value={name} onChange={(e) => setName(e.target.value)} />
                <input className="field" placeholder="Commune (ex. Lausanne)" value={commune} onChange={(e) => setCommune(e.target.value)} />
              </div>
              <div className="row" style={{ gap: 10 }}>
                <button className="ds-btn" disabled={busy || !name || !commune} onClick={() => onCreate(name, commune)}>{busy ? "Création…" : "Créer & ouvrir"}</button>
                <button className="ds-btn ghost" onClick={() => setCreating(false)}>Annuler</button>
              </div>
            </div>
          ) : (
            <button className="proj-row soon" style={{ borderStyle: "dashed", opacity: 1, cursor: "pointer" }} onClick={() => setCreating(true)}>
              <Icon n="plus" /><span style={{ flex: 1 }}><span className="nm" style={{ display: "block" }}>Nouveau projet</span><span className="me">Créer un projet vierge</span></span>
              <span className="chip">Créer</span>
            </button>
          )}
        </div>

        {users && <Team users={users} onAdd={onAddUser} onSetRole={onSetRole} />}

        {err && <p className="note" style={{ color: "var(--ts-conflict)" }}>{err}</p>}
      </div>
    </div>
  );
}

const ROLE_FR: Record<string, string> = { owner: "Propriétaire", member: "Membre", viewer: "Lecteur" };
function Team({ users, onAdd, onSetRole }: { users: any[]; onAdd: (e: string, n: string, r: string) => Promise<string>; onSetRole: (id: number, r: string) => Promise<void>; }) {
  const [inv, setInv] = useState(false);
  const [email, setEmail] = useState(""); const [name, setName] = useState(""); const [role, setRole] = useState("member");
  const [busy, setBusy] = useState(false); const [newKey, setNewKey] = useState<string | null>(null); const [err, setErr] = useState("");
  const add = async () => {
    setBusy(true); setErr("");
    try { const k = await onAdd(email, name || email, role); setNewKey(k); setEmail(""); setName(""); setInv(false); }
    catch (e: any) { setErr(e.message?.includes("exists") ? "Cet e-mail est déjà membre." : e.message); } finally { setBusy(false); }
  };
  return (
    <div className="card" style={{ marginTop: 24 }}>
      <h3>Équipe ({users.length})</h3>
      {users.map((u) => (
        <div className="claim" key={u.id} style={{ alignItems: "center" }}>
          <div style={{ flex: 1 }}><div className="ttl">{u.name}{u.is_you && <small style={{ display: "inline" }}> · vous</small>}</div><small>{u.email}</small></div>
          <select className="field" style={{ padding: "6px 8px" }} value={u.role} disabled={u.is_you} onChange={(e) => onSetRole(u.id, e.target.value)}>
            {Object.entries(ROLE_FR).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </div>
      ))}
      {newKey && <div className="flash" style={{ marginTop: 12 }}><b>Membre ajouté.</b> Clé d&apos;accès à lui transmettre :<code>{newKey}</code><button className="linkbtn" style={{ paddingLeft: 0 }} onClick={() => setNewKey(null)}>OK</button></div>}
      {inv ? (
        <div className="fields" style={{ marginTop: 12 }}>
          <input className="field" placeholder="E-mail du collaborateur" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input className="field" placeholder="Nom (optionnel)" value={name} onChange={(e) => setName(e.target.value)} />
          <select className="field" value={role} onChange={(e) => setRole(e.target.value)}>
            {Object.entries(ROLE_FR).map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
          <div className="row" style={{ gap: 10 }}>
            <button className="ds-btn" disabled={busy || !email} onClick={add}>{busy ? "Ajout…" : "Inviter"}</button>
            <button className="ds-btn ghost" onClick={() => setInv(false)}>Annuler</button>
          </div>
          {err && <p className="note" style={{ color: "var(--ts-conflict)" }}>{err}</p>}
        </div>
      ) : (
        <button className="linkbtn" style={{ paddingLeft: 0, marginTop: 8 }} onClick={() => setInv(true)}>+ Inviter un collaborateur</button>
      )}
    </div>
  );
}

/* ---- Coûts & appels d'offres ----------------------------------------- */
function Couts({ d }: { d?: any }) {
  if (!d) return <p className="spin">Chargement…</p>;
  const c = d.cockpit;
  const chf = (n: number) => "CHF " + Number(n).toLocaleString("fr-CH");
  const head = <div className="vhead"><h2>Coûts &amp; appels d&apos;offres</h2><p>Estimation d&apos;honoraires, rentabilité du mandat et hypothèses portées en comparatif de soumissions. L&apos;outil n&apos;embarque aucun coefficient SIA payant — il enregistre les hypothèses de l&apos;atelier.</p></div>;
  if (!c) return (<>{head}<div className="placeholder"><h4>Aucune estimation pour ce projet</h4><p>L&apos;estimation d&apos;honoraires et les hypothèses de soumission n&apos;ont pas encore été saisies. Le projet de référence « Place de la Palud » montre le rendu attendu.</p></div></>);
  return (
    <>
      {head}
      <div className="kpis">
        <div className="kpi"><div className="lab">Honoraires estimés</div><div className="num" style={{ fontSize: 23 }}>{chf(c.estimated_fee_chf)}</div><div className="sub">{c.estimated_hours} h · {c.hourly_rate_chf} CHF/h</div></div>
        <div className="kpi"><div className="lab">Marge cible</div><div className="num">{c.target_margin_percent}%</div><div className="sub">objectif atelier</div></div>
        <div className="kpi"><div className="lab">Risque de marge</div><div className="num" style={{ textTransform: "capitalize" }}>{c.margin_risk}</div><div className="sub">{c.absorbed_hours} h absorbées · {chf(c.absorbed_cost_chf)}</div></div>
        <div className="kpi"><div className="lab">Prestations spéciales</div><div className="num">{c.special_prestations.length}</div><div className="sub">à chiffrer ou exclure</div></div>
      </div>
      <div className="grid2">
        <div className="card"><h3>Prestations absorbées (non chiffrées)</h3>
          {c.absorbed_tasks.map((t: any, i: number) => (
            <div className="claim" key={i}><Trust state="assumption" label="absorbé" /><div><div className="ttl">{t.title}</div><small>{t.estimated_hours} h · {t.action}</small></div></div>
          ))}
        </div>
        <div className="card"><h3>Hypothèses portées en soumission</h3>
          {d.tender_assumptions.map((a: any, i: number) => (
            <div className="claim" key={i}><Trust state="computed" label={a.kind} /><div><div className="ttl">{a.title}</div><small>colonne : {a.offer_comparison_column}</small></div></div>
          ))}
        </div>
      </div>
    </>
  );
}

/* ---- Chantier & remise ----------------------------------------------- */
function Chantier({ d }: { d?: any }) {
  if (!d) return <p className="spin">Chargement…</p>;
  const map = (s: string) => (s === "closed" ? "satisfied" : s === "blocked" ? "conflict" : s === "open" ? "unknown" : "assumption");
  const lbl: Record<string, string> = { open: "ouvert", closed: "clos", blocked: "bloqué" };
  const sev = (s: string) => (s === "high" ? "eleve" : s === "medium" ? "modere" : "faible");
  const head = <div className="vhead"><h2>Chantier &amp; remise</h2><p>Suivi d&apos;exécution : réserves / défauts et check-list de remise, avec responsable et échéance — pour clôturer proprement.</p></div>;
  if (d.data_basis === "empty") return (<>{head}<div className="placeholder"><h4>Aucun suivi de chantier pour ce projet</h4><p>Les réserves et la check-list de remise apparaîtront ici en phase exécution. Le projet de référence « Place de la Palud » montre le rendu attendu.</p></div></>);
  return (
    <>
      {head}
      <div className="banner" style={{ borderLeftColor: d.summary.handover_blocked ? "var(--ts-conflict)" : "var(--ts-sourced)" }}><b>{d.summary.handover_blocked}</b> point(s) de remise bloqué(s) · <b>{d.summary.defects_open}</b> défaut(s) ouvert(s).</div>
      <div className="grid2">
        <div className="card"><h3>Check-list de remise</h3>
          {d.handover.map((i: any, k: number) => (
            <div className="claim" key={k}><Trust state={map(i.status)} label={lbl[i.status] || i.status} /><div><div className="ttl">{i.title}</div><small>{i.responsible_party} · échéance {i.due_at}</small></div></div>
          ))}
        </div>
        <div className="card"><h3>Réserves &amp; défauts</h3>
          {d.defects.map((x: any, k: number) => (
            <div className="claim" key={k}><span className={`lvl ${sev(x.severity)}`}>{x.severity}</span><div><div className="ttl">{x.title}</div><small>{x.responsible_party} · {x.status} · échéance {x.target_resolution}</small></div></div>
          ))}
        </div>
      </div>
    </>
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
      <div className="banner"><b>Comment lire cet outil :</b> chaque donnée est soit <b>sourcée</b> (lien officiel), soit marquée <b>« à vérifier »</b> — jamais inventée. Et chaque surface annonce sa maturité : <b>opérationnelle</b>, <b>données de référence</b> (réf.), ou <b>à venir</b>. L&apos;IA propose ; l&apos;architecte décide.</div>
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
function Terrain({ claims, mode, reason, support, commune, onLookup, onRequest }: {
  claims?: any[]; mode?: string; reason?: string; support?: any; commune?: string;
  onLookup: (q: string) => Promise<void>; onRequest: () => Promise<void>;
}) {
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState("");
  if (!claims) return <p className="spin">Chargement…</p>;
  const lookup = async () => { if (!q.trim()) return; setBusy("lookup"); try { await onLookup(q.trim()); } catch { /* surfaced upstream */ } finally { setBusy(""); } };
  const req = async () => { setBusy("commune"); try { await onRequest(); } catch { /* */ } finally { setBusy(""); } };
  const usable = support ? support.usable : true;
  return (
    <>
      <div className="vhead"><h2>Terrain &amp; zonage</h2><p>Ce que la parcelle autorise — gabarit, distances, indices. Chaque ligne est sourcée sur une base officielle, ou marquée « à vérifier » quand la donnée n&apos;est pas publiée en ligne.</p></div>

      {support && !usable && (
        <div className="banner" style={{ borderLeftColor: "var(--ts-assume)" }}>
          Commune <b>{commune}</b> pas encore prise en charge — l&apos;enveloppe constructible ne peut pas être fiabilisée.{" "}
          <button className="ds-btn ghost" style={{ padding: "6px 12px", marginLeft: 6 }} onClick={req} disabled={busy === "commune"}>{busy === "commune" ? "Demande…" : "Demander l'ingestion"}</button>
          {support.status && <small style={{ display: "block", marginTop: 6 }}>statut du pack : {support.status}</small>}
        </div>
      )}

      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row" style={{ gap: 10 }}>
          <input className="field" style={{ flex: 1 }} placeholder="Adresse ou parcelle — ex. Place de la Palud, Lausanne" value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && lookup()} />
          <button className="ds-btn" onClick={lookup} disabled={busy === "lookup"}>{busy === "lookup" ? "Recherche…" : "Rechercher (live)"}</button>
        </div>
        {mode === "offline" && <p className="note">Recherche live indisponible — données de référence affichées. {reason}</p>}
        {mode === "live" && <p className="note" style={{ color: "var(--ts-sourced)" }}>Parcelle résolue en direct (OEREB).</p>}
      </div>

      {claims.length === 0 ? (
        <div className="placeholder">
          <h4>Aucune parcelle analysée pour ce projet</h4>
          <p>Lancez une recherche d&apos;adresse ci-dessus pour résoudre la parcelle. Le projet de référence « Place de la Palud » montre le rendu attendu — chaque contrainte sourcée ou marquée « à vérifier ».</p>
        </div>
      ) : (
        <div className="card">
          {claims.map((c) => (
            <div className="claim" key={c.claim_id}><Trust state={c.state} />
              <div><div className="ttl">{c.title}</div><div className="val">{c.value == null ? "Non disponible — à confirmer sur le règlement communal" : String(c.value)}</div></div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

/* ---- Permis ---------------------------------------------------------- */
function Permis({ d, onSubmit }: { d?: any; onSubmit: (itemId: string, present: boolean) => Promise<void> }) {
  const [busy, setBusy] = useState("");
  if (!d) return <p className="spin">Chargement…</p>;
  const toggle = async (id: string, present: boolean) => { setBusy(id); try { await onSubmit(id, present); } catch { /* surfaced upstream */ } finally { setBusy(""); } };
  return (
    <>
      <div className="vhead"><h2>Dossier de permis</h2><p>L&apos;état de complétude de votre demande, pièce par pièce et par intervenant. Marquez chaque pièce comme fournie au fur et à mesure — pour ne plus déposer un dossier incomplet.</p></div>
      <div className="banner" style={{ borderLeftColor: d.ready_for_review ? "var(--ts-sourced)" : "var(--ts-assume)" }}>
        {d.ready_for_review ? <b>Dossier prêt à déposer.</b> : <><b>Pas encore prêt — {d.summary.required_blockers} pièce(s) requise(s) manquante(s).</b> Détail ci-dessous.</>}
        {d.data_basis === "empty" && <span> Aucune pièce déposée pour ce projet — le dossier démarre vide.</span>}
      </div>
      {d.groups?.map((g: any, i: number) => (
        <div className="card" key={i} style={{ marginBottom: 14 }}>
          <h3>{fr(g.actor)} · {fr(g.category)}</h3>
          {g.items.map((it: any, j: number) => {
            const present = it.status === "present";
            return (
              <div className="claim" key={j} style={{ alignItems: "center" }}><Trust state={it.status} />
                <div style={{ flex: 1 }}><div className="ttl">{fr(it.title)}</div>{it.missing_message && (it.status === "missing" || it.status === "assumption") && <small>{it.missing_message}</small>}</div>
                <button className="ds-btn ghost" style={{ padding: "6px 12px" }} disabled={busy === it.item_id} onClick={() => toggle(it.item_id, !present)}>
                  {busy === it.item_id ? "…" : present ? "Retirer" : "Fournir"}
                </button>
              </div>
            );
          })}
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
      {d.overall ? (
        <>
          <div className="banner">Niveau global : <b style={{ textTransform: "capitalize" }}>{d.overall}</b> (score {d.score}). {d.disclaimer}</div>
          <div className="card">
            {d.signals?.map((s: any, i: number) => (
              <div className="claim" key={i}><span className={`lvl ${cls(s.level)}`}>{s.level}</span>
                <div><div className="ttl">{fr(s.ground)} <small style={{ display: "inline" }}>· {fr(s.category)}</small></div>
                  <div className="val" style={{ fontFamily: "var(--font-ui)", fontWeight: 400 }}>{s.basis}</div></div></div>
            ))}
          </div>
        </>
      ) : (
        <div className="placeholder"><h4>Aucune analyse d&apos;opposition</h4><p>{d.disclaimer}</p></div>
      )}
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
function Copilote({ token, pid, ledger, onChange }: { token: string; pid: string; ledger?: any[]; onChange: () => void }) {
  const [txn, setTxn] = useState<any>(null);
  const [approved, setApproved] = useState(false);
  const [executed, setExecuted] = useState(false);
  const [msg, setMsg] = useState("");
  const [blocked, setBlocked] = useState(false);

  async function dryRun() {
    setMsg(""); setBlocked(false);
    try {
      const r = await api<any>(`/projects/${pid}/adapter/dry-run`, { method: "POST", token, body: { adapter_id: "archicad_json", operations: [{ op_id: "O1", kind: "set_property", target: "AC-SPACE-101", before: "", after: "bureau", undo: "restore" }] } });
      setTxn(r.transaction); setExecuted(false); setApproved(false);
      setMsg("Aperçu prêt. Rien n'a encore changé dans votre maquette."); onChange();
    } catch (e: any) { setMsg(e.message); }
  }
  async function approve() {
    try { await api(`/projects/${pid}/approvals`, { method: "POST", token, body: { scope: "adapter_execution", basis: "validation architecte" } }); setApproved(true); setBlocked(false); setMsg("Exécution validée par l'architecte."); onChange(); }
    catch (e: any) { setMsg(e.message); }
  }
  async function execute() {
    if (!txn) { setMsg("Demandez d'abord un aperçu."); return; }
    try {
      const r = await api<any>(`/projects/${pid}/adapter/execute`, { method: "POST", token, body: { transaction: txn } });
      if (r.executed) { setExecuted(true); setBlocked(false); setMsg("Modification appliquée à la maquette et inscrite à l'historique — réversible."); }
      else { setBlocked(true); setMsg(r.reason || "Bloqué : validation d'exécution requise."); }
      onChange();
    } catch (e: any) { setMsg(e.message); }
  }

  const s1 = !!txn, s2 = approved, s3 = executed;
  return (
    <>
      <div className="vhead"><h2>Copilote IA · maquette Archicad</h2><p>L&apos;IA prépare une modification de votre maquette, vous la prévisualisez, vous la validez, elle l&apos;applique — et tout reste tracé et réversible. <b>Rien ne change sans votre accord.</b></p></div>

      <div className="banner">Boucle d&apos;action <b>réelle</b> : aperçu → validation → exécution → journal. L&apos;adaptateur Archicad fonctionne en mode <b>replay</b> (modèle rejoué) ; la connexion à une instance Archicad <b>live</b> est la prochaine étape. Exemple : <b>« classer l&apos;espace AC-SPACE-101 en bureau »</b>.</div>

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
