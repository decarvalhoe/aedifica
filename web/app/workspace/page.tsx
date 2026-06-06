"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { api, apiUpload } from "@/lib/api";
import { AttachField } from "./AttachField";
import { GanttView } from "./GanttView";
import { KanbanView } from "./KanbanView";
import { PhaseTasks } from "./PhaseTasks";
import { Foresight } from "./Foresight";

const REF_ID = "DEMO-LAUSANNE-PALUD";
const REF = { name: "Place de la Palud", commune: "Lausanne" };

/* ---- SIA phase model (official sub-phases SIA 112/102) ---- */
const PHASES: [string, string][] = [
  ["11", "Objectifs"], ["21", "Faisab."], ["22", "Mandataires"], ["31", "Avant-pr."],
  ["32", "Projet"], ["33", "Permis"], ["41", "Appel d'offres"], ["51", "Exécution"],
  ["52", "Chantier"], ["53", "Service"], ["61", "Exploit."],
];
// W11.A: a fresh project carries phase_code = "0" by default — this used to
// silently get coerced to "11" by norm(), which made every UI element (project
// card, phase rail, dashboard title, prochain pas) lie that the project was in
// phase 11. Now norm() preserves the unset state, and phase{Index,Label} return
// explicit "not started" signals that the UI handles distinctly.
const PHASE_ALIAS: Record<string, string> = { "5x": "51", "6": "61" };
const isPhaseUnset = (c?: string) => !c || c === "0" || c.trim() === "";
const norm = (c?: string) => (c && PHASE_ALIAS[c]) || c || "";
const PHASE_LABEL_FR: Record<string, string> = { "11": "Définition des objectifs", "21": "Études préliminaires", "22": "Choix des mandataires", "31": "Avant-projet", "32": "Projet de l'ouvrage", "33": "Autorisation / permis", "41": "Appel d'offres", "51": "Projet d'exécution", "52": "Exécution / chantier", "53": "Mise en service", "61": "Exploitation" };
const phaseIndex = (code?: string) => (isPhaseUnset(code) ? -1 : PHASES.findIndex((p) => p[0] === norm(code)));
const phaseLabel = (code?: string) => {
  if (isPhaseUnset(code)) return "Phase à cadrer";
  const c = norm(code);
  const lb = PHASE_LABEL_FR[c];
  return lb ? `Phase ${c} · ${lb}` : `Phase ${c}`;
};
// SIA cost-precision convergence per phase (from the SIA Vaud chart)
const COST_PRECISION: Record<string, string> = { "31": "± 15 %", "32": "± 10 %", "33": "± 10 %", "41": "ferme", "51": "ferme", "52": "ferme" };

type View = "dashboard" | "taches" | "terrain" | "checklist" | "coordination" | "intervenants" | "documents" | "brs" | "permis" | "opposition" | "conformite" | "copilote" | "memoire" | "couts" | "chantier" | "equipe" | "foresight" | "atelier";
// W13: views that don't require an active project — they're aggregated or org-level.
const PROJECT_AGNOSTIC: View[] = ["atelier", "equipe"];
// W11 P0: every NAV icon references the official Datum sprite by symbol id —
// `web/public/assets/functional-icons.svg#ic-*` — no more inline custom SVG.
// Closest semantic match per surface, taken from the DS iconography page §05.
const NAV: { id: View; lb: string; ico: string; ph?: string; grp: string }[] = [
  { id: "dashboard", lb: "Tableau de bord", ico: "ic-portfolio", grp: "Pilotage" },
  { id: "foresight", lb: "Foresight · prédictions", ico: "ic-datum-target", grp: "Pilotage" },
  { id: "taches", lb: "Tâches & priorités", ico: "ic-claims", grp: "Pilotage" },
  { id: "checklist", lb: "Checklist SIA", ico: "ic-check", grp: "Pilotage" },
  { id: "terrain", lb: "Terrain & zonage", ico: "ic-map-pin", ph: "0–11", grp: "Pilotage" },
  { id: "copilote", lb: "Copilote · maquette", ico: "ic-datum-target", ph: "32", grp: "Pilotage" },
  { id: "memoire", lb: "Mémoire", ico: "ic-ledger", ph: "6", grp: "Pilotage" },
  { id: "coordination", lb: "Coordination", ico: "ic-layers", grp: "Coordination" },
  { id: "intervenants", lb: "Intervenants", ico: "ic-claims", ph: "0", grp: "Coordination" },
  { id: "documents", lb: "Documents & sources", ico: "ic-source", ph: "0–33", grp: "Coordination" },
  { id: "brs", lb: "Exigences (BRS)", ico: "ic-decisions", grp: "Coordination" },
  { id: "permis", lb: "Dossier de permis", ico: "ic-permit", ph: "33", grp: "Dossier réglementaire" },
  { id: "opposition", lb: "Risque d'opposition", ico: "ic-opposition", ph: "33", grp: "Dossier réglementaire" },
  { id: "conformite", lb: "Conformité", ico: "ic-check", ph: "33", grp: "Dossier réglementaire" },
  { id: "couts", lb: "Coûts & soumissions", ico: "ic-report", ph: "41", grp: "Économie & chantier" },
  { id: "chantier", lb: "Chantier & remise", ico: "ic-datum-dimension", ph: "52", grp: "Économie & chantier" },
  // W13: «Atelier · global» — surfaces multi-projet/org-level, accessibles depuis
  // n'importe quel projet sans bouger la sélection courante.
  { id: "atelier", lb: "Atelier · multi-projet", ico: "ic-portfolio", grp: "Atelier · global" },
  { id: "equipe", lb: "Équipe", ico: "ic-claims", grp: "Atelier · global" },
];
const GROUPS = ["Pilotage", "Coordination", "Dossier réglementaire", "Économie & chantier", "Atelier · global"];

const TRUST: Record<string, [string, string]> = {
  sourced: ["is-sourced", "Source officielle"], computed: ["is-computed", "Calculé"],
  assumption: ["is-assume", "Hypothèse"], unknown: ["is-unknown", "À vérifier"],
  conflict: ["is-conflict", "Conflit"], present: ["is-sourced", "Fourni"], missing: ["is-assume", "Manquant"],
  satisfied: ["is-sourced", "Satisfait"], action_required: ["is-assume", "Action requise"], decision: ["is-decision", "Décision"],
};
function Trust({ state, label }: { state: string; label?: string }) {
  const [c, l] = TRUST[state] || ["is-unknown", state];
  return <span className={`ds-ts ${c}`}><span className="dot" />{label || l}</span>;
}
const EVENT: Record<string, string> = { adapter_dry_run: "Aperçu", approval: "Validation", adapter_execution: "Modification", decision: "Décision", brief: "Brief" };
function human(e: any): string {
  if (e.event_type === "adapter_dry_run") return "Aperçu d'une modification préparé — aucune mutation.";
  if (e.event_type === "approval") return "Exécution validée par l'architecte.";
  if (e.event_type === "adapter_execution") return "Modification appliquée à la maquette — réversible.";
  return e.summary;
}
const FR: Record<string, string> = {
  architect: "Architecte", architect_or_surveyor: "Architecte / géomètre", specialist: "Spécialiste",
  architect_or_specialist: "Architecte / spécialiste", aedifica: "Aedifica", platform: "Plateforme", plans: "Plans",
  parcel: "Parcelle", project: "Projet", compliance: "Conformité", special_authorizations: "Autorisations spéciales",
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
const fr = (s?: string) => (!s ? s || "" : FR[s] ?? FR[s.toLowerCase()] ?? s);
const LVL: Record<string, string> = { faible: "faible", "modéré": "modere", modere: "modere", moyen: "modere", "élevé": "eleve", eleve: "eleve", low: "faible", medium: "modere", high: "eleve" };
const lvlClass = (s?: string) => LVL[(s || "").toLowerCase()] || "modere";

// ---- parcel search parsing (home → project) ----
const COMMUNE_CANTON: Record<string, string> = {
  lausanne: "VD", pully: "VD", renens: "VD", morges: "VD", nyon: "VD", "yverdon-les-bains": "VD", montreux: "VD", vevey: "VD", "préverenges": "VD",
  fontainemelon: "NE", "neuchâtel": "NE", neuchatel: "NE", "val-de-ruz": "NE", "la chaux-de-fonds": "NE", "le locle": "NE",
  "genève": "GE", geneve: "GE", carouge: "GE", lancy: "GE", fribourg: "FR", bulle: "FR", sion: "VS", sierre: "VS", monthey: "VS",
  bern: "BE", berne: "BE", thun: "BE", "zürich": "ZH", zurich: "ZH", winterthur: "ZH",
};
const noAccent = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "");
// W13: parseParcel / projIdFrom / isReferenceParcel removed with the Home page —
// they were only consumed by the parcel-search shortcut that lived on Home.
// The same flow now lives inside Terrain & zonage on each project.

// W11 P0: ALL icons come from the official Datum sprite (web/public/assets/functional-icons.svg).
// The DS rule is one proprietary sprite, no external icon library; 24px grid, 1.5 stroke, currentColor.
// `n` is the symbol id minus the `ic-` prefix (backwards-compatibility) or the full id.
function Icon({ n }: { n: string }) {
  const id = n.startsWith("ic-") ? n : `ic-${n}`;
  return (
    <svg className="i" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <use href={`/assets/functional-icons.svg#${id}`} />
    </svg>
  );
}

// W11 P1: official ÆDIFICA wordmark — same geometry as the DS spec (viewBox 480×150)
// but rendered INLINE as JSX so the page's @font-face Space Grotesk applies. An
// <img src=".svg"> would isolate the SVG from page fonts and fall back to the browser
// default — that's why it was rendering in a wrong serif before. 300 weight on
// DIFICA, 400 on the Æ ligature, 2px datum rule stepping up at x=300.
const WORDMARK_FONT = '"Space Grotesk", Helvetica, Arial, sans-serif';
const MONO_FONT_FAMILY = '"IBM Plex Mono", ui-monospace, monospace';
function Wordmark({ height = 32, dark = false }: { height?: number; dark?: boolean }) {
  const W = 480, H = 150;
  const width = Math.round(height * (W / H));
  const ink = dark ? "#F3F1EC" : "#16171A";
  const mute = dark ? "#908E85" : "#87867D";
  return (
    <svg width={width} height={height} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="ÆDIFICA"
         style={{ display: "inline-block", verticalAlign: "middle" }}>
      <text x={452} y={36} textAnchor="end" fontFamily={MONO_FONT_FAMILY} fontSize={11} letterSpacing={1.6} fill={mute}>DATUM +13.50</text>
      <text x={26} y={92} fontFamily={WORDMARK_FONT} fontSize={68} fontWeight={300} letterSpacing={2} fill={ink}>
        <tspan fontWeight={400}>Æ</tspan>DIFICA
      </text>
      <path d="M26 112 H300 V106 H454" fill="none" stroke="#C0392B" strokeWidth={2} />
    </svg>
  );
}

// The compact Æ monogram — INLINE for the same font reason. Used in narrow chrome
// (avatar slot, signature corner). NOT used next to the wordmark.
function Monogram({ size = 32, dark = false }: { size?: number; dark?: boolean }) {
  const ink = dark ? "#F3F1EC" : "#16171A";
  const bg = dark ? "#16171A" : "transparent";
  const rule = dark ? "rgba(243,241,236,0.22)" : "rgba(22,23,26,0.18)";
  return (
    <svg width={size} height={size} viewBox="0 0 160 160" role="img" aria-label="Æ"
         style={{ display: "inline-block", verticalAlign: "middle" }}>
      <rect width={160} height={160} fill={bg} />
      <line x1={28} y1={44} x2={132} y2={44} stroke={rule} strokeWidth={1} />
      <text x={80} y={108} textAnchor="middle" fontFamily={WORDMARK_FONT} fontSize={98} fontWeight={400} fill={ink}>Æ</text>
      <path d="M28 128 H92 V122 H132" fill="none" stroke="#C0392B" strokeWidth={2} />
      <text x={132} y={146} textAnchor="end" fontFamily={MONO_FONT_FAMILY} fontSize={9} letterSpacing={1.5} fill={dark ? "#908E85" : "#87867D"}>+13.50</text>
    </svg>
  );
}

type Project = { project_id: string; name: string; phase_code: string; jurisdiction: { commune: string; canton: string; country: string }; claims: number; ledger_entries: number; reports: number };

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
  const [flash, setFlash] = useState<{ kind: "ok" | "warn"; text: string } | null>(null);
  const [users, setUsers] = useState<any[] | null>(null);
  const [atelier, setAtelier] = useState<any>(null);
  const [atelierAlerts, setAtelierAlerts] = useState<any[]>([]);
  // W10: external (client / mandataire) user state. When set, the entire workspace is
  // replaced by the External scoped view.
  const [ext, setExt] = useState<any | null>(null);
  // W11.C → W13: deep-link bridge — Coordination on a project triggers a planning
  // jump that lands on the Atelier multi-project view with this project pre-filtered
  // and the Gantt view active. Consumed (and cleared) by AtelierPilotage on render.
  const [pendingPlanningFilter, setPendingPlanningFilter] = useState<string | null>(null);
  // W13: auto-select the project that was last active in this browser. Falls
  // back to the most recently created (top of the list) if nothing is stored.
  const LAST_PID_KEY = "aedifica_last_pid";

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("aedifica_token") : null;
    if (t) verify(t); else setReady(true);
  }, []);
  async function verify(t: string) {
    // Try the external scope first — if 200, the token belongs to an external user.
    try { const me = await api<any>("/external/me", { token: t }); await loadExternal(t, me); setToken(t); setReady(true); return; } catch { /* not external */ }
    try { await loadProjects(t); await loadUsers(t); loadAtelier(t); setToken(t); }
    catch { localStorage.removeItem("aedifica_token"); } finally { setReady(true); }
  }
  async function loadExternal(t: string, me?: any) {
    const meR = me || await api<any>("/external/me", { token: t });
    const [cl, dx] = await Promise.all([
      api<any>("/external/me/checklist", { token: t }),
      api<any>("/external/me/documents", { token: t }),
    ]);
    setExt({ me: meR, checklist: cl, documents: dx });
  }
  async function tickExternal(id: number, status: string) {
    if (!token) return;
    await api(`/external/me/checklist/${id}`, { method: "PATCH", token: token, body: { status } });
    await loadExternal(token);
  }
  async function acceptInvite(token_: string, password: string, name: string) {
    setBusy(true); setErr("");
    try {
      const r = await api<any>("/auth/accept-invite", { method: "POST", body: { token: token_, password, name } });
      const tk = r.token as string;
      localStorage.setItem("aedifica_token", tk);
      await loadExternal(tk);
      setToken(tk);
    } catch (e: any) { setErr(e.message?.includes("INVITE_INVALID") || e.message?.includes("404") ? "Code d'invitation invalide ou déjà utilisé." : (e.message || "Activation impossible.")); }
    finally { setBusy(false); }
  }
  async function loadAtelier(t: string) {
    try {
      const r = await api<any>("/atelier/tasks", { token: t });
      setAtelier(r);
      try { const al = await api<any>("/atelier/alerts", { token: t }); setAtelierAlerts(al.alerts || []); }
      catch { setAtelierAlerts([]); }
    } catch { setAtelier(null); setAtelierAlerts([]); }
  }
  // W11.C: cross-project handlers for the multi-project Kanban+Gantt drag actions.
  // The PATCH is routed to the right project's task endpoint, then atelier tasks
  // are refreshed so collisions/load follow.
  async function patchAtelierTask(pid: string, tid: number, body: any) {
    await api(`/projects/${pid}/tasks/${tid}`, { method: "PATCH", token: token!, body });
    await loadAtelier(token!);
    if (active && active.project_id === pid) await refreshTasks();
  }
  async function delAtelierTask(pid: string, tid: number) {
    await api(`/projects/${pid}/tasks/${tid}`, { method: "DELETE", token: token! });
    await loadAtelier(token!);
    if (active && active.project_id === pid) await refreshTasks();
  }
  // W13: Coordination → Planning Atelier deep-link. Switches to the multi-project
  // `atelier` view with this project pre-filtered, WITHOUT dropping the active
  // project (the user comes back to the same project context afterwards).
  function openAtelierPlanning(pid: string) {
    setPendingPlanningFilter(pid);
    setView("atelier");
  }
  async function loadProjects(t: string): Promise<Project[]> {
    const ids = (await api<any>("/projects", { token: t })).projects as string[];
    const sums = await Promise.all(ids.map((id) => api<any>(`/projects/${id}`, { token: t }).then((r) => r.project as Project)));
    setProjects(sums); return sums;
  }
  async function loadUsers(t: string) { try { setUsers((await api<any>("/orgs/users", { token: t })).users); } catch { setUsers(null); } }
  async function bootstrap(): Promise<string> {
    const t = (await api<any>("/orgs", { method: "POST", body: { org_name: "Atelier démo", user_email: "demo@aedifica.ch" } })).token;
    localStorage.setItem("aedifica_token", t); setToken(t); return t;
  }
  async function seedReference(t: string) {
    try { await api("/projects", { method: "POST", token: t, body: { project_id: REF_ID, name: REF.name, commune: REF.commune, seed_reports: true } }); } catch { /* exists */ }
    try { const c = ((await api<any>(`/projects/${REF_ID}/claims`, { token: t })).claims) || []; if (!c.length) await api(`/projects/${REF_ID}/intake`, { method: "POST", token: t, body: { query: `${REF.name}, ${REF.commune}`, live: false } }); } catch { /* */ }
  }
  async function register(orgName: string, email: string, password: string) {
    setBusy(true); setErr("");
    try { const t = (await api<any>("/orgs", { method: "POST", body: { org_name: orgName, user_email: email, password } })).token as string;
      localStorage.setItem("aedifica_token", t); await seedReference(t); await loadProjects(t); await loadUsers(t); loadAtelier(t); setToken(t);
    } catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  }
  async function login(email: string, password: string) {
    setBusy(true); setErr("");
    try { const r = await api<any>("/auth/login", { method: "POST", body: { email, password } });
      const t = r.token as string; localStorage.setItem("aedifica_token", t);
      if (r.role === "external") { await loadExternal(t); setToken(t); }
      else { await loadProjects(t); await loadUsers(t); loadAtelier(t); setToken(t); }
    } catch (e: any) { setErr(e.message?.includes("incorrect") ? "E-mail ou mot de passe incorrect." : (e.message || "Connexion impossible.")); } finally { setBusy(false); }
  }
  async function joinWithKey(key: string) {
    setBusy(true); setErr("");
    try { await loadProjects(key); await loadUsers(key); localStorage.setItem("aedifica_token", key); setToken(key); }
    catch { setErr("Clé d'invitation invalide."); } finally { setBusy(false); }
  }
  function signOut() { localStorage.removeItem("aedifica_token"); setToken(null); setProjects(null); setActive(null); setD({}); setFlashKey(null); setFlash(null); setUsers(null); setExt(null); }

  async function createProject(name: string, commune: string) {
    const id = (name.trim().toUpperCase().replace(/[^A-Z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40)) || `PROJ-${(projects?.length ?? 0) + 1}`;
    setBusy(true); setErr("");
    try { await api("/projects", { method: "POST", token: token!, body: { project_id: id, name, commune } }); const sums = await loadProjects(token!); const p = sums.find((s) => s.project_id === id); if (p) await openProject(p); }
    catch (e: any) { setErr(e.message?.includes("exists") ? "Un projet porte déjà ce nom." : e.message); } finally { setBusy(false); }
  }
  async function openProject(p: Project) {
    setActive(p);
    // W13: keep the current view if it's project-agnostic (Atelier / Équipe);
    // otherwise land on the Dashboard for the freshly-opened project.
    setView((v) => (PROJECT_AGNOSTIC.includes(v) ? v : "dashboard"));
    setD({}); setFlashKey(null); setFlash(null);
    try { localStorage.setItem(LAST_PID_KEY, p.project_id); } catch {}
    try { await loadAll(p, token!); } catch (e: any) { setErr(e.message); }
  }
  // W13: pick an initial active project once the project list lands. Prefer
  // the last-active id from localStorage, fall back to the first (most recent).
  useEffect(() => {
    if (!token || !projects || active) return;
    let last: string | null = null;
    try { last = localStorage.getItem(LAST_PID_KEY); } catch {}
    const pick = (last && projects.find((p) => p.project_id === last)) || projects[0];
    if (pick) { openProject(pick); }
  /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [token, projects]);
  async function loadAll(p: Project, t: string) {
    const pid = p.project_id; const g = (path: string) => api<any>(`/projects/${pid}${path}`, { token: t });
    const sup = api<any>(`/communes/${p.jurisdiction.commune}/${p.jurisdiction.canton}/support`, { token: t }).then((r) => r.support).catch(() => null);
    const [claims, permit, opposition, compliance, cost, site, ledger, next, unknowns, support, interv, docs, checklist, brs, toval, tasks, captures, coord] = await Promise.all([
      g("/claims"), g("/permit"), g("/opposition"), g("/compliance"), g("/cost"), g("/site"), g("/ledger"), g("/next-step"), g("/memory/unknowns"), sup, g("/intervenants"), g("/documents"), g("/checklist"), g("/brs"), g("/to-validate"), g("/tasks"), g("/captures"), g("/coordination").catch(() => null),
    ]);
    setD({ claims: claims.claims, permit: permit.permit, opposition: opposition.opposition, compliance: compliance.compliance, cost: cost.cost, site: site.site, ledger: ledger.ledger, next: next.steps, nextStep: next, unknowns: unknowns.unknowns, support, intervenants: interv, documents: docs.documents, docSummary: docs.summary, checklist, brs, toValidate: toval, tasks, captures, coord });
  }
  async function refreshCoord() { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/coordination`, { token: token! }); setD((x) => ({ ...x, coord: r })); }
  async function inviteIntervenant(id: number, email: string, name: string | null) { const r = await api2(`/intervenants/${id}/invite`, { email, name }); await refreshInterv(); return r; }
  // W11 P0: switch the project to a different SIA sub-phase from the top phase rail.
  // Re-fetches the summary so subsequent loadAll/coordination reflect the new phase.
  async function setProjectPhase(code: string) {
    if (!active) return;
    const r = await api<any>(`/projects/${active.project_id}`, { method: "PATCH", token: token!, body: { phase_code: code } });
    const p = r.project as Project;
    setActive(p);
    setProjects((xs) => (xs ? xs.map((q) => (q.project_id === p.project_id ? p : q)) : xs));
    await loadAll(p, token!);
    setFlash({ kind: "ok", text: `Projet basculé en phase ${code} · ${SIA_PHASE_FR[code] || code}` });
  }
  async function refreshCaptures() { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/captures`, { token: token! }); setD((x) => ({ ...x, captures: r })); }
  async function addCapture(b: any) { await api2("/captures", b); await refreshCaptures(); }
  async function delCapture(id: number) { await api2(`/captures/${id}`, undefined, "DELETE"); await refreshCaptures(); }
  async function refreshTasks() { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/tasks`, { token: token! }); setD((x) => ({ ...x, tasks: r })); }
  async function addTask(b: any) { await api2("/tasks", b); await refreshTasks(); }
  async function patchTask(id: number, b: any) { await api2(`/tasks/${id}`, b, "PATCH"); await refreshTasks(); }
  async function delTask(id: number) { await api2(`/tasks/${id}`, undefined, "DELETE"); await refreshTasks(); }
  async function addDep(id: number, blocked_by_id: number) { await api2(`/tasks/${id}/deps`, { blocked_by_id }); await refreshTasks(); }
  async function delDep(id: number, bid: number) { await api2(`/tasks/${id}/deps/${bid}`, undefined, "DELETE"); await refreshTasks(); }
  async function predictTask(id: number) { return api2(`/tasks/${id}/predict`); }
  async function feeEstimate(b: any) { return api2("/fee-estimate", b); }
  async function refreshInterv() { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/intervenants`, { token: token! }); setD((x) => ({ ...x, intervenants: r })); }
  async function refreshDocs() { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/documents`, { token: token! }); setD((x) => ({ ...x, documents: r.documents, docSummary: r.summary })); await refreshToVal(); }
  async function refreshChecklist() { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/checklist`, { token: token! }); setD((x) => ({ ...x, checklist: r })); await refreshToVal(); }
  async function refreshBrs() { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/brs`, { token: token! }); setD((x) => ({ ...x, brs: r })); }
  async function refreshToVal() { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/to-validate`, { token: token! }); setD((x) => ({ ...x, toValidate: r })); }
  async function api2(path: string, body?: any, method = "POST") { return api<any>(`/projects/${active!.project_id}${path}`, { method, token: token!, body }); }
  async function seedChecklist(entry_phase: string) { await api2("/checklist/seed", { entry_phase }); await refreshChecklist(); }
  async function patchChecklist(id: number, status: string) { await api2(`/checklist/${id}`, { status }, "PATCH"); await refreshChecklist(); }
  async function addChecklistItem(b: any) { await api2("/checklist", b); await refreshChecklist(); }
  async function delChecklistItem(id: number) { await api2(`/checklist/${id}`, undefined, "DELETE"); await refreshChecklist(); }
  async function addBrs(b: any) { await api2("/brs", b); await refreshBrs(); }
  async function patchBrs(id: number, b: any) { await api2(`/brs/${id}`, b, "PATCH"); await refreshBrs(); }
  async function delBrs(id: number) { await api2(`/brs/${id}`, undefined, "DELETE"); await refreshBrs(); }
  async function addGrant(docId: number, b: any) { await api2(`/documents/${docId}/grants`, b); await refreshDocs(); }
  async function revokeGrant(docId: number, gid: number) { await api2(`/documents/${docId}/grants/${gid}`, undefined, "DELETE"); await refreshDocs(); }
  async function addGroup(name: string, kind: string) { await api2("/intervenant-groups", { name, kind }); await refreshInterv(); }
  async function delGroup(id: number) { await api2(`/intervenant-groups/${id}`, undefined, "DELETE"); await refreshInterv(); }
  async function addIntervenant(b: any) { await api2("/intervenants", b); await refreshInterv(); }
  async function patchIntervenant(id: number, b: any) { await api2(`/intervenants/${id}`, b, "PATCH"); await refreshInterv(); }
  async function delIntervenant(id: number) { await api2(`/intervenants/${id}`, undefined, "DELETE"); await refreshInterv(); }
  async function addDocument(b: any) { await api2("/documents", b); await refreshDocs(); }
  async function validateDocument(id: number, level: string) { await api2(`/documents/${id}/validate`, { level }); await refreshDocs(); }
  async function patchDocument(id: number, b: any) { await api2(`/documents/${id}`, b, "PATCH"); await refreshDocs(); }
  async function delDocument(id: number) { await api2(`/documents/${id}`, undefined, "DELETE"); await refreshDocs(); }
  async function refreshLedger() { if (!active) return; const [ledger, unknowns] = await Promise.all([api<any>(`/projects/${active.project_id}/ledger`, { token: token! }), api<any>(`/projects/${active.project_id}/memory/unknowns`, { token: token! })]); setD((x) => ({ ...x, ledger: ledger.ledger, unknowns: unknowns.unknowns })); }
  async function lookup(query: string) {
    if (!active) return;
    if (d.support && d.support.usable === false) {
      setFlash({ kind: "warn", text: `Commune ${active.jurisdiction.commune} pas encore prise en charge — aucune donnée inventée. Utilisez « Demander l'ingestion ».` });
      return;
    }
    const r = await api<any>(`/projects/${active.project_id}/intake`, { method: "POST", token: token!, body: { query, live: true } });
    await loadAll(active, token!);
    setD((x) => ({ ...x, intakeMode: r.mode }));
  }
  // W11 P0: ingestion request gets explicit success/failure feedback.
  // The endpoint returns the queued pack; show the user it's been registered.
  async function requestCommune() {
    if (!active) return;
    try {
      const r = await api<any>("/communes", { method: "POST", token: token!, body: { commune: active.jurisdiction.commune, canton: active.jurisdiction.canton } });
      await loadAll(active, token!);
      const status = r?.pack?.status || r?.status || "queued";
      setFlash({ kind: "ok", text: `Demande d'ingestion enregistrée pour ${active.jurisdiction.commune} (${active.jurisdiction.canton}) — statut : ${status}. Le pack apparaîtra sur le tableau atelier dès qu'il sera produit.` });
    } catch (e: any) {
      setFlash({ kind: "warn", text: `Échec de la demande d'ingestion : ${e?.message || "erreur inconnue"}. Réessayez ou contactez l'opérateur.` });
    }
  }
  async function submitPermit(itemId: string, present: boolean) { if (!active) return; const r = await api<any>(`/projects/${active.project_id}/permit/dossier`, { method: "POST", token: token!, body: { item_id: itemId, present } }); setD((x) => ({ ...x, permit: r.permit })); }
  async function addUser(email: string, name: string, role: string): Promise<string> { const r = await api<any>("/orgs/users", { method: "POST", token: token!, body: { email, name, role } }); await loadUsers(token!); return r.token; }
  async function setUserRole(id: number, role: string) { await api(`/orgs/users/${id}`, { method: "PATCH", token: token!, body: { role } }); await loadUsers(token!); }

  // W13: the home parcel-search shortcut is gone — same flow now lives inside
  // Terrain & zonage on each project, which avoids the duplicate search box
  // on the intermediate Home page (now removed entirely).

  if (!ready) return <div className="center"><span className="spin">Chargement…</span></div>;
  if (!token) return <Login busy={busy} err={err} onRegister={register} onLogin={login} onJoin={joinWithKey} onAcceptInvite={acceptInvite} />;
  if (ext) return <ExternalView ext={ext} onTick={tickExternal} onSignOut={signOut} />;

  // W13: single unified shell — no more intermediate Home page. The sidebar
  // hosts a ProjectSwitcher (replaces the old static .psw card + the
  // "Tous les projets" back button) and always shows the "Atelier · global"
  // group so multi-projet planning + équipe stay one click away from any
  // project context.
  const cur = NAV.find((n) => n.id === view) || NAV[0];
  const projectAgnostic = PROJECT_AGNOSTIC.includes(view);
  const j = active?.jurisdiction;
  const curIdx = active ? phaseIndex(active.phase_code) : -1;
  // Empty-state when an architect has zero projects. The switcher's inline
  // create form lives in the sidebar; here we just say "you can also create
  // your first project from the switcher above".
  const noProjects = (projects || []).length === 0;
  // When the active project's data is still loading, only the agnostic views
  // (atelier, equipe) can render meaningfully — everything else needs `d.*`.
  const projectViewBlocked = !projectAgnostic && (!active || !d || Object.keys(d).length === 0);

  return (
    <div className="ws">
      <aside className="ws__side">
        <div className="ws__brand" style={{ display: "flex", alignItems: "center", padding: "4px 0" }}>
          <Wordmark height={48} />
        </div>
        <ProjectSwitcher active={active} projects={projects} onOpen={openProject} onCreate={createProject} busy={busy} />
        <nav className="tnav">
          {GROUPS.map((grp) => (
            <div key={grp}>
              <div className="grp">{grp}</div>
              {NAV.filter((n) => n.grp === grp).map((n) => {
                // W13: per-project surfaces are disabled until a project is
                // selected. Atelier · global stays clickable.
                const disabled = !active && !PROJECT_AGNOSTIC.includes(n.id);
                return (
                  <button key={n.id}
                          className={`titem ${view === n.id ? "on" : ""}`}
                          disabled={disabled}
                          title={disabled ? "Sélectionnez un projet" : undefined}
                          style={disabled ? { opacity: 0.4, cursor: "not-allowed" } : undefined}
                          onClick={() => { if (!disabled) { setView(n.id); setFlash(null); } }}>
                    <Icon n={n.ico} /><span className="lb">{n.lb}</span>{n.ph && <span className="ph">{n.ph}</span>}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
        <div className="ws__sfoot"><span className="d" /><button className="signout" onClick={signOut}>Se déconnecter</button></div>
      </aside>

      <main className="ws__main">
        {active && (
          <div className="phaserail">
            <div className="cap">
              <span className="t">Parcours SIA du projet</span>
              {curIdx >= 0
                ? <span className="now">● {phaseLabel(active.phase_code)}</span>
                : <span className="now" style={{ color: "var(--mut)" }}>○ Phase à cadrer — cliquez une phase pour démarrer</span>}
              {curIdx >= 0 && COST_PRECISION[norm(active.phase_code)] && <span className="chip">Précision coût {COST_PRECISION[norm(active.phase_code)]}</span>}
              {d.intervenants && (d.intervenants.people || []).length > 0 && <span className="chip">{(d.intervenants.people || []).length} intervenant·e·s</span>}
            </div>
            <div className="phases">
              {PHASES.map(([code, lb], i) => {
                const isDone = curIdx >= 0 && i < curIdx;
                const isNow = curIdx >= 0 && i === curIdx;
                return (
                  <button key={code} className={`phase ${isDone ? "done" : ""} ${isNow ? "now" : ""}`}
                          title={`Basculer le projet en ${SIA_PHASE_FR[code] || ("Phase " + code)}`}
                          onClick={() => setProjectPhase(code).catch((e: any) => setErr(e?.message || "Échec du changement de phase"))}>
                    <span className="pt">{isDone ? "✓" : code}</span><span className="pl">{code} {lb}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}
        <div className="ws__top">
          <span className="t-nm">{cur.lb}</span>
          {j && <span className="chip">{j.commune}</span>}
          <span className="sp" />
          <span className="chip">L&apos;IA propose — l&apos;architecte décide</span>
        </div>
        <div className="ws__view">
          {flash && <div className={`banner ${flash.kind}`} style={{ display: "flex", alignItems: "center", gap: 12 }}><span style={{ flex: 1 }}>{flash.text}</span><button className="toggle" onClick={() => setFlash(null)}>Compris</button></div>}
          {flashKey && (
            <div className="banner" style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ flex: 1 }}><b>Atelier créé.</b> Conservez votre clé d&apos;accès pour vous reconnecter : <code>{flashKey}</code></span>
              <button className="toggle" onClick={() => setFlashKey(null)}>J&apos;ai noté ma clé</button>
            </div>
          )}

          {/* Project-agnostic views (always renderable). */}
          {view === "atelier" && (
            atelier ? <AtelierPilotage atelier={atelier} onOpen={openProject} projects={projects}
                                       pendingFilter={pendingPlanningFilter}
                                       onClearPending={() => setPendingPlanningFilter(null)}
                                       onPatchTask={patchAtelierTask} onDelTask={delAtelierTask} />
                    : <p className="spin">Chargement de l&apos;atelier…</p>
          )}
          {view === "equipe" && <Team users={users} onAdd={addUser} onSetRole={setUserRole} />}

          {/* Empty-state when no project exists at all. */}
          {!active && noProjects && !projectAgnostic && (
            <div className="placeholder" style={{ maxWidth: 560, margin: "32px auto" }}>
              <h4>Créer votre premier projet</h4>
              <p>Ouvrez le sélecteur de projet en haut de la barre latérale et choisissez <b>+ Nouveau projet</b>. La parcelle, les contraintes, et la feuille SIA sont seedées à la création.</p>
            </div>
          )}

          {/* Project-required views — blocked until a project is loaded. */}
          {!projectAgnostic && projectViewBlocked && active && (
            <p className="spin">Chargement du projet {active.name}…</p>
          )}

          {!projectAgnostic && !projectViewBlocked && active && (
            <>
              {view === "dashboard" && <Dashboard d={d} project={active} go={setView} alerts={atelierAlerts} onOpenAtelierPlanning={openAtelierPlanning} />}
              {view === "taches" && <Taches data={d.tasks} token={token!} pid={active.project_id} onAdd={addTask} onPatch={patchTask} onDel={delTask} onAddDep={addDep} onDelDep={delDep} onPredict={predictTask} />}
              {view === "checklist" && <Checklist data={d.checklist} entryPhase={active.phase_code} token={token!} pid={active.project_id} onSeed={seedChecklist} onPatch={patchChecklist} onAdd={addChecklistItem} onDel={delChecklistItem} />}
              {view === "terrain" && <Terrain claims={d.claims} mode={d.intakeMode} support={d.support} commune={active.jurisdiction.commune} initialQuery={d.pendingQuery} regAlerts={d.captures?.regulation_alerts} onLookup={lookup} onRequest={requestCommune} />}
              {view === "coordination" && <Coordination data={d.coord} onRefresh={refreshCoord} go={setView} projectId={active.project_id} onOpenAtelierPlanning={openAtelierPlanning} />}
              {view === "intervenants" && <Intervenants data={d.intervenants} token={token!} projectId={active.project_id} onAddGroup={addGroup} onDelGroup={delGroup} onAdd={addIntervenant} onPatch={patchIntervenant} onDel={delIntervenant} onInvite={inviteIntervenant} />}
              {view === "documents" && <Documents docs={d.documents} summary={d.docSummary} intervenants={d.intervenants} token={token!} pid={active.project_id} onAdd={addDocument} onRefresh={refreshDocs} onValidate={validateDocument} onPatch={patchDocument} onDel={delDocument} onGrant={addGrant} onRevoke={revokeGrant} />}
              {view === "brs" && <Brs data={d.brs} intervenants={d.intervenants} token={token!} pid={active.project_id} onAdd={addBrs} onPatch={patchBrs} onDel={delBrs} />}
              {view === "permis" && <Permis d={d.permit} onSubmit={submitPermit} tasks={d.tasks?.tasks || []} projectId={active.project_id} token={token!} onOpenAtelierPlanning={openAtelierPlanning} />}
              {view === "opposition" && <Opposition d={d.opposition} canonicalDocs={(d.documents || []).filter((x: any) => x.validation_level === "canonical").length} />}
              {view === "conformite" && <Conformite d={d.compliance} tasks={d.tasks?.tasks || []} projectId={active.project_id} token={token!} onOpenAtelierPlanning={openAtelierPlanning} />}
              {view === "copilote" && <Copilote token={token} pid={active.project_id} ledger={d.ledger} onChange={refreshLedger} />}
              {view === "memoire" && <Memoire unknowns={d.unknowns} ledger={d.ledger} captures={d.captures} token={token!} pid={active.project_id} onAddCapture={addCapture} onDelCapture={delCapture} />}
              {view === "couts" && <Couts d={d.cost} onFee={feeEstimate} tasks={d.tasks?.tasks || []} projectPhase={active.phase_code} projectId={active.project_id} onOpenAtelierPlanning={openAtelierPlanning} />}
              {view === "chantier" && <Chantier d={d.site} tasks={d.tasks?.tasks || []} projectId={active.project_id} onOpenAtelierPlanning={openAtelierPlanning} />}
              {view === "foresight" && token && <Foresight token={token} pid={active.project_id} />}
            </>
          )}
          {err && <p className="note err" style={{ marginTop: 16 }}>{err}</p>}
        </div>
      </main>
    </div>
  );
}

/* ===================== LOGIN ===================== */
function Login({ busy, err, onRegister, onLogin, onJoin, onAcceptInvite }: { busy: boolean; err: string; onRegister: (o: string, e: string, p: string) => void; onLogin: (e: string, p: string) => void; onJoin: (k: string) => void; onAcceptInvite: (token: string, password: string, name: string) => void }) {
  const [mode, setMode] = useState<"login" | "register" | "join" | "invite">("login");
  const [org, setOrg] = useState(""); const [email, setEmail] = useState(""); const [pw, setPw] = useState(""); const [key, setKey] = useState("");
  const [invToken, setInvToken] = useState(""); const [invName, setInvName] = useState("");
  const titles: Record<string, string> = { login: "Connexion", register: "Créer un atelier", join: "Rejoindre un atelier", invite: "Activer mon invitation" };
  const canReg = !!org && !!email && pw.length >= 6;
  return (
    <div className="center">
      <div className="login__box">
        <Wordmark height={84} />
        <span className="eyebrow">ArchiOS Suisse · l&apos;assistant de l&apos;architecte</span>
        <h2>{titles[mode]}</h2>
        {mode !== "join" && (
          <div className="seg">
            <button className={mode === "login" ? "on" : ""} onClick={() => setMode("login")}>Se connecter</button>
            <button className={mode === "register" ? "on" : ""} onClick={() => setMode("register")}>Créer un atelier</button>
          </div>
        )}
        {mode === "register" && (
          <>
            <label className="lbl">Nom de l&apos;atelier</label>
            <input className="fld" value={org} onChange={(e) => setOrg(e.target.value)} placeholder="Atelier Martin" />
            <label className="lbl">E-mail</label>
            <input className="fld" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vous@atelier.ch" />
            <label className="lbl">Mot de passe</label>
            <input className="fld" type="password" autoComplete="new-password" value={pw} onChange={(e) => setPw(e.target.value)} onKeyDown={(e) => e.key === "Enter" && canReg && onRegister(org, email, pw)} placeholder="6 caractères minimum" />
            <button className="ds-btn full" disabled={busy || !canReg} onClick={() => onRegister(org, email, pw)}>{busy ? "Création…" : "Créer l'atelier"}</button>
            <p className="note" style={{ marginTop: 12 }}>Un atelier de démonstration (Place de la Palud) sera ajouté pour explorer.</p>
          </>
        )}
        {mode === "login" && (
          <>
            <label className="lbl">E-mail</label>
            <input className="fld" type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="vous@atelier.ch" />
            <label className="lbl">Mot de passe</label>
            <input className="fld" type="password" autoComplete="current-password" value={pw} onChange={(e) => setPw(e.target.value)} onKeyDown={(e) => e.key === "Enter" && email && pw && onLogin(email, pw)} placeholder="votre mot de passe" />
            <button className="ds-btn full" disabled={busy || !email || !pw} onClick={() => onLogin(email, pw)}>{busy ? "Connexion…" : "Se connecter"}</button>
            <p className="login__alt"><a onClick={() => setMode("invite")}>J&apos;ai reçu un code d&apos;invitation</a> · <a onClick={() => setMode("join")}>Clé atelier</a></p>
          </>
        )}
        {mode === "join" && (
          <>
            <label className="lbl">Clé d&apos;invitation</label>
            <input className="fld" value={key} onChange={(e) => setKey(e.target.value)} onKeyDown={(e) => e.key === "Enter" && key && onJoin(key.trim())} placeholder="collez la clé reçue" />
            <button className="ds-btn full" disabled={busy || !key} onClick={() => onJoin(key.trim())}>{busy ? "Connexion…" : "Rejoindre"}</button>
            <p className="login__alt"><a onClick={() => setMode("login")}>← Retour à la connexion</a></p>
          </>
        )}
        {mode === "invite" && (
          <>
            <p className="note" style={{ marginBottom: 12 }}>L&apos;architecte vous a transmis un code d&apos;invitation. Définissez votre mot de passe pour accéder à votre espace.</p>
            <label className="lbl">Code d&apos;invitation</label>
            <input className="fld" value={invToken} onChange={(e) => setInvToken(e.target.value)} placeholder="collez le code reçu" />
            <label className="lbl">Votre nom</label>
            <input className="fld" value={invName} onChange={(e) => setInvName(e.target.value)} placeholder="Prénom Nom" />
            <label className="lbl">Mot de passe</label>
            <input className="fld" type="password" autoComplete="new-password" value={pw} onChange={(e) => setPw(e.target.value)} onKeyDown={(e) => e.key === "Enter" && invToken && pw.length >= 6 && onAcceptInvite(invToken.trim(), pw, invName)} placeholder="6 caractères minimum" />
            <button className="ds-btn full" disabled={busy || !invToken || pw.length < 6} onClick={() => onAcceptInvite(invToken.trim(), pw, invName)}>{busy ? "…" : "Activer mon accès"}</button>
            <p className="login__alt"><a onClick={() => setMode("login")}>← Retour à la connexion</a></p>
          </>
        )}
        {err && <p className="note err" style={{ marginTop: 12 }}>{err}</p>}
      </div>
    </div>
  );
}

/* ===================== HOME ===================== */
/* ===================== ATELIER · PILOTAGE MULTI-PROJET (W9 #225/#227 + W11.C) ===================== */
// W11.C: the multi-project planning surface. Three intentional views over the
// SAME pool of atelier tasks: List (priorities, the original W9 view), Kanban
// (drag-and-drop by status), Gantt (timeline + collisions). A project filter
// lets the user focus on one project's tasks while keeping the collision
// detector at the atelier scope. Bridged from per-project Coordination via the
// `pendingFilter` prop (clicked from a project, lands here pre-filtered).
function AtelierPilotage({ atelier, onOpen, projects, pendingFilter, onClearPending, onPatchTask, onDelTask }: any) {
  const allTasks: any[] = atelier.tasks || [];
  const projectIds = Array.from(new Set(allTasks.map((t) => t.project_id)));
  const [filter, setFilter] = useState<string>("");
  useEffect(() => { if (pendingFilter) { setFilter(pendingFilter); onClearPending?.(); } }, [pendingFilter, onClearPending]);
  const [view, setView] = useState<"list" | "kanban" | "gantt">(pendingFilter ? "gantt" : "list");
  const scoped = filter ? allTasks.filter((t) => t.project_id === filter) : allTasks;
  const open: any[] = scoped.filter((t: any) => t.status !== "done");
  const col = atelier.collision || {}; const load = atelier.load_by_assignee || {};
  const top = [...open].sort((a, b) => (a.priority > b.priority ? 1 : a.priority < b.priority ? -1 : 0)).slice(0, 6);
  const openProj = (pid: string) => { const p = (projects || []).find((x: any) => x.project_id === pid); if (p) onOpen(p); };
  return (
    <div className="home__sec">
      <div className="row" style={{ alignItems: "baseline", gap: 12, flexWrap: "wrap" }}>
        <h2 style={{ margin: 0 }}>Atelier · pilotage multi-projet ({atelier.projects} projet·s)</h2>
        <span className="grow" />
        <label className="mono" style={{ fontSize: 11, color: "var(--mut)", display: "flex", alignItems: "center", gap: 6 }}>
          Projet
          <select className="fld" style={{ margin: 0, padding: "4px 8px", width: "auto" }} value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="">Tous ({allTasks.length})</option>
            {projectIds.map((pid) => {
              const t0 = allTasks.find((t) => t.project_id === pid);
              return <option key={pid} value={pid}>{t0?.project_name || pid} ({allTasks.filter((t) => t.project_id === pid).length})</option>;
            })}
          </select>
        </label>
        <span className="row" style={{ gap: 4 }}>
          {([["list","Liste"],["kanban","Kanban"],["gantt","Gantt"]] as const).map(([v, lb]) => (
            <button key={v} className={`toggle ${view === v ? "on" : ""}`} onClick={() => setView(v)}>{lb}</button>
          ))}
        </span>
      </div>
      {(col.overloaded || []).length > 0 && <div className="banner bad" style={{ marginTop: 10, marginBottom: 12 }}><b>Collision de charge</b> — {col.overloaded.map((o: any) => `${o.week} : ${o.hours} h (+${o.over})`).join(" · ")} au-delà de {col.weekly_capacity} h/sem.</div>}

      {view === "list" && (
        <div className="g2" style={{ marginTop: 12 }}>
          <div className="card"><h3>Tâches prioritaires{filter ? "" : " (tous projets)"}</h3>{top.length === 0 && <p className="spin">Aucune tâche ouverte.</p>}{top.map((t: any) => { const [pc, pl] = PRIO[t.priority] || ["modere", t.priority]; return (
            <div className="row-line" key={`${t.project_id}-${t.id}`}><span className={`lvl ${pc}`}>{pl}</span><span className="grow"><span className="ttl">{t.title}{t.is_blocked && <small style={{ display: "inline", color: "var(--ts-conflict)" }}> · bloquée</small>}</span><small>{[t.project_name, t.assignee ? "→ " + t.assignee : null, t.estimate_hours ? t.estimate_hours + " h" : null, t.due_date ? "éch. " + t.due_date : null].filter(Boolean).join(" · ")}</small></span><button className="toggle" onClick={() => openProj(t.project_id)}>Ouvrir →</button></div>
          ); })}</div>
          <div className="card"><h3>Charge par collaborateur</h3>{Object.keys(load).length === 0 && <p className="spin">—</p>}{Object.entries(load).map(([n, h]: any) => (<div className="row-line" key={n}><span className="grow"><span className="ttl">{n}</span></span><span className={`lvl ${h > 40 ? "eleve" : h > 20 ? "modere" : "faible"}`}>{h} h</span></div>))}
            {Object.keys(col.by_week || {}).length > 0 && <div style={{ marginTop: 12 }}><div className="mono" style={{ fontSize: 10, margin: "0 0 6px", color: "var(--mut)" }}>CHARGE PAR SEMAINE</div>{Object.entries(col.by_week).map(([w, h]: any) => (<div className="row-line" key={w}><span className="grow"><span className="mono" style={{ fontSize: 12 }}>{w}</span></span><span className={`lvl ${h > col.weekly_capacity ? "eleve" : "faible"}`}>{h} h</span></div>))}</div>}
          </div>
        </div>
      )}

      {view === "kanban" && (
        <div className="card" style={{ marginTop: 12 }}>
          <KanbanView tasks={scoped} onPatch={onPatchTask} onDel={onDelTask} />
        </div>
      )}

      {view === "gantt" && (
        <div className="card" style={{ marginTop: 12 }}>
          <GanttView tasks={scoped} onPatch={onPatchTask} />
        </div>
      )}
    </div>
  );
}

// W13 — Project switcher (replaces the static .psw card). A button that
// opens a popover with the project list (search if many), a checkmark on the
// active one, and an inline "+ Nouveau projet" form at the bottom. Pattern
// borrowed from Notion / Linear / Figma workspace switchers: stay in the
// workspace, never bounce to a separate page.
function ProjectSwitcher({ active, projects, onOpen, onCreate, busy }: {
  active: Project | null; projects: Project[] | null;
  onOpen: (p: Project) => void;
  onCreate: (name: string, commune: string) => Promise<void> | void;
  busy: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [commune, setCommune] = useState("Lausanne");
  const ref = useRef<HTMLDivElement | null>(null);
  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!open) return;
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false); setCreating(false);
      }
    }
    function onKey(e: KeyboardEvent) { if (e.key === "Escape") { setOpen(false); setCreating(false); } }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  }, [open]);

  const list = (projects || []).slice();
  const filtered = q.trim() ? list.filter((p) => `${p.name} ${p.jurisdiction.commune}`.toLowerCase().includes(q.toLowerCase())) : list;
  const create = async () => {
    if (!name.trim()) return;
    await onCreate(name, commune);
    setCreating(false); setName(""); setOpen(false);
  };
  return (
    <div className="psw-wrap" ref={ref}>
      <button className="psw-btn" onClick={() => setOpen(v => !v)} aria-haspopup="listbox" aria-expanded={open}>
        <div className="psw-cur">
          <div className="k">Projet</div>
          {active
            ? <>
                <div className="nm">{active.name}</div>
                <div className="me">{active.jurisdiction.commune} · {active.jurisdiction.canton} · {phaseLabel(active.phase_code)}</div>
              </>
            : <>
                <div className="nm" style={{ color: "var(--mut)" }}>Aucun projet</div>
                <div className="me">Créez-en un ↓</div>
              </>}
        </div>
        <span className="psw-caret" aria-hidden="true">▾</span>
      </button>
      {open && (
        <div className="psw-pop" role="listbox">
          {list.length > 5 && (
            <input className="fld psw-search" placeholder="Filtrer…" value={q} onChange={(e) => setQ(e.target.value)} autoFocus />
          )}
          <div className="psw-list">
            {filtered.length === 0 && <div className="psw-empty">Aucun projet ne correspond.</div>}
            {filtered.map((p) => {
              const isActive = active && active.project_id === p.project_id;
              return (
                <button key={p.project_id} className={`psw-item ${isActive ? "on" : ""}`}
                        onClick={() => { onOpen(p); setOpen(false); }}>
                  <div className="psw-item-main">
                    <div className="psw-item-nm">{p.name}</div>
                    <div className="psw-item-me">{p.jurisdiction.commune} · {phaseLabel(p.phase_code)}</div>
                  </div>
                  {isActive && <span className="psw-check" aria-hidden="true">✓</span>}
                </button>
              );
            })}
          </div>
          <div className="psw-sep" />
          {!creating ? (
            <button className="psw-new" onClick={() => setCreating(true)}>+ Nouveau projet</button>
          ) : (
            <div className="psw-form">
              <input className="fld" placeholder="Nom du projet" value={name} onChange={(e) => setName(e.target.value)} autoFocus />
              <input className="fld" placeholder="Commune" value={commune} onChange={(e) => setCommune(e.target.value)} />
              <div className="row" style={{ gap: 6 }}>
                <button className="ds-btn" disabled={busy || !name} onClick={create}>{busy ? "…" : "Créer"}</button>
                <button className="ds-btn ghost" onClick={() => setCreating(false)}>Annuler</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// W13: the Home component is gone. After login the user lands directly in the
// unified workspace. The reference parcel search (was duplicate of Terrain),
// the marketing "Présentation faisabilité" cards, and the standalone project
// grid all disappear — project selection lives in the sidebar's ProjectSwitcher
// and the per-phase guidance lives inside each project's surfaces.

/* ===================== DASHBOARD (phase-aware) ===================== */
function Dashboard({ d, project, go, alerts, onOpenAtelierPlanning }: { d: any; project: Project; go: (v: View) => void; alerts: any[]; onOpenAtelierPlanning: (pid: string) => void }) {
  if (!d.claims) return <p className="spin">Chargement…</p>;
  const sourced = d.claims.filter((c: any) => c.state === "sourced" || c.state === "computed").length;
  const verify = d.claims.filter((c: any) => c.state === "unknown" || c.state === "assumption").length;
  const blockers = d.permit?.summary?.required_blockers ?? 0;
  const opp = d.opposition?.overall ?? "—";
  const mut = (d.ledger || []).filter((e: any) => e.mutating).length;
  return (
    <>
      <div className="vh"><div className="row"><h2>{phaseLabel(project.phase_code)}</h2><span className="badge live"><span className="d" />Opérationnel</span></div>
        {isPhaseUnset(project.phase_code)
          ? <p>Projet à cadrer — basculez en <b>Phase 11 · Définition des objectifs</b> via la barre du haut pour démarrer la séquence SIA. Tant que la phase n&apos;est pas définie, le Prochain pas reste sur les actions d&apos;initialisation.</p>
          : <p>L&apos;état du projet en un coup d&apos;œil : ce qui est fiable, ce qu&apos;il faut traiter ensuite, et les quick-wins de cette phase.</p>}
      </div>
      {(alerts || []).length > 0 && (
        <div className="card" style={{ marginBottom: 14, borderLeft: "3px solid var(--ts-conflict)" }}>
          <div className="row" style={{ alignItems: "baseline" }}>
            <h3 style={{ margin: 0 }}>Alertes Atelier</h3>
            <small style={{ color: "var(--mut)" }}>{(alerts || []).length} alerte{(alerts || []).length > 1 ? "s" : ""} dérivée{(alerts || []).length > 1 ? "s" : ""} du planning (Gantt + collisions)</small>
            <span className="grow" />
            <button className="toggle" onClick={() => onOpenAtelierPlanning(project.project_id)}>Voir le planning Atelier →</button>
          </div>
          <div style={{ marginTop: 8 }}>
            {(alerts || []).slice(0, 6).map((a: any, i: number) => {
              const sev = a.severity === "bad" ? "is-conflict" : a.severity === "warn" ? "is-assume" : "is-computed";
              return (
                <div className="row-line" key={i}>
                  <span className={`ds-ts ${sev}`}><span className="dot" />{a.severity?.toUpperCase()}</span>
                  <span className="grow"><span className="ttl">{a.title}</span><small>{a.detail}</small></span>
                  {a.project_id && a.project_id !== project.project_id && (
                    <button className="toggle" onClick={() => onOpenAtelierPlanning(a.project_id)} title="Ouvrir le planning Atelier filtré sur ce projet">→</button>
                  )}
                </div>
              );
            })}
            {(alerts || []).length > 6 && <small style={{ color: "var(--mut)" }}>+{(alerts || []).length - 6} de plus dans le planning Atelier.</small>}
          </div>
        </div>
      )}
      {d.toValidate && (d.toValidate.counts.documents + d.toValidate.counts.checklist_todo) > 0 && (
        <div className="banner warn" style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <b>À valider</b>
          {d.toValidate.counts.documents > 0 && <button className="toggle" onClick={() => go("documents")}>{d.toValidate.counts.documents} document(s)</button>}
          {d.toValidate.counts.checklist_todo > 0 && <button className="toggle" onClick={() => go("checklist")}>{d.toValidate.counts.checklist_todo} step(s) à faire{d.toValidate.counts.checklist_retroactive_todo > 0 ? ` · ${d.toValidate.counts.checklist_retroactive_todo} rétroactif` : ""}</button>}
        </div>
      )}
      <div className="next">
        <div className="h"><span className="t">Prochain pas</span><button className="toggle" style={{ marginLeft: "auto", padding: "2px 8px", fontSize: 11 }} onClick={() => go("foresight")}>Voir Foresight →</button></div>
        {d.nextStep?.top_pick && (
          <div className="row" style={{ background: "var(--surface-2)", padding: 10, borderRadius: 2, marginBottom: 6 }}>
            <span className="ix" style={{ background: "var(--accent)", color: "var(--surface)" }}>★</span>
            <span>
              <span className="tx">{fr(d.nextStep.top_pick.title)}</span>
              <span className="mt" style={{ display: "block" }}>{d.nextStep.top_pick.rationale || d.nextStep.top_pick.action} · phase {d.nextStep.top_pick.phase} · impact {d.nextStep.top_pick.impact_score}</span>
            </span>
          </div>
        )}
        {(d.next || []).slice(0, 4).map((s: any, i: number) => (
          <div className="row" key={i}><span className="ix">{String(i + 1).padStart(2, "0")}</span>
            <span><span className="tx">{fr(s.title)}</span><span className="mt">{s.rationale || s.action || s.kind} · phase {s.phase}{s.impact_score ? ` · impact ${s.impact_score}` : ""}</span></span></div>
        ))}
        {(d.next || []).length === 0 && <div className="row"><span className="spin">Rien en attente.</span></div>}
      </div>
      <div className="kpis">
        <button className="kpi click" onClick={() => go("terrain")}><div className="lab">Contraintes terrain</div><div className="num">{sourced}<small> / {sourced + verify}</small></div><div className="sub"><span className="d" style={{ background: "var(--ts-assume)" }} />{verify} à vérifier</div></button>
        <button className="kpi click" onClick={() => go("permis")}><div className="lab">Dossier de permis</div><div className="num">{blockers === 0 ? "Prêt" : blockers}</div><div className="sub">{blockers === 0 ? "aucun blocage" : "pièces manquantes"}</div></button>
        <button className="kpi click" onClick={() => go("opposition")}><div className="lab">Risque d&apos;opposition</div><div className="num" style={{ textTransform: "capitalize", fontSize: 24 }}>{opp}</div><div className="sub">score {d.opposition?.score ?? "—"}</div></button>
        <button className="kpi click" onClick={() => go("copilote")}><div className="lab">Actions maquette</div><div className="num">{mut}</div><div className="sub">tracées &amp; réversibles</div></button>
      </div>
      <div className="card"><h3>Activité récente</h3>
        {[...(d.ledger || [])].reverse().slice(0, 5).map((e: any, i: number) => (
          <div className="claim" key={i}><Trust state={e.mutating ? "conflict" : e.event_type === "approval" ? "sourced" : "computed"} label={EVENT[e.event_type] || e.event_type} /><div><div className="ttl">{human(e)}</div></div></div>
        ))}
        {(d.ledger || []).length === 0 && <p className="spin">Aucune action — voir le Copilote.</p>}
      </div>
    </>
  );
}

/* ===================== TERRAIN ===================== */
// W14.A — honest ingestion panel. Replaces the misleading "en queue" banner.
// When a commune is not yet usable, the architect sees:
// - The actual status of the IngestionJob (seed | requested + age in days)
// - The list of REAL inputs that must be captured for the commune to become
//   usable (PGA, RPGA, geoportal layer, in-force date).
// - A truthful explanation that this requires an operator (not a worker).
function IngestionPanel({ commune, support, onRequest }: { commune: string; support: any; onRequest: () => void }) {
  const job = support?.job;
  const required = support?.required_inputs || [];
  const hasJob = !!job;
  return (
    <div className="card" style={{ borderLeft: "3px solid var(--ts-assume)", marginBottom: 14 }}>
      <div className="row" style={{ alignItems: "baseline", gap: 8, flexWrap: "wrap" }}>
        <h3 style={{ margin: 0 }}>Commune <i>{commune}</i> pas encore exploitable</h3>
        <span className="grow" />
        {!hasJob && <button className="ds-btn" onClick={onRequest}>Consigner la demande</button>}
      </div>
      {hasJob ? (
        <p className="note" style={{ marginTop: 8 }}>
          Demande consignée le <b>{(job.requested_at || "").slice(0, 10)}</b>
          {typeof job.age_days === "number" && job.age_days >= 0 ? ` (il y a ${job.age_days} jour${job.age_days > 1 ? "s" : ""})` : ""} —
          statut <b>{job.status}</b>.
        </p>
      ) : (
        <p className="note" style={{ marginTop: 8 }}>
          Aucune demande consignée. En consigner une enregistre l&apos;intention dans l&apos;atelier ; <b>la capture du règlement reste un acte manuel</b>.
        </p>
      )}
      <p style={{ marginTop: 4 }}>
        Aedifica ne fabrique pas de zones. Pour rendre la commune exploitable, un opérateur (vous ou votre équipe) doit capturer ces sources officielles, puis les charger via l&apos;outil d&apos;ingestion :
      </p>
      <ul style={{ margin: "6px 0 0 18px", padding: 0 }}>
        {required.map((s: string, i: number) => (
          <li key={i} style={{ marginBottom: 4 }}><span className="mono" style={{ fontSize: 11 }}>{s}</span></li>
        ))}
      </ul>
      <p className="note" style={{ marginTop: 12, color: "var(--mut)" }}>
        Tant que la commune reste à l&apos;état <i>seed</i>, le Terrain reste honnêtement vide — aucune valeur inventée.
      </p>
    </div>
  );
}

function Terrain({ claims, mode, support, commune, onLookup, onRequest, initialQuery, regAlerts }: any) {
  const [q, setQ] = useState(initialQuery || ""); const [b, setB] = useState("");
  if (!claims) return <p className="spin">Chargement…</p>;
  const lookup = async () => { if (!q.trim()) return; setB("l"); try { await onLookup(q.trim()); } catch { } finally { setB(""); } };
  const usable = support ? support.usable : true;
  return (
    <>
      <div className="vh"><div className="row" style={{ gap: 10, alignItems: "center" }}><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" style={{ color: "var(--ink-60)" }}><use href="/assets/functional-icons.svg#ic-datum-north" /></svg><h2 style={{ margin: 0 }}>Terrain &amp; zonage</h2><span className="badge live"><span className="d" />Opérationnel</span></div><p>Ce que la parcelle autorise — sourcé sur une base officielle, ou marqué « à vérifier ». Le datum géographique du projet : tout part d&apos;ici.</p></div>
      {(regAlerts || []).map((r: any) => <div className="banner bad" key={r.id} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}><svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true" style={{ flex: "0 0 16px", marginTop: 2 }}><use href="/assets/functional-icons.svg#ic-warning" /></svg><div><b>Règlement à l&apos;étude</b> — {r.content}{r.source_ref ? ` (${r.source_ref})` : ""}. Les règles (hauteurs, densités) peuvent changer en cours de projet.</div></div>)}
      {support && !usable && <IngestionPanel commune={commune} support={support} onRequest={onRequest} />}
      <div className="searchrow"><input value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && lookup()} placeholder="Adresse ou parcelle — ex. Place de la Palud, Lausanne" /><button onClick={lookup}>{b ? "…" : "Rechercher (live)"}</button></div>
      {mode === "offline" && <p className="note" style={{ marginBottom: 12 }}>Recherche live indisponible — données de référence affichées.</p>}
      {claims.length === 0 ? (
        <div className="placeholder"><h4>Aucune parcelle analysée</h4><p>Lancez une recherche d&apos;adresse pour résoudre la parcelle.</p></div>
      ) : (
        <div className="card">{claims.map((c: any) => (
          <div className="claim" key={c.claim_id}><Trust state={c.state} /><div><div className="ttl">{c.title}</div><div className="val">{c.value == null ? "Non disponible — à confirmer sur le règlement communal" : String(c.value)}</div></div></div>
        ))}</div>
      )}
    </>
  );
}

/* ===================== PERMIS ===================== */
function Permis({ d, onSubmit, tasks, projectId, token, onOpenAtelierPlanning }: any) {
  const [busy, setBusy] = useState("");
  if (!d) return <p className="spin">Chargement…</p>;
  const toggle = async (id: string, present: boolean) => { setBusy(id); try { await onSubmit(id, present); } catch { } finally { setBusy(""); } };
  return (
    <>
      <div className="vh">
        <h2>Dossier de permis</h2>
        <p>
          Complétude pièce par pièce, par intervenant. Pour chaque pièce : <b>joignez le document réel</b> (lien Drive / OneDrive / SharePoint, ou upload direct), puis marquez-la comme fournie. Le statut « Fournir » seul ne suffit pas — il faut une trace vérifiable.
        </p>
      </div>
      <div className="banner" style={{ borderLeftColor: d.ready_for_review ? "var(--ts-sourced)" : "var(--ts-assume)" }}>
        {d.ready_for_review ? <b>Dossier prêt à déposer.</b> : <><b>Pas encore prêt — {d.summary.required_blockers} pièce(s) requise(s) manquante(s).</b></>}
      </div>
      {d.groups?.map((g: any, i: number) => (
        <div className="card" key={i} style={{ marginBottom: 14 }}>
          <h3>{fr(g.actor)} · {fr(g.category)}</h3>
          {g.items.map((it: any, j: number) => {
            const present = it.status === "present";
            return (
              // W14.B — each dossier piece carries an AttachField. The "Fournir"
              // toggle records the *declared* status; the attached link/upload
              // records the *evidence*. Both live on the same row.
              <div key={j} style={{ borderTop: j === 0 ? "none" : "1px solid var(--line)", paddingTop: j === 0 ? 0 : 12, paddingBottom: 6 }}>
                <div className="row-line" style={{ borderBottom: "none", paddingBottom: 0 }}>
                  <Trust state={it.status} />
                  <span className="grow">
                    <span className="ttl">{fr(it.title)}</span>
                    {it.missing_message && (it.status === "missing" || it.status === "assumption") && <small>{it.missing_message}</small>}
                  </span>
                  <button className={`toggle ${present ? "" : "fill"}`} disabled={busy === it.item_id} onClick={() => toggle(it.item_id, !present)}>
                    {busy === it.item_id ? "…" : present ? "Retirer" : "Fournir"}
                  </button>
                </div>
                {token && projectId && (
                  <div style={{ paddingLeft: 32 }}>
                    <AttachField token={token} projectId={projectId} ownerKind="permit" ownerId={it.item_id} label="Pièce officielle" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}
      <PhaseTasks phase="33" tasks={tasks || []} projectId={projectId} onOpenAtelierPlanning={onOpenAtelierPlanning} label="phase 33 · autorisation / permis" />
    </>
  );
}

/* ===================== OPPOSITION ===================== */
function Opposition({ d, canonicalDocs }: any) {
  if (!d) return <p className="spin">Chargement…</p>;
  // W14.B — honest empty-state: explain WHAT this surface needs to populate,
  // and which surface to go fill first.
  if (!d.overall) return (<>
    <div className="vh">
      <h2>Risque d&apos;opposition</h2>
      <p>
        Évaluation des motifs d&apos;opposition les plus probables, basée sur les <b>faits sourcés du dossier</b> (contraintes parcelle + documents canoniques validés). À utiliser avant l&apos;enquête publique pour cibler ce qu&apos;il faut désamorcer.
      </p>
    </div>
    <div className="card" style={{ borderLeft: "3px solid var(--ts-assume)" }}>
      <h3>Pas encore d&apos;évaluation</h3>
      <p>
        Pour qu&apos;une analyse de risque émerge, Aedifica a besoin de :
      </p>
      <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
        <li>Une <b>parcelle analysée</b> dans <i>Terrain &amp; zonage</i> (contraintes sourcées de la commune)</li>
        <li>Au moins un <b>document canonique validé</b> dans <i>Documents &amp; sources</i> (plans, notice d&apos;impact…)</li>
        <li>Idéalement, une commune <b>exploitable</b> (cf. ingestion sur Terrain) pour que les motifs cantonaux soient connus</li>
      </ul>
      <p className="note" style={{ color: "var(--mut)" }}>Aucune analyse n&apos;est inventée — tant que ces bases ne sont pas posées, la surface reste explicitement vide.</p>
    </div>
  </>);
  return (
    <>
      <div className="vh"><h2>Risque d&apos;opposition</h2><p>Les motifs d&apos;opposition les plus probables, évalués <b>sur les faits du dossier</b> — pour cibler précisément ce qu&apos;il faut désamorcer avant l&apos;enquête.</p></div>
      <div className="banner warn">Niveau global : <b style={{ textTransform: "capitalize" }}>{d.overall}</b> (score {d.score}). {d.disclaimer}</div>
      <p className="note" style={{ marginBottom: 12 }}>Base d&apos;analyse : <b>{canonicalDocs ?? 0} document(s) canonique(s)</b> du dossier + données parcelle. <br />Scan des <b>décisions publiques communales + jurisprudence</b> de la zone : à brancher (sources publiques) — aucune donnée inventée.</p>
      <div className="card">{d.signals?.map((s: any, i: number) => (
        <div className="row-line" key={i}><span className={`lvl ${lvlClass(s.level)}`}>{s.level}</span><span className="grow"><span className="ttl">{fr(s.ground)} <small style={{ display: "inline", color: "var(--mut)" }}>· {fr(s.category)}</small></span><small style={{ fontFamily: "var(--font-ui)", color: "var(--ink-90)", fontSize: 13 }}>{s.basis}</small></span></div>
      ))}</div>
    </>
  );
}

/* ===================== CONFORMITE ===================== */
// W14.B — Conformité: official-text references per domain. The architect can
// add a public URL pointing to the canonical règlement (NCCR, AEAI, MINERGIE,
// SIA 380/1, etc.) and link the filled attestation via an AttachField on the
// gate itself. The list is the atelier's vetted set of references; we never
// fabricate them.
const CONFORMITE_OFFICIAL_REFS: Record<string, { title: string; url: string }[]> = {
  legal: [
    { title: "Loi vaudoise sur l'aménagement du territoire (LATC)", url: "https://prestations.vd.ch/pub/blv-publication/actes/consolide/700.11" },
    { title: "Règlement vaudois sur les normes de protection incendie (AEAI)", url: "https://www.bsvonline.ch/fr/regelwerk/" },
    { title: "MoPEC 2014 — modèle d'ordonnance sur l'énergie", url: "https://www.endk.ch/fr/politique-energetique/mopec" },
    { title: "Loi vaudoise sur l'énergie (LVLEne)", url: "https://prestations.vd.ch/pub/blv-publication/actes/consolide/730.01" },
    { title: "Norme SIA 500 — accessibilité aux constructions", url: "https://www.sia.ch/fr/services-info/normes-de-la-sia/" },
  ],
  contractual: [
    { title: "Norme SIA 102 — prestations et honoraires architecte", url: "https://www.sia.ch/fr/services-info/normes-de-la-sia/" },
    { title: "SIA 2046 — Conventions BIM (IPB)", url: "https://www.sia.ch/fr/services-info/normes-de-la-sia/" },
  ],
};

function Conformite({ d, tasks, projectId, token, onOpenAtelierPlanning }: any) {
  if (!d) return <p className="spin">Chargement…</p>;
  const Gate = ({ g, i, domain }: any) => {
    const state = g.status === "satisfied" ? "satisfied" : g.status === "unknown" ? "unknown" : "action_required";
    return (
      <div key={i} style={{ borderTop: i === 0 ? "none" : "1px solid var(--line)", paddingTop: i === 0 ? 0 : 12, paddingBottom: 6 }}>
        <div className="row-line" style={{ borderBottom: "none", paddingBottom: 0 }}>
          <Trust state={state} />
          <span className="grow">
            <span className="ttl">{fr(g.title)} <small style={{ display: "inline", color: "var(--mut)" }}>({fr(g.domain)})</small></span>
            {g.next_action && <small>{g.next_action}</small>}
          </span>
        </div>
        {token && projectId && g.id && (
          <div style={{ paddingLeft: 32 }}>
            <AttachField token={token} projectId={projectId} ownerKind="permit" ownerId={"compliance-" + g.id} label="Attestation / pièce remplie" />
          </div>
        )}
      </div>
    );
  };
  const refs = (kind: "legal" | "contractual") => (
    <div style={{ marginTop: 8, padding: "8px 0 0", borderTop: "1px dashed var(--line)" }}>
      <div className="mono" style={{ fontSize: 10, color: "var(--mut)", letterSpacing: ".08em", textTransform: "uppercase", marginBottom: 6 }}>
        Textes officiels de référence
      </div>
      {CONFORMITE_OFFICIAL_REFS[kind].map((r, i) => (
        <div key={i} style={{ marginBottom: 4 }}>
          <a href={r.url} target="_blank" rel="noreferrer" className="mono" style={{ fontSize: 11, color: "var(--ink)", textDecoration: "underline" }}>{r.title}</a>
        </div>
      ))}
      <small style={{ color: "var(--mut)" }}>Liens vers la documentation officielle. Confirmez la version applicable à votre commune (la jurisprudence cantonale prime).</small>
    </div>
  );
  return (
    <>
      <div className="vh">
        <h2>Conformité</h2>
        <p>
          Obligations légales et conventions à lever avant le dépôt — contraignant vs contractuel. Pour chaque obligation, <b>joignez la pièce remplie</b> (rapport énergie, concept incendie, attestation accessibilité…) ; les liens vers les textes officiels apparaissent sous chaque section.
        </p>
      </div>
      <div className="banner warn"><b>{d.summary.legal_blockers}</b> obligation(s) légale(s) à lever.</div>
      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Obligations légales</h3>
        {d.legal?.map((g: any, i: number) => <Gate key={i} g={g} i={i} domain="legal" />)}
        {refs("legal")}
      </div>
      <div className="card">
        <h3>Conventions contractuelles (BIM)</h3>
        {d.contractual?.map((g: any, i: number) => <Gate key={i} g={g} i={i} domain="contractual" />)}
        {refs("contractual")}
      </div>
      <PhaseTasks phase="33" tasks={tasks || []} projectId={projectId} onOpenAtelierPlanning={onOpenAtelierPlanning} label="phase 33 · conformité énergie / incendie / accessibilité" />
    </>
  );
}

/* ===================== COPILOTE (action loop) ===================== */
// W11.D: paramétrable au lieu d'une demande hardcodée. L'architecte saisit l'ID
// de l'espace cible + la classification voulue (la pré-fill garde la démo
// "AC-SPACE-101 → bureau" comme exemple, mais c'est éditable). Sans endpoint
// Archicad renseigné, on garde un état vide honnête plutôt que de prétendre
// qu'on a une connexion live — Etienne avait raison : "surface fake" sinon.
function Copilote({ token, pid, ledger, onChange }: { token: string; pid: string; ledger?: any[]; onChange: () => void }) {
  const [txn, setTxn] = useState<any>(null); const [approved, setApproved] = useState(false); const [executed, setExecuted] = useState(false);
  const [msg, setMsg] = useState(""); const [blocked, setBlocked] = useState(false);
  const [endpoint, setEndpoint] = useState(""); const [mode, setMode] = useState(""); const [product, setProduct] = useState<any>(null);
  const [opKind, setOpKind] = useState<"set_property" | "rename" | "set_category">("set_property");
  const [target, setTarget] = useState("");      // ID de l'élément (ex. AC-SPACE-101)
  const [propName, setPropName] = useState("Classification");
  const [propAfter, setPropAfter] = useState(""); // valeur souhaitée
  async function dryRun() {
    setMsg(""); setBlocked(false);
    if (!target.trim() || !propAfter.trim()) { setMsg("Renseignez l'identifiant de l'élément Archicad ET la valeur cible avant l'aperçu."); return; }
    try {
      const op: any = { op_id: "O1", kind: opKind, target: target.trim(), undo: "restore" };
      if (opKind === "set_property") { op.property = propName.trim() || "Classification"; op.after = propAfter.trim(); }
      else if (opKind === "rename") { op.after = propAfter.trim(); }
      else if (opKind === "set_category") { op.category = propAfter.trim(); }
      const r = await api<any>(`/projects/${pid}/adapter/dry-run`, { method: "POST", token, body: { adapter_id: "archicad_json", operations: [op], adapter_endpoint: endpoint.trim() || undefined } });
      setTxn(r.transaction); setExecuted(false); setApproved(false); setMode(r.mode); setProduct(r.preview?.product);
      setMsg(r.mode === "live" ? `Aperçu live depuis Archicad ${r.preview?.product?.version || ""} — lecture seule.` : r.mode === "fixture_fallback" ? "Endpoint injoignable — aperçu sur le modèle replay." : "Aperçu prêt (replay). Rien n'a encore changé."); onChange();
    } catch (e: any) { setMsg(e.message); }
  }
  async function approve() { try { await api(`/projects/${pid}/approvals`, { method: "POST", token, body: { scope: "adapter_execution", basis: "validation architecte" } }); setApproved(true); setBlocked(false); setMsg("Exécution validée par l'architecte."); onChange(); } catch (e: any) { setMsg(e.message); } }
  async function execute() {
    if (!txn) { setMsg("Demandez d'abord un aperçu."); return; }
    try { const r = await api<any>(`/projects/${pid}/adapter/execute`, { method: "POST", token, body: { transaction: txn } });
      if (r.executed) { setExecuted(true); setBlocked(false); setMsg("Modification appliquée et inscrite au journal — réversible."); } else { setBlocked(true); setMsg(r.reason || "Bloqué : validation requise."); } onChange();
    } catch (e: any) { setMsg(e.message); }
  }
  const s1 = !!txn;
  const hasEndpoint = endpoint.trim().length > 0;
  return (
    <>
      <div className="vh"><div className="row"><h2>Copilote IA · maquette Archicad</h2><span className="badge live"><span className="d" />Opérationnel</span></div><p>L&apos;IA prépare une modification, vous la validez, elle l&apos;applique — tracé et réversible. <b>Rien ne change sans votre accord.</b></p></div>
      {!hasEndpoint && (
        // W14.B — the previous "Aucun endpoint Archicad" banner was opaque:
        // the architect had no idea what an "endpoint Archicad" was nor where
        // to find one. This card explains the prerequisite + the alternative
        // (replay mode for understanding the flow), in plain language.
        <div className="card" style={{ marginBottom: 14, borderLeft: "3px solid var(--ts-assume)" }}>
          <h3 style={{ margin: 0 }}>Branchement Archicad — pas encore configuré</h3>
          <p style={{ marginTop: 8 }}>
            Pour qu&apos;Aedifica modifie réellement votre maquette, il faut un <b>JSON-bridge Archicad</b> : une petite passerelle exposée sur votre poste (ou serveur atelier) qui reçoit les opérations de l&apos;IA et les applique dans Archicad via l&apos;API officielle. Tant que cette passerelle n&apos;est pas connectée :
          </p>
          <ul style={{ margin: "6px 0 10px 18px", padding: 0 }}>
            <li><b>Mode <i>replay</i></b> : l&apos;IA exécute l&apos;opération sur un modèle de fixture (pour comprendre le flux + valider l&apos;UX). Aucune mutation sur votre vraie maquette.</li>
            <li><b>Mode <i>live</i></b> : disponible dès qu&apos;une URL est renseignée ci-dessous (ex. <code className="mono">http://localhost:19723/aedifica</code>).</li>
          </ul>
          <p style={{ marginTop: 0 }}>
            Le bridge n&apos;est pas encore distribué publiquement — c&apos;est un add-on que l&apos;atelier installe sur la machine qui héberge Archicad. Vous pouvez explorer le flux complet sans bridge, sur le modèle replay.
          </p>
        </div>
      )}
      <div className="searchrow"><input value={endpoint} onChange={(e) => setEndpoint(e.target.value)} placeholder="Endpoint Archicad JSON — http://127.0.0.1:19723 (vide = replay)" /><button onClick={dryRun} disabled={!target.trim() || !propAfter.trim()}>Connecter &amp; aperçu</button></div>
      <div className="card" style={{ marginTop: 8, marginBottom: 12 }}>
        <h3>Opération à proposer à l&apos;architecte</h3>
        <div className="g2">
          <label className="mono" style={{ fontSize: 11, color: "var(--mut)" }}>Type
            <select className="fld" value={opKind} onChange={(e) => setOpKind(e.target.value as any)}>
              <option value="set_property">Modifier une propriété</option>
              <option value="rename">Renommer un élément</option>
              <option value="set_category">Changer la classification SIA</option>
            </select>
          </label>
          <label className="mono" style={{ fontSize: 11, color: "var(--mut)" }}>Élément Archicad (ID)
            <input className="fld" placeholder="ex. AC-SPACE-101" value={target} onChange={(e) => setTarget(e.target.value)} />
          </label>
          {opKind === "set_property" && (
            <label className="mono" style={{ fontSize: 11, color: "var(--mut)" }}>Nom de propriété
              <input className="fld" value={propName} onChange={(e) => setPropName(e.target.value)} placeholder="Classification" />
            </label>
          )}
          <label className="mono" style={{ fontSize: 11, color: "var(--mut)" }}>Valeur cible
            <input className="fld" placeholder={opKind === "set_category" ? "ex. eCH-0119:room.office" : "ex. bureau"} value={propAfter} onChange={(e) => setPropAfter(e.target.value)} />
          </label>
        </div>
        {target && propAfter && (
          <small style={{ color: "var(--mut)" }}>
            Demande : <b>{opKind === "rename" ? `renommer « ${target} » en « ${propAfter} »` : opKind === "set_category" ? `classer « ${target} » en « ${propAfter} »` : `mettre la propriété « ${propName || "Classification"} » de « ${target} » à « ${propAfter} »`}</b>
            {mode && <> · mode <b>{mode === "live" ? `live (${product?.version || "Archicad"})` : "replay"}</b></>}.
          </small>
        )}
      </div>
      <div className="stepper">
        <div className={`step ${executed ? "done" : s1 && !executed ? "act" : ""}`}><div className="idx">Étape 1</div><div className="nm">Aperçu (simulation)</div></div>
        <div className={`step ${approved ? "done" : s1 && !approved ? "act" : ""}`}><div className="idx">Étape 2</div><div className="nm">Votre validation</div></div>
        <div className={`step ${executed ? "done act" : ""}`}><div className="idx">Étape 3</div><div className="nm">Appliqué &amp; tracé</div></div>
      </div>
      <div className="actbar">
        <button className="ds-btn" disabled={!target.trim() || !propAfter.trim()} onClick={dryRun}>Demander un aperçu</button>
        <button className="ds-btn ghost" onClick={approve} disabled={!s1}>Valider l&apos;exécution</button>
        <button className="ds-btn ghost" onClick={execute} disabled={!s1}>Appliquer à la maquette</button>
      </div>
      {msg && <div className={`banner ${blocked ? "bad" : executed ? "ok" : ""}`}>{blocked && <b>Garde-fou · </b>}{msg}</div>}
      <div className="card"><h3>Historique du projet — horodaté, signé, réversible</h3>
        {[...(ledger || [])].map((e, i) => (<div className="claim" key={i}><Trust state={e.mutating ? "conflict" : e.event_type === "approval" ? "sourced" : "computed"} label={EVENT[e.event_type] || e.event_type} /><div><div className="ttl">{human(e)}</div>{e.mutating && <small>réf. {e.ledger_id} · réversible</small>}</div></div>))}
        {(ledger || []).length === 0 && <p className="spin">Aucune action. Connectez Archicad puis composez une opération ci-dessus.</p>}
      </div>
    </>
  );
}

/* ===================== COUTS ===================== */
function Couts({ d, onFee, tasks, projectPhase, projectId, onOpenAtelierPlanning }: any) {
  const [fi, setFi] = useState<any>({ cfc2: "", project_type: "villa", hourly_rate: "150", hours: "" });
  const [est, setEst] = useState<any>(null); const [busy, setBusy] = useState(false);
  const chf = (n: number) => "CHF " + Number(n).toLocaleString("fr-CH");
  const c = d?.cockpit;
  const calc = async () => { setBusy(true); try { const r = await onFee({ cfc2: Number(fi.cfc2) || 0, project_type: fi.project_type, hourly_rate: fi.hourly_rate ? Number(fi.hourly_rate) : null, hours: fi.hours ? Number(fi.hours) : null }); setEst(r.estimate); } catch { } finally { setBusy(false); } };
  const head = <div className="vh"><h2>Coûts &amp; honoraires</h2><p>Estimateur d&apos;honoraires SIA 102 (deux méthodes), rentabilité et hypothèses. Aucun coefficient SIA payant embarqué — la formule publique, vos paramètres.</p></div>;
  const feeCard = (
    <div className="card" style={{ marginBottom: 14 }}>
      <h3>Estimateur d&apos;honoraires (SIA 102)</h3>
      <div className="g2">
        <input className="fld" type="number" placeholder="Coût de l'ouvrage CFC2 (CHF)" value={fi.cfc2} onChange={(e) => setFi({ ...fi, cfc2: e.target.value })} />
        <select className="fld" value={fi.project_type} onChange={(e) => setFi({ ...fi, project_type: e.target.value })}><option value="villa">Villa</option><option value="logement">Logement collectif</option><option value="renovation">Rénovation</option><option value="amenagement">Aménagement</option><option value="autre">Autre</option></select>
        <input className="fld" type="number" placeholder="Tarif horaire (CHF/h)" value={fi.hourly_rate} onChange={(e) => setFi({ ...fi, hourly_rate: e.target.value })} />
        <input className="fld" type="number" placeholder="Heures estimées (T)" value={fi.hours} onChange={(e) => setFi({ ...fi, hours: e.target.value })} />
      </div>
      <div className="actbar"><span className="mono" style={{ fontSize: 11 }}>% du CFC2 &nbsp;ou&nbsp; H = T × h</span><span style={{ marginLeft: "auto" }} /><button className="ds-btn" disabled={busy} onClick={calc}>{busy ? "…" : "Estimer"}</button></div>
      {est && (
        <div style={{ marginTop: 10 }}>
          <div className="kpis">
            <div className="kpi"><div className="lab">Méthode % CFC2</div><div className="num" style={{ fontSize: 21 }}>{est.by_cost_method ? chf(est.by_cost_method) : "—"}</div><div className="sub">{Math.round(est.percentage * 100)} % du CFC2</div></div>
            <div className="kpi"><div className="lab">Méthode H = T × h</div><div className="num" style={{ fontSize: 21 }}>{est.by_time_method ? chf(est.by_time_method) : "—"}</div><div className="sub">{est.hours || "—"} h × {est.hourly_rate || "—"}</div></div>
            <div className="kpi"><div className="lab">Recommandé</div><div className="num" style={{ fontSize: 21 }}>{est.recommended ? chf(est.recommended) : "—"}</div><div className="sub">à ajuster (curseur)</div></div>
          </div>
          {Object.keys(est.by_phase || {}).length > 0 && <div className="card" style={{ marginTop: 10 }}><h3>Répartition par phase SIA</h3>{Object.entries(est.by_phase).map(([ph, v]: any) => (<div className="row-line" key={ph}><span className="grow"><span className="ttl">{SIA_PHASE_FR[ph] || "Phase " + ph}</span></span><span className="mono">{chf(v)}</span></div>))}</div>}
        </div>
      )}
    </div>
  );
  if (!c) return (<>{head}{feeCard}<div className="placeholder"><h4>Cockpit détaillé indisponible</h4><p>L&apos;estimation d&apos;honoraires détaillée (cockpit) n&apos;a pas encore été saisie. L&apos;estimateur ci-dessus reste utilisable.</p></div></>);
  return (
    <>{head}{feeCard}
      <div className="kpis">
        <div className="kpi"><div className="lab">Honoraires estimés</div><div className="num" style={{ fontSize: 22 }}>{chf(c.estimated_fee_chf)}</div><div className="sub">{c.estimated_hours} h · {c.hourly_rate_chf} CHF/h</div></div>
        <div className="kpi"><div className="lab">Marge cible</div><div className="num">{c.target_margin_percent}%</div><div className="sub">objectif atelier</div></div>
        <div className="kpi"><div className="lab">Risque de marge</div><div className="num" style={{ textTransform: "capitalize", fontSize: 24 }}>{c.margin_risk}</div><div className="sub">{c.absorbed_hours} h absorbées</div></div>
        <div className="kpi"><div className="lab">Prestations spéciales</div><div className="num">{c.special_prestations.length}</div><div className="sub">à chiffrer ou exclure</div></div>
      </div>
      <div className="g2">
        <div className="card"><h3>Prestations absorbées (non chiffrées)</h3>{c.absorbed_tasks.map((t: any, i: number) => (<div className="claim" key={i}><Trust state="assumption" label="absorbé" /><div><div className="ttl">{t.title}</div><small>{t.estimated_hours} h · {t.action}</small></div></div>))}</div>
        <div className="card"><h3>Hypothèses portées en soumission</h3>{d.tender_assumptions.map((a: any, i: number) => (<div className="claim" key={i}><Trust state="computed" label={a.kind} /><div><div className="ttl">{a.title}</div><small>colonne : {a.offer_comparison_column}</small></div></div>))}</div>
      </div>
      <PhaseTasks phase={projectPhase && projectPhase !== "0" ? projectPhase : "32"} tasks={tasks || []} projectId={projectId} onOpenAtelierPlanning={onOpenAtelierPlanning} />
      <div className="card" style={{ marginTop: 12 }}>
        <h3>Heures réellement engagées (toutes phases)</h3>
        <p style={{ color: "var(--mut)" }}>Somme des estimations des tâches du projet. À rapprocher des honoraires estimés ci-dessus pour calibrer votre tarif horaire.</p>
        {(() => {
          const total = (tasks || []).reduce((s: number, t: any) => s + (t.estimate_hours || 0), 0);
          const done = (tasks || []).filter((t: any) => t.status === "done").reduce((s: number, t: any) => s + (t.actual_hours || t.estimate_hours || 0), 0);
          return (
            <div className="kpis" style={{ marginTop: 8 }}>
              <div className="kpi"><div className="lab">Estimé total</div><div className="num">{total} h</div></div>
              <div className="kpi"><div className="lab">Engagé sur tâches faites</div><div className="num">{done} h</div></div>
              <div className="kpi"><div className="lab">Reste à engager</div><div className="num">{Math.max(0, total - done)} h</div></div>
            </div>
          );
        })()}
      </div>
    </>
  );
}

/* ===================== CHANTIER ===================== */
function Chantier({ d, tasks, projectId, onOpenAtelierPlanning }: any) {
  if (!d) return <p className="spin">Chargement…</p>;
  const map = (s: string) => (s === "closed" ? "satisfied" : s === "blocked" ? "conflict" : s === "open" ? "unknown" : "assumption");
  const lbl: Record<string, string> = { open: "ouvert", closed: "clos", blocked: "bloqué" };
  const head = <div className="vh"><div className="row" style={{ gap: 10, alignItems: "center" }}><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" style={{ color: "var(--ink-60)" }}><use href="/assets/functional-icons.svg#ic-datum-dimension" /></svg><h2 style={{ margin: 0 }}>Chantier &amp; remise</h2></div><p>Suivi d&apos;exécution : réserves / défauts et check-list de remise, avec responsable et échéance — la phase où l&apos;on mesure ce qui a vraiment été réalisé.</p></div>;
  // W14.B — explicit empty-state: the surface populates from phase 52
  // onwards. Until then we say so plainly + show what kind of evidence
  // will live here.
  if (d.data_basis === "empty") return (
    <>{head}
      <div className="card" style={{ borderLeft: "3px solid var(--ts-assume)" }}>
        <h3>Pas encore de suivi de chantier</h3>
        <p>
          Cette surface devient active à partir de la <b>phase 52 — réalisation</b>. Y vivront :
        </p>
        <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
          <li><b>Check-list de remise</b> — état des prestations, responsable, échéance</li>
          <li><b>Réserves &amp; défauts</b> — relevés contradictoires, gravité, résolution attendue</li>
          <li><b>Pièces signées</b> — PV de réception, attestations, levées de réserve (à joindre par item)</li>
        </ul>
        <p className="note" style={{ color: "var(--mut)" }}>
          Si vous êtes déjà sur un chantier, basculez le projet en phase 52 ou 53 depuis la barre du haut pour activer la surface.
        </p>
      </div>
      <PhaseTasks phase={["52", "53"]} tasks={tasks || []} projectId={projectId} onOpenAtelierPlanning={onOpenAtelierPlanning} label="phases 52/53 · chantier et mise en service" />
    </>
  );
  return (
    <>{head}
      <div className="banner warn"><b>{d.summary.handover_blocked}</b> remise bloquée · <b>{d.summary.defects_open}</b> défaut(s) ouvert(s).</div>
      <div className="g2">
        <div className="card"><h3>Check-list de remise</h3>{d.handover.map((i: any, k: number) => (<div className="claim" key={k}><Trust state={map(i.status)} label={lbl[i.status] || i.status} /><div><div className="ttl">{i.title}</div><small>{i.responsible_party} · échéance {i.due_at}</small></div></div>))}</div>
        <div className="card"><h3>Réserves &amp; défauts</h3>{d.defects.map((x: any, k: number) => (<div className="claim" key={k}><span className={`lvl ${lvlClass(x.severity)}`}>{x.severity}</span><div><div className="ttl">{x.title}</div><small>{x.responsible_party} · {x.status} · échéance {x.target_resolution}</small></div></div>))}</div>
      </div>
      <PhaseTasks phase={["52", "53"]} tasks={tasks || []} projectId={projectId} onOpenAtelierPlanning={onOpenAtelierPlanning} label="phases 52/53 · chantier et mise en service" />
    </>
  );
}

/* ===================== MEMOIRE ===================== */
const CAP_KIND: Record<string, string> = { friction: "Friction", observation: "Observation", photo: "Photo / preuve", decision: "Décision", regulation: "Règlement à l'étude" };
const CAP_TS: Record<string, string> = { friction: "is-assume", observation: "is-computed", photo: "is-sourced", decision: "is-decision", regulation: "is-conflict" };
function Memoire({ unknowns, ledger, captures, token, pid, onAddCapture, onDelCapture }: any) {
  const [f, setF] = useState<any>({ kind: "friction", content: "", source_ref: "" });
  const [busy, setBusy] = useState("");
  const [showCap, setShowCap] = useState(false);
  if (!unknowns) return <p className="spin">Chargement…</p>;
  const caps: any[] = captures?.captures || [];
  const add = async () => { if (!f.content.trim()) return; setBusy("add"); try { await onAddCapture({ ...f, source_ref: f.source_ref || null }); setF({ kind: f.kind, content: "", source_ref: "" }); setShowCap(false); } catch { } finally { setBusy(""); } };
  const act = async (p: Promise<any>, id: string) => { setBusy(id); try { await p; } catch { } finally { setBusy(""); } };
  // W11.D: positionnée comme JOURNAL AUTOMATIQUE (ledger + unknowns + alertes
  // règlement-à-l'étude captées). La capture manuelle est reléguée à un toggle
  // secondaire — pour les cas explicites (tél client, photo chantier) — et
  // n'est plus la vue principale qui faisait croire que c'était un bloc-notes.
  const regAlerts = caps.filter((c) => c.kind === "regulation");
  const ledRev = [...(ledger || [])].reverse();
  return (
    <>
      <div className="vh">
        <h2>Mémoire du projet</h2>
        <p>
          <b>Un journal automatique, pas un bloc-notes.</b> Aedifica écrit ici toute seule, au fur et à mesure que vous travaillez ailleurs dans le projet :
        </p>
        <ul style={{ margin: "4px 0 8px 18px", padding: 0 }}>
          <li><b>Inconnues</b> — chaque claim non sourcé / non décidé apparaît tant qu&apos;il n&apos;est pas levé ; cliquer permet d&apos;atteindre la surface qui le résout.</li>
          <li><b>Activité récente</b> — les écritures du ledger (validations de documents, approbations Copilote, ingestions, changements de phase…) horodatées et signées.</li>
          <li><b>Règlement à l&apos;étude</b> — les captures de type <i>regulation</i> que vous avez signalées comme modifications en cours.</li>
        </ul>
        <p>
          Le bouton <b>+ Capter</b> en bas est <b>secondaire</b> : il sert UNIQUEMENT à ranger ce qui n&apos;a aucune autre place (un coup de fil avec le client, une photo chantier, une friction non liée à un document). 95 % du temps vous n&apos;y touchez pas — la mémoire se construit toute seule via les actions sur les autres surfaces.
        </p>
      </div>

      <div className="g2">
        <div className="card">
          <div className="row" style={{ gap: 8, alignItems: "center", marginBottom: 8 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" style={{ color: "var(--ts-conflict)" }}><use href="/assets/functional-icons.svg#ic-datum-target" /></svg>
            <h3 style={{ margin: 0 }}>Inconnues du projet ({unknowns.length})</h3>
          </div>
          <small style={{ color: "var(--mut)", display: "block", marginBottom: 8 }}>Les cibles à cadrer avant de pouvoir avancer — chaque ligne porte la prochaine action.</small>
          {unknowns.length === 0 && <p className="spin">Rien d&apos;identifié comme inconnu à ce stade.</p>}
          {unknowns.map((c: any, i: number) => (
            <div className="claim" key={"u" + i}>
              <Trust state={c.state} />
              <div><div className="ttl">{c.title}</div>{c.next_action && <small>{c.next_action}</small>}</div>
            </div>
          ))}
        </div>
        <div className="card">
          <h3>Activité récente ({ledRev.length})</h3>
          {ledRev.length === 0 && <p className="spin">Aucune action enregistrée encore.</p>}
          {ledRev.slice(0, 10).map((e: any, i: number) => (
            <div className="claim" key={"l" + i}>
              <Trust state={e.mutating ? "conflict" : e.event_type === "approval" ? "sourced" : "computed"} label={EVENT[e.event_type] || e.event_type} />
              <div><div className="ttl">{human(e)}</div></div>
            </div>
          ))}
        </div>
      </div>

      {regAlerts.length > 0 && (
        <div className="card" style={{ marginTop: 12, borderLeft: "3px solid var(--ts-conflict)" }}>
          <h3>Règlement à l&apos;étude ({regAlerts.length})</h3>
          <p style={{ color: "var(--mut)" }}>Modifications réglementaires repérées qui peuvent affecter ce projet en cours.</p>
          {regAlerts.map((c: any) => (
            <div key={c.id} style={{ borderTop: "1px solid var(--line)", paddingTop: 8, marginTop: 8 }}>
              <div className="claim" style={{ marginBottom: 0 }}>
                <span className={`ds-ts ${CAP_TS.regulation || "is-conflict"}`}><span className="dot" />{CAP_KIND.regulation}</span>
                <div style={{ flex: 1 }}><div className="ttl">{c.content}</div><small>{[c.author ? "par " + c.author : null, (c.created_at || "").slice(0, 16).replace("T", " "), c.source_ref].filter(Boolean).join(" · ")}</small></div>
                <button className="signout" style={{ padding: 0 }} onClick={() => act(onDelCapture(c.id), "d" + c.id)}>✕</button>
              </div>
              {token && pid && <AttachField token={token} projectId={pid} ownerKind="capture" ownerId={c.id} label="Extrait réglementaire" />}
            </div>
          ))}
        </div>
      )}

      <div className="card" style={{ marginTop: 12 }}>
        <div className="row" style={{ alignItems: "baseline" }}>
          <h3 style={{ margin: 0 }}>Captures manuelles ({caps.length - regAlerts.length})</h3>
          <small style={{ color: "var(--mut)" }}>Friction · photo · décision verbale · … — pour ce qui n&apos;a pas d&apos;autre endroit où vivre.</small>
          <span className="grow" />
          <button className="toggle" onClick={() => setShowCap((v) => !v)}>{showCap ? "Annuler" : "+ Capter"}</button>
        </div>
        {showCap && (
          <div className="row" style={{ gap: 8, alignItems: "stretch", marginTop: 12 }}>
            <select className="fld" style={{ margin: 0, width: "auto" }} value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}>{Object.entries(CAP_KIND).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
            <input className="fld" style={{ margin: 0, flex: 1, minWidth: 160 }} placeholder="Ce que vous voulez garder en trace…" value={f.content} onChange={(e) => setF({ ...f, content: e.target.value })} onKeyDown={(e) => e.key === "Enter" && add()} />
            <input className="fld" style={{ margin: 0, width: 150 }} placeholder="Réf / photo (URL)" value={f.source_ref} onChange={(e) => setF({ ...f, source_ref: e.target.value })} />
            <button className="ds-btn" disabled={busy === "add" || !f.content} onClick={add}>{busy === "add" ? "…" : "Capter"}</button>
          </div>
        )}
        {caps.filter((c) => c.kind !== "regulation").length === 0 ? (
          <p className="spin" style={{ marginTop: 8 }}>Aucune capture manuelle. La plupart du temps, rien à mettre ici — la mémoire du projet vit toute seule dans le journal au-dessus.</p>
        ) : caps.filter((c) => c.kind !== "regulation").map((c: any) => (
          <div key={c.id} style={{ borderTop: "1px solid var(--line)", paddingTop: 8, marginTop: 8 }}>
            <div className="claim" style={{ marginBottom: 0 }}>
              <span className={`ds-ts ${CAP_TS[c.kind] || "is-unknown"}`}><span className="dot" />{CAP_KIND[c.kind] || c.kind}</span>
              <div style={{ flex: 1 }}><div className="ttl">{c.content}</div><small>{[c.author ? "par " + c.author : null, (c.created_at || "").slice(0, 16).replace("T", " "), c.source_ref].filter(Boolean).join(" · ")}</small></div>
              <button className="signout" style={{ padding: 0 }} onClick={() => act(onDelCapture(c.id), "d" + c.id)}>✕</button>
            </div>
            {token && pid && <AttachField token={token} projectId={pid} ownerKind="capture" ownerId={c.id} label="Photos / preuves" />}
          </div>
        ))}
      </div>
    </>
  );
}

/* ===================== INTERVENANTS (W9) ===================== */
const GROUP_KINDS: Record<string, string> = { company: "Entreprise", discipline: "Discipline", group: "Groupe" };
function Intervenants({ data, token, projectId, onAddGroup, onDelGroup, onAdd, onDel, onInvite }: any) {
  const [gName, setGName] = useState(""); const [gKind, setGKind] = useState("discipline"); const [showG, setShowG] = useState(false);
  const [f, setF] = useState<any>({ name: "", role: "", organization: "", email: "", phone: "", is_responsible: false, group_id: "" });
  const [busy, setBusy] = useState(false);
  const [inviting, setInviting] = useState<number | null>(null);
  const [inviteEmail, setInviteEmail] = useState("");
  const [issued, setIssued] = useState<{ id: number; email: string; token: string } | null>(null);
  // W14.A — atelier-wide directory: contacts already entered on other projects,
  // available for one-click import here. De-duplicated server-side.
  const [showDir, setShowDir] = useState(false);
  const [dir, setDir] = useState<any[] | null>(null);
  const [dirBusy, setDirBusy] = useState(false);
  async function loadDir() {
    if (!token || !projectId) return;
    setDirBusy(true);
    try {
      const r = await api<any>(`/orgs/intervenants-directory?project_id=${projectId}`, { token });
      setDir(r.contacts || []);
    } catch { setDir([]); }
    finally { setDirBusy(false); }
  }
  async function importContact(c: any) {
    setBusy(true);
    try {
      await onAdd({ name: c.name, role: c.role || "", organization: c.organization || "",
                    email: c.email || "", phone: c.phone || "", is_responsible: false,
                    group_id: null });
      // Refresh directory to remove the imported one from the suggestions.
      await loadDir();
    } catch {} finally { setBusy(false); }
  }
  if (!data) return <p className="spin">Chargement…</p>;
  const groups: any[] = data.groups || []; const people: any[] = data.people || [];
  const inGroup = (gid: number | null) => people.filter((p) => (p.group_id ?? null) === gid);
  const submit = async () => { if (!f.name.trim()) return; setBusy(true); try { await onAdd({ ...f, group_id: f.group_id ? Number(f.group_id) : null }); setF({ name: "", role: "", organization: "", email: "", phone: "", is_responsible: false, group_id: f.group_id }); } catch { } finally { setBusy(false); } };
  const addG = async () => { if (!gName.trim()) return; await onAddGroup(gName, gKind); setGName(""); setShowG(false); };
  const invite = async (p: any) => {
    if (!onInvite) return; const em = inviteEmail.trim() || p.email; if (!em) return;
    try { const r = await onInvite(p.id, em, p.name); setIssued({ id: p.id, email: em, token: r.invite_token }); setInviting(null); setInviteEmail(""); } catch { }
  };
  const Person = ({ p }: any) => (
    <div className="member">
      <span className="grow">
        <span className="nm">{p.name}{p.is_responsible && <small style={{ display: "inline", color: "var(--accent)" }}> · responsable</small>}</span>
        <span className="em">{[p.role, p.organization, p.email, p.phone].filter(Boolean).join(" · ") || "—"}</span>
      </span>
      {onInvite && (inviting === p.id ? (
        <span className="row" style={{ gap: 6 }}>
          <input className="fld" style={{ margin: 0, padding: "4px 8px", width: 180 }} placeholder={p.email || "e-mail"} value={inviteEmail} onChange={(e) => setInviteEmail(e.target.value)} />
          <button className="toggle" onClick={() => invite(p)}>Inviter</button>
          <button className="signout" style={{ padding: 0 }} onClick={() => { setInviting(null); setInviteEmail(""); }}>×</button>
        </span>
      ) : <button className="toggle" style={{ marginRight: 8 }} onClick={() => { setInviting(p.id); setInviteEmail(p.email || ""); }}>Inviter sur la plateforme</button>)}
      <button className="signout" style={{ padding: 0 }} onClick={() => onDel(p.id)}>Retirer</button>
    </div>
  );
  return (
    <>
      <div className="vh"><div className="row"><h2>Intervenants du projet</h2><span className="badge live"><span className="d" />Opérationnel</span></div><p>Les <b>acteurs de CE projet</b> — groupes, sous-groupes, personnes — avec contacts sourcés. Chaque intervenant peut être <b>invité sur la plateforme</b> (accès scoping) : il y verra ses documents et ses devoirs. <i>Différent de Équipe atelier</i>, qui liste les membres de votre atelier avec un compte Aedifica.</p></div>
      {issued && (
        <div className="banner ok" style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <span style={{ flex: 1 }}>Invitation émise pour <b>{issued.email}</b>. Transmettez ce code à l&apos;intervenant pour qu&apos;il définisse son mot de passe : <code className="mono" style={{ background: "var(--surface)", padding: "2px 6px", borderRadius: 4 }}>{issued.token}</code></span>
          <button className="toggle" onClick={() => navigator.clipboard?.writeText(issued.token).catch(() => {})}>Copier</button>
          <button className="toggle" onClick={() => setIssued(null)}>OK</button>
        </div>
      )}
      {/* W14.A — Atelier directory: contacts saisis sur d'autres projets,
          réimportables en un click ici (déduplication serveur). */}
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row" style={{ alignItems: "baseline" }}>
          <h3 style={{ margin: 0 }}>Annuaire atelier</h3>
          <small style={{ color: "var(--mut)", marginLeft: 8 }}>
            Contacts saisis sur d&apos;autres projets de votre atelier.
          </small>
          <span className="grow" />
          <button className="toggle" disabled={dirBusy} onClick={() => { setShowDir(v => !v); if (!showDir && !dir) loadDir(); }}>
            {showDir ? "Masquer" : dirBusy ? "…" : "Voir l'annuaire"}
          </button>
        </div>
        {showDir && (
          dir === null ? <p className="spin" style={{ marginTop: 8 }}>Chargement…</p>
          : dir.length === 0 ? <p className="spin" style={{ marginTop: 8 }}>
              Aucun contact réutilisable depuis un autre projet de l&apos;atelier.
            </p>
          : <div style={{ marginTop: 8 }}>
              {dir.map((c, i) => (
                <div className="row-line" key={i}>
                  <span className="grow">
                    <span className="ttl">{c.name}</span>
                    <small>{[c.role, c.organization, c.email].filter(Boolean).join(" · ")}</small>
                    <small style={{ color: "var(--mut)" }}>
                      Déjà vu dans : {(c.seen_in_projects || []).map((p: any) => p.name).join(", ")}
                    </small>
                  </span>
                  <button className="toggle" disabled={busy} onClick={() => importContact(c)}>Importer</button>
                </div>
              ))}
            </div>
        )}
      </div>

      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Ajouter un intervenant</h3>
        <div className="g2">
          <input className="fld" placeholder="Nom" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} />
          <input className="fld" placeholder="Rôle (ex. ingénieur civil)" value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })} />
          <input className="fld" placeholder="Organisation" value={f.organization} onChange={(e) => setF({ ...f, organization: e.target.value })} />
          <input className="fld" placeholder="E-mail" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} />
          <input className="fld" placeholder="Téléphone" value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} />
          <select className="fld" value={f.group_id} onChange={(e) => setF({ ...f, group_id: e.target.value })}><option value="">— sans groupe —</option>{groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}</select>
        </div>
        <div className="actbar">
          <label className="mono" style={{ display: "flex", alignItems: "center", gap: 7 }}><input type="checkbox" checked={f.is_responsible} onChange={(e) => setF({ ...f, is_responsible: e.target.checked })} /> Responsable / de référence</label>
          <span style={{ marginLeft: "auto" }} /><button className="ds-btn" disabled={busy || !f.name} onClick={submit}>{busy ? "…" : "Ajouter"}</button>
        </div>
      </div>
      <div className="row" style={{ marginBottom: 12 }}>
        {showG ? (
          <div className="actbar" style={{ margin: 0, width: "100%" }}>
            <input className="fld" style={{ margin: 0, flex: 1 }} placeholder="Nom du groupe (ex. Ingénieurs)" value={gName} onChange={(e) => setGName(e.target.value)} />
            <select className="fld" style={{ margin: 0, width: "auto" }} value={gKind} onChange={(e) => setGKind(e.target.value)}>{Object.entries(GROUP_KINDS).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
            <button className="ds-btn" onClick={addG} disabled={!gName}>Créer</button><button className="ds-btn ghost" onClick={() => setShowG(false)}>Annuler</button>
          </div>
        ) : <button className="toggle" onClick={() => setShowG(true)}>+ Nouveau groupe</button>}
      </div>
      {groups.map((g) => (
        <div className="card" key={g.id} style={{ marginBottom: 12 }}>
          <h3 style={{ display: "flex", alignItems: "center" }}>{g.name} <span className="chip" style={{ marginLeft: 8 }}>{GROUP_KINDS[g.kind] || g.kind}</span><button className="signout" style={{ marginLeft: "auto", padding: 0 }} onClick={() => onDelGroup(g.id)}>Supprimer le groupe</button></h3>
          {inGroup(g.id).length ? inGroup(g.id).map((p: any) => <Person key={p.id} p={p} />) : <p className="spin">Aucun membre.</p>}
        </div>
      ))}
      <div className="card"><h3>Sans groupe</h3>{inGroup(null).length ? inGroup(null).map((p: any) => <Person key={p.id} p={p} />) : <p className="spin">Tous les intervenants sont rattachés à un groupe.</p>}</div>
    </>
  );
}

/* ===================== DOCUMENTS & SOURCES (W9) ===================== */
const VLEVEL: Record<string, [string, string]> = { canonical: ["is-sourced", "Canonique"], indicative: ["is-computed", "Indicatif"], refused: ["is-conflict", "Refusé"], pending: ["is-unknown", "À valider"] };
function Documents({ docs, summary, intervenants, token, pid, onAdd, onRefresh, onValidate, onPatch, onDel, onGrant, onRevoke }: any) {
  const [f, setF] = useState<any>({ official_name: "", category: "general", source: "manual", confidential: false });
  const [busy, setBusy] = useState("");
  const [grantFor, setGrantFor] = useState<number | null>(null);
  const [grantSel, setGrantSel] = useState("");
  // W14.B — bulk import: pick multiple files; we POST a Document row per file
  // and attach the file as an upload to that document via /attachments/upload.
  const [bulkFiles, setBulkFiles] = useState<File[]>([]);
  const [bulkBusy, setBulkBusy] = useState(false);
  const [bulkProgress, setBulkProgress] = useState<{ done: number; total: number }>({ done: 0, total: 0 });
  const [bulkErr, setBulkErr] = useState<string | null>(null);
  async function bulkImport() {
    if (bulkFiles.length === 0) return;
    setBulkBusy(true); setBulkErr(null); setBulkProgress({ done: 0, total: bulkFiles.length });
    try {
      for (let i = 0; i < bulkFiles.length; i++) {
        const file = bulkFiles[i];
        // 1) Create the Document row (default category, source=manual, not LPD).
        const r = await api<any>(`/projects/${pid}/documents`, {
          method: "POST", token,
          body: { official_name: file.name.replace(/\.[^.]+$/, ""), category: "general", source: "manual", confidential: false },
        });
        const docId = r?.document?.id;
        if (!docId) continue;
        // 2) Attach the actual file as an upload.
        const fd = new FormData();
        fd.append("owner_kind", "document");
        fd.append("owner_id", String(docId));
        fd.append("title", file.name);
        fd.append("file", file);
        await apiUpload(`/projects/${pid}/attachments/upload`, fd, token!);
        setBulkProgress({ done: i + 1, total: bulkFiles.length });
      }
      setBulkFiles([]);
      // Refresh the parent's docs list so the new rows appear.
      await onRefresh?.();
    } catch (e: any) {
      setBulkErr(e?.message || "Échec d'import en lot");
    } finally {
      setBulkBusy(false);
    }
  }
  if (!docs) return <p className="spin">Chargement…</p>;
  const groups: any[] = intervenants?.groups || []; const people: any[] = intervenants?.people || [];
  const gName = (id: number) => groups.find((g) => g.id === id)?.name || `groupe ${id}`;
  const pName = (id: number) => people.find((p) => p.id === id)?.name || `personne ${id}`;
  const submit = async () => { if (!f.official_name.trim()) return; setBusy("add"); try { await onAdd(f); setF({ official_name: "", category: "general", source: "manual", confidential: false }); } catch { } finally { setBusy(""); } };
  const act = async (p: Promise<any>, id: string) => { setBusy(id); try { await p; } catch { } finally { setBusy(""); } };
  const grant = async (docId: number) => { if (!grantSel) return; const [t, id] = grantSel.split(":"); setBusy("g" + docId); try { await onGrant(docId, t === "g" ? { group_id: Number(id) } : { intervenant_id: Number(id) }); setGrantFor(null); setGrantSel(""); } catch { } finally { setBusy(""); } };
  const s = summary || { total: 0, pending: 0, by_level: {} };
  return (
    <>
      <div className="vh"><div className="row"><h2>Documents &amp; sources</h2><span className="badge live"><span className="d" />Opérationnel</span></div><p>La curation des sources du projet : import + versioning, validation par l&apos;architecte (canonique / indicatif / refusé), marquage confidentiel (LPD) et accès par intervenant. « Sourcé ou inconnu — jamais inventé. »</p></div>
      {s.pending > 0 && <div className="banner warn"><b>{s.pending}</b> document(s) à valider.</div>}
      {/* W14.B — bulk import: drag/select several files at once. One Document
          row is created per file, with the file attached as an upload. */}
      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Import en lot</h3>
        <p style={{ marginTop: 4, color: "var(--mut)" }}>
          Sélectionnez plusieurs fichiers à la fois : Aedifica crée un document par fichier, attache le fichier comme upload, et laisse les niveaux de validation à « en attente » pour que vous les revoyiez.
        </p>
        <div className="row" style={{ gap: 8, alignItems: "center", flexWrap: "wrap", marginTop: 8 }}>
          <input type="file" multiple disabled={bulkBusy} onChange={(e) => setBulkFiles(Array.from(e.target.files || []))} />
          <span className="grow" />
          {bulkFiles.length > 0 && !bulkBusy && (
            <small style={{ color: "var(--mut)" }}>{bulkFiles.length} fichier{bulkFiles.length > 1 ? "s" : ""} sélectionné{bulkFiles.length > 1 ? "s" : ""}</small>
          )}
          {bulkBusy && (
            <small className="mono" style={{ color: "var(--mut)" }}>{bulkProgress.done}/{bulkProgress.total} traités…</small>
          )}
          <button className="ds-btn" disabled={bulkBusy || bulkFiles.length === 0} onClick={bulkImport}>{bulkBusy ? "…" : "Importer en lot"}</button>
        </div>
        {bulkErr && <small style={{ color: "var(--ts-conflict)", display: "block", marginTop: 6 }}>{bulkErr}</small>}
      </div>
      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Ajouter / injecter une source</h3>
        <div className="g2">
          <input className="fld" placeholder="Nom officiel du document" value={f.official_name} onChange={(e) => setF({ ...f, official_name: e.target.value })} />
          <input className="fld" placeholder="Catégorie / dossier" value={f.category} onChange={(e) => setF({ ...f, category: e.target.value })} />
        </div>
        <div className="actbar">
          <select className="fld" style={{ margin: 0, width: "auto" }} value={f.source} onChange={(e) => setF({ ...f, source: e.target.value })}><option value="manual">Source manuelle (atelier)</option><option value="fetched">Récupérée en ligne</option></select>
          <label className="mono" style={{ display: "flex", alignItems: "center", gap: 7 }}><input type="checkbox" checked={f.confidential} onChange={(e) => setF({ ...f, confidential: e.target.checked })} /> Confidentiel (LPD)</label>
          <span style={{ marginLeft: "auto" }} /><button className="ds-btn" disabled={busy === "add" || !f.official_name} onClick={submit}>{busy === "add" ? "…" : "Ajouter"}</button>
        </div>
      </div>
      <div className="card">
        <h3>Sources du projet ({s.total})</h3>
        {docs.length === 0 && <p className="spin">Aucun document. Ajoutez ou injectez une source ci-dessus.</p>}
        {docs.map((dd: any) => { const [c, l] = VLEVEL[dd.validation_level] || ["is-unknown", dd.validation_level]; return (
          <div key={dd.id} style={{ borderTop: "1px solid var(--line)", paddingTop: 11, marginTop: 11 }}>
            <div className="row-line" style={{ border: 0, padding: 0 }}>
              <span className={`ds-ts ${c}`}><span className="dot" />{l}</span>
              <span className="grow"><span className="ttl">{dd.official_name}{dd.confidential && <small style={{ display: "inline", color: "var(--ts-conflict)" }}> · confidentiel</small>}</span><small>{[dd.category, dd.latest, dd.validated_by ? `validé par ${dd.validated_by}` : null].filter(Boolean).join(" · ")}</small></span>
              <span className="row" style={{ gap: 6 }}>
                <button className={`toggle ${dd.validation_level === "canonical" ? "on" : ""}`} disabled={busy === `v${dd.id}`} onClick={() => act(onValidate(dd.id, "canonical"), `v${dd.id}`)}>Canonique</button>
                <button className={`toggle ${dd.validation_level === "indicative" ? "on" : ""}`} disabled={busy === `v${dd.id}`} onClick={() => act(onValidate(dd.id, "indicative"), `v${dd.id}`)}>Indicatif</button>
                <button className={`toggle ${dd.validation_level === "refused" ? "on" : ""}`} disabled={busy === `v${dd.id}`} onClick={() => act(onValidate(dd.id, "refused"), `v${dd.id}`)}>Refusé</button>
                <button className={`toggle ${dd.confidential ? "on" : ""}`} onClick={() => act(onPatch(dd.id, { confidential: !dd.confidential }), `c${dd.id}`)}>{dd.confidential ? "Confidentiel (LPD)" : "Rendre confidentiel"}</button>
                <button className="signout" style={{ padding: 0 }} onClick={() => act(onDel(dd.id), `x${dd.id}`)}>✕</button>
              </span>
            </div>
            <div className="row" style={{ gap: 6, marginTop: 7, flexWrap: "wrap" }}>
              <span className="mono" style={{ fontSize: 10 }}>Accès :</span>
              {(dd.grants || []).length === 0 && <span className="mono" style={{ fontSize: 10, color: dd.confidential ? "var(--ts-conflict)" : "var(--mut)" }}>{dd.confidential ? "confidentiel — restreint" : "aucun (atelier seul)"}</span>}
              {(dd.grants || []).map((gr: any) => (
                <span key={gr.id} className="chip" style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>{gr.group_id ? gName(gr.group_id) : pName(gr.intervenant_id)}<button className="signout" style={{ padding: 0 }} onClick={() => act(onRevoke(dd.id, gr.id), `r${gr.id}`)}>✕</button></span>
              ))}
              {grantFor === dd.id ? (
                <span className="row" style={{ gap: 4 }}>
                  <select className="fld" style={{ margin: 0, padding: "4px 8px", width: "auto" }} value={grantSel} onChange={(e) => setGrantSel(e.target.value)}>
                    <option value="">— qui ? —</option>
                    {groups.map((g) => <option key={"g" + g.id} value={"g:" + g.id}>Groupe · {g.name}</option>)}
                    {people.map((p) => <option key={"p" + p.id} value={"p:" + p.id}>{p.name}</option>)}
                  </select>
                  <button className="toggle" disabled={!grantSel} onClick={() => grant(dd.id)}>OK</button>
                  <button className="signout" style={{ padding: 0 }} onClick={() => setGrantFor(null)}>annuler</button>
                </span>
              ) : <button className="toggle" style={{ padding: "3px 8px" }} onClick={() => { setGrantFor(dd.id); setGrantSel(""); }}>+ accès</button>}
            </div>
            {token && pid && <AttachField token={token} projectId={pid} ownerKind="document" ownerId={dd.id} />}
          </div>
        ); })}
      </div>
    </>
  );
}

/* ===================== CHECKLIST SIA (W9 #221) ===================== */
const SIA_PHASE_FR: Record<string, string> = { "11": "1 · Définition des objectifs", "21": "2 · Études préliminaires", "22": "2 · Choix des mandataires", "31": "3.31 · Avant-projet", "32": "3.32 · Projet de l'ouvrage", "33": "3.33 · Autorisation / enquête", "41": "4.41 · Appel d'offres", "51": "5.51 · Projet d'exécution", "52": "5.52 · Chantier", "53": "5.53 · Mise en service", "61": "6 · Exploitation" };
const CSTATUS: Record<string, [string, string]> = { done: ["is-sourced", "Fait"], todo: ["is-unknown", "À faire"], deferred: ["is-assume", "Plus tard"], skipped: ["is-computed", "Inutile"] };
/* W10: short labels for the four actor categories — also surfaced by the API. */
const ACTOR_FR: Record<string, string> = { mo: "Maître d'ouvrage", architecte: "Atelier", mandataire: "Mandataire", entreprise: "Entreprise" };
const ACTOR_CHIP: Record<string, string> = { mo: "is-decision", architecte: "is-sourced", mandataire: "is-computed", entreprise: "is-assume" };

function Checklist({ data, entryPhase, token, pid, onSeed, onPatch }: any) {
  const valid = /^(11|21|22|31|32|33|41|51|52|53|61)$/;
  const [phase, setPhase] = useState(valid.test(entryPhase || "") ? entryPhase : "11");
  const [busy, setBusy] = useState("");
  const [actorFilter, setActorFilter] = useState<string>("");  // "" = all
  const [hideDone, setHideDone] = useState<boolean>(false);
  if (!data) return <p className="spin">Chargement…</p>;
  const items: any[] = data.items || []; const s = data.summary || {};
  const byActor = s.by_actor || {};
  const seed = async () => { setBusy("seed"); try { await onSeed(phase); } catch { } finally { setBusy(""); } };
  const set = async (id: number, status: string) => { setBusy("i" + id); try { await onPatch(id, status); } catch { } finally { setBusy(""); } };
  if (!s.seeded) {
    return (
      <>
        <div className="vh"><h2>Checklist SIA</h2><p>Les steps du mandat, dérivés de la norme SIA — par phase <b>et par acteur</b> (maître d&apos;ouvrage, atelier, mandataire, entreprise). Déjà classés dans l&apos;ordre ; vous activez / différez / désactivez selon le projet.</p></div>
        <div className="placeholder"><h4>Checklist non initialisée</h4><p>Initialisez la checklist depuis le gabarit SIA. Choisissez la <b>phase d&apos;entrée</b> du projet : les steps des phases antérieures seront marqués « rétroactif » (à reconstituer pour un projet repris en cours).</p>
          <div className="actbar" style={{ justifyContent: "center", marginTop: 14 }}>
            <select className="fld" style={{ margin: 0, width: "auto" }} value={phase} onChange={(e) => setPhase(e.target.value)}>{Object.entries(SIA_PHASE_FR).map(([v, lb]) => <option key={v} value={v}>{lb}</option>)}</select>
            <button className="ds-btn" disabled={busy === "seed"} onClick={seed}>{busy === "seed" ? "…" : "Initialiser la checklist"}</button>
          </div>
        </div>
      </>
    );
  }
  const done = (s.by_status?.done) || 0;
  let filtered = actorFilter ? items.filter((i) => i.actor === actorFilter) : items;
  if (hideDone) filtered = filtered.filter((i) => i.status !== "done" && i.status !== "skipped");
  const phases = filtered.map((i) => i.phase_code).filter((v, idx, a) => a.indexOf(v) === idx);
  return (
    <>
      <div className="vh"><div className="row"><h2>Checklist SIA</h2><span className="badge live"><span className="d" />{done}/{s.total} fait</span></div><p>Steps réels du projet, <b>par phase et par acteur</b>.{s.retroactive > 0 && <> <b>{s.retroactive} step(s) rétroactif(s)</b> à reconstituer.</>}{s.external_blockers > 0 && <> <span className="ds-ts is-conflict"><span className="dot" />{s.external_blockers} bloquant(s) externe(s)</span></>}</p></div>
      <div className="actbar" style={{ marginBottom: 12, gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <label className="mono" style={{ fontSize: 11, color: "var(--mut, #6A6F73)", display: "flex", alignItems: "center", gap: 8 }}>
          Acteur
          <select className="fld" style={{ margin: 0, padding: "6px 10px", width: "auto", minWidth: 220 }} value={actorFilter} onChange={(e) => setActorFilter(e.target.value)}>
            <option value="">Tous les acteurs ({s.total || 0})</option>
            {Object.entries(ACTOR_FR).map(([k, lb]) => {
              const slot = byActor[k] || { total: 0, todo: 0, done: 0 };
              return <option key={k} value={k}>{lb} — {slot.total || 0} step{slot.total > 1 ? "s" : ""}{slot.todo ? ` · ${slot.todo} à faire` : ""}</option>;
            })}
          </select>
        </label>
        <label className="mono" style={{ fontSize: 11, color: "var(--mut, #6A6F73)", display: "flex", alignItems: "center", gap: 8 }}>
          <input type="checkbox" checked={hideDone} onChange={(e) => setHideDone(e.target.checked)} /> Masquer les étapes terminées / inutiles
        </label>
      </div>
      {phases.map((ph) => {
        const phaseItems = filtered.filter((i) => i.phase_code === ph);
        const phaseDone = phaseItems.filter((i) => i.status === "done" || i.status === "skipped");
        const phaseOpen = phaseItems.filter((i) => i.status !== "done" && i.status !== "skipped");
        return (
        <div className="card" key={ph} style={{ marginBottom: 12 }}>
          <div className="row" style={{ alignItems: "baseline" }}>
            <h3 style={{ margin: 0 }}>{SIA_PHASE_FR[ph] || ph}</h3>
            <small style={{ color: "var(--mut)", marginLeft: 8 }}>
              {phaseOpen.length} ouvert{phaseOpen.length > 1 ? "s" : ""}{phaseDone.length > 0 ? ` · ${phaseDone.length} clos` : ""}
            </small>
          </div>
          {/* W14.C.1 — compact row: a single status select (was 4 toggles
              taking up half the row) + the actor as a discreet tag rather
              than another colored chip. Title + status are what we read. */}
          {phaseItems.map((it) => {
            const done = it.status === "done" || it.status === "skipped";
            const [c, l] = CSTATUS[it.status] || ["is-unknown", it.status];
            return (
              <div key={it.id} style={{ borderTop: "1px solid var(--line)", paddingTop: 10, marginTop: 10, opacity: done ? 0.55 : 1 }}>
                <div className="row-line" style={{ border: 0, padding: 0, gap: 10 }}>
                  <span className={`ds-ts ${c}`} style={{ minWidth: 80 }}><span className="dot" />{l}</span>
                  <span className="grow">
                    <span className="ttl">
                      {it.title}
                      {it.is_retroactive && <small style={{ display: "inline", color: "var(--ts-assume)" }}> · rétroactif</small>}
                      {it.is_external && it.status === "todo" && <small style={{ display: "inline", color: "var(--ts-conflict)" }}> · en attente de l&apos;extérieur</small>}
                    </span>
                    <small style={{ color: "var(--mut)" }}>
                      {ACTOR_FR[it.actor] || it.actor}{it.responsible_name ? ` · ${it.responsible_name}` : ""}
                    </small>
                  </span>
                  <select className="fld" style={{ margin: 0, padding: "5px 10px", width: "auto" }}
                          disabled={busy === `i${it.id}`}
                          value={it.status}
                          onChange={(e) => set(it.id, e.target.value)}
                          title="Changer le statut">
                    <option value="todo">À faire</option>
                    <option value="done">Fait</option>
                    <option value="deferred">Plus tard</option>
                    <option value="skipped">Inutile</option>
                  </select>
                </div>
                {token && pid && !done && <AttachField token={token} projectId={pid} ownerKind="checklist" ownerId={it.id} label="Livrables / preuves" />}
              </div>
            );
          })}
        </div>
        );
      })}
    </>
  );
}

/* ===================== COORDINATION — single point of truth (W10) ===================== */
// W14.C.1 — Coordination rework. The previous layout was a vertical stack of
// nested cards (g2 inside card), visually flat and dense. The new layout
// builds a clear hierarchy:
//   1. KPI strip up top — the 4 numbers the architect scans first.
//   2. Single-column "Qui doit quoi" with an actor filter (tabs) so the
//      reader sees ONE focused list at a time instead of 4 mini-cards.
//   3. Side-by-side "Blocages externes" vs "Blocages atelier" — the colors
//      now match the semantic (conflict-red for external waits, assume-amber
//      for atelier blocks).
//   4. Documents à valider + steps checklist à valider in a compact footer
//      that doubles as nav shortcuts.
function Coordination({ data, onRefresh, go, projectId, onOpenAtelierPlanning }: { data: any; onRefresh: () => void; go: (v: View) => void; projectId: string; onOpenAtelierPlanning: (pid: string) => void }) {
  useEffect(() => { if (!data) onRefresh(); }, []);
  const [actorTab, setActorTab] = useState<string>("");
  if (!data) return <p className="spin">Chargement de la coordination…</p>;
  const owes = data.who_owes_what || {};
  const blockers = data.blockers || { external: [], atelier: [], counts: { external: 0, atelier: 0 } };
  const docs = (data.documents?.items || []);
  const queue = data.to_validate || {};
  const allOwes = Object.values(owes).flat() as any[];
  const totalOpen = allOwes.length;
  const totalExternal = blockers.counts?.external ?? blockers.external?.length ?? 0;
  const totalAtelier = blockers.counts?.atelier ?? blockers.atelier?.length ?? 0;
  const totalToValidate = (queue.documents?.length || 0) + (queue.checklist_todo || 0);
  // Build per-actor counts for the tabs.
  const actorCounts = Object.fromEntries(Object.keys(ACTOR_FR).map((k) => [k, (owes[k] || []).length])) as Record<string, number>;
  const visibleOwes: any[] = actorTab ? (owes[actorTab] || []) : allOwes;
  return (
    <>
      <div className="vh">
        <div className="row" style={{ gap: 10, alignItems: "center" }}>
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" style={{ color: "var(--ink-60)" }}><use href="/assets/functional-icons.svg#ic-datum-target" /></svg>
          <h2 style={{ margin: 0 }}>Coordination</h2><span className="badge live"><span className="d" />Point unique</span>
          <span className="grow" />
          <button className="toggle" onClick={() => onOpenAtelierPlanning(projectId)} title="Ouvrir le planning Atelier filtré sur ce projet">
            Planning Atelier →
          </button>
        </div>
        <p>Le tableau de bord opérationnel du projet : <b>qui doit quoi</b>, <b>où ça bloque</b>, <b>ce qui attend votre validation</b>. Source : la feuille SIA Vaud, projetée par acteur.</p>
      </div>

      {/* KPI strip — the 4 numbers the architect scans first */}
      <div className="kpis" style={{ marginBottom: 14 }}>
        <div className="kpi"><div className="lab">Devoirs ouverts</div><div className="num">{totalOpen}</div><div className="sub">tous acteurs</div></div>
        <button className="kpi click" onClick={() => go("documents")}><div className="lab">Documents à valider</div><div className="num">{queue.documents?.length || 0}</div><div className="sub">en attente</div></button>
        <button className="kpi click" onClick={() => go("checklist")}><div className="lab">Steps checklist</div><div className="num">{queue.checklist_todo || 0}</div><div className="sub">à faire</div></button>
        <div className="kpi"><div className="lab">Blocages</div><div className="num">{totalExternal + totalAtelier}</div><div className="sub" style={{ color: "var(--ts-conflict)" }}>{totalExternal} ext · {totalAtelier} atelier</div></div>
      </div>

      {/* Qui doit quoi — single list with actor tabs */}
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row" style={{ alignItems: "baseline", gap: 12 }}>
          <h3 style={{ margin: 0 }}>Qui doit quoi</h3>
          <small style={{ color: "var(--mut)" }}>{visibleOwes.length} ouvert{visibleOwes.length > 1 ? "s" : ""}</small>
          <span className="grow" />
          <button className="signout" style={{ padding: 0 }} onClick={() => go("checklist")}>Voir la checklist complète →</button>
        </div>
        <div className="row" style={{ gap: 6, flexWrap: "wrap", marginTop: 10 }}>
          <button className={`toggle ${actorTab === "" ? "on" : ""}`} onClick={() => setActorTab("")}>Tous ({totalOpen})</button>
          {Object.entries(ACTOR_FR).map(([k, lb]) => (
            <button key={k} className={`toggle ${actorTab === k ? "on" : ""}`} disabled={actorCounts[k] === 0 && actorTab !== k} onClick={() => setActorTab(actorTab === k ? "" : k)}>
              {lb} ({actorCounts[k] || 0})
            </button>
          ))}
        </div>
        <div style={{ marginTop: 10 }}>
          {visibleOwes.length === 0 && <p className="spin" style={{ paddingTop: 8 }}>Rien d&apos;ouvert pour {actorTab ? ACTOR_FR[actorTab] : "ce périmètre"}.</p>}
          {visibleOwes.slice(0, 12).map((r: any) => (
            <div key={r.id} className="row-line">
              <span className={`ds-ts ${ACTOR_CHIP[r.actor] || "is-unknown"}`} style={{ minWidth: 110 }}><span className="dot" />{ACTOR_FR[r.actor] || r.actor}</span>
              <span className="grow">
                <span className="ttl" style={{ fontSize: 13 }}>{r.title}</span>
                <small>phase {r.phase_code}{r.is_retroactive ? " · rétroactif" : ""}{r.responsible_name ? ` · ${r.responsible_name}` : ""}</small>
              </span>
            </div>
          ))}
          {visibleOwes.length > 12 && <small style={{ color: "var(--mut)" }}>+ {visibleOwes.length - 12} de plus — cliquez « Voir la checklist complète » au-dessus.</small>}
        </div>
      </div>

      {/* Où ça bloque — side-by-side with semantic colors */}
      <div className="g2" style={{ marginBottom: 14 }}>
        <div className="card" style={{ borderLeft: "3px solid var(--ts-conflict)", margin: 0 }}>
          <div className="row" style={{ alignItems: "baseline" }}>
            <h3 style={{ margin: 0 }}>Blocages externes ({totalExternal})</h3>
            <small style={{ color: "var(--mut)", marginLeft: 8 }}>en attente d&apos;un acteur hors atelier</small>
          </div>
          {blockers.external.length === 0 && <p className="spin" style={{ paddingTop: 8 }}>Aucun bloquant externe.</p>}
          {blockers.external.slice(0, 8).map((b: any) => (
            <div key={b.id} className="row-line">
              <span className={`ds-ts ${ACTOR_CHIP[b.actor] || "is-assume"}`}><span className="dot" />{ACTOR_FR[b.actor] || b.actor}</span>
              <span className="grow">
                <span className="ttl" style={{ fontSize: 13 }}>{b.title}</span>
                <small>phase {b.phase_code}</small>
              </span>
            </div>
          ))}
        </div>
        <div className="card" style={{ borderLeft: "3px solid var(--ts-assume)", margin: 0 }}>
          <div className="row" style={{ alignItems: "baseline" }}>
            <h3 style={{ margin: 0 }}>Blocages atelier ({totalAtelier})</h3>
            <small style={{ color: "var(--mut)", marginLeft: 8 }}>tâches internes bloquées</small>
          </div>
          {blockers.atelier.length === 0 && <p className="spin" style={{ paddingTop: 8 }}>Aucun blocage atelier.</p>}
          {blockers.atelier.slice(0, 8).map((t: any) => (
            <div key={t.id} className="row-line">
              <span className="ds-ts is-assume"><span className="dot" />{t.priority?.toUpperCase()}</span>
              <span className="grow">
                <span className="ttl" style={{ fontSize: 13 }}>{t.title}</span>
                {t.assignee && <small>{t.assignee}</small>}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Documents récents — only validation-pending by default */}
      {(queue.documents?.length || 0) > 0 && (
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="row" style={{ alignItems: "baseline" }}>
            <h3 style={{ margin: 0 }}>Documents en attente de validation</h3>
            <small style={{ color: "var(--mut)", marginLeft: 8 }}>{queue.documents.length} pièce{queue.documents.length > 1 ? "s" : ""}</small>
            <span className="grow" />
            <button className="toggle" onClick={() => go("documents")}>Ouvrir Documents →</button>
          </div>
          {(queue.documents || []).slice(0, 8).map((d: any) => (
            <div key={d.id} className="row-line">
              <span className="ds-ts is-assume"><span className="dot" />À valider</span>
              <span className="grow"><span className="ttl" style={{ fontSize: 13 }}>{d.official_name}</span><small>{[d.category, d.confidential ? "confidentiel (LPD)" : null].filter(Boolean).join(" · ")}</small></span>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

/* ===================== EXTERNAL USER VIEW (W10 — client / mandataire) ===================== */
function ExternalView({ ext, onTick, onSignOut }: { ext: any; onTick: (id: number, status: string) => void; onSignOut: () => void }) {
  const me = ext.me || {}; const project = me.project || {}; const iv = me.intervenant || {};
  const checklist = ext.checklist || { items: [], summary: {} };
  const docs = ext.documents?.documents || [];
  const isMo = iv.actor_category === "mo";
  const intro = isMo
    ? "Voici votre projet. Cette page rassemble : ce que nous attendons de vous, vos documents accessibles, et l'avancée — le tout côte à côte avec votre architecte."
    : "Voici votre mandat. Cette page rassemble : ce que nous attendons de vous, vos documents accessibles, et l'avancée — côte à côte avec l'atelier.";
  const phases = Array.from(new Set(checklist.items.map((c: any) => c.phase_code))) as string[];
  return (
    <div className="ws" style={{ gridTemplateColumns: "1fr" }}>
      <main className="ws__main" style={{ maxWidth: 900, margin: "0 auto", padding: 24 }}>
        <div className="vh" style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <Wordmark height={48} />
          <span className="grow" />
          <small className="mono">{me.user?.email}</small>
          <button className="signout" onClick={onSignOut}>Déconnexion</button>
        </div>
        <div className="card" style={{ marginBottom: 14 }}>
          <h2>{project.name || project.project_id}</h2>
          <p>{intro}</p>
          <div className="row" style={{ flexWrap: "wrap", gap: 8 }}>
            <span className="ds-ts is-sourced"><span className="dot" />{iv.name}{iv.organization ? ` · ${iv.organization}` : ""}</span>
            <span className="ds-ts is-computed"><span className="dot" />{iv.role || (isMo ? "Maître d'ouvrage" : "Intervenant")}</span>
            <span className="ds-ts is-decision"><span className="dot" />{me.phase_label || project.phase_code}</span>
          </div>
        </div>
        <div className="card" style={{ marginBottom: 14 }}>
          <div className="row"><h3>{isMo ? "Ce que vous devez fournir" : "Vos livrables"}</h3><span className="grow" /><span className="badge live"><span className="d" />{checklist.summary?.done || 0}/{checklist.summary?.total || 0} fait</span></div>
          {checklist.items.length === 0 && <p className="spin">Rien à faire pour le moment — l&apos;atelier vous notifiera.</p>}
          {phases.map((ph) => (
            <div key={ph} style={{ borderTop: "1px solid var(--line)", paddingTop: 11, marginTop: 11 }}>
              <h4 style={{ margin: "0 0 8px" }}>{checklist.items.find((c: any) => c.phase_code === ph)?.phase_label || ph}</h4>
              {checklist.items.filter((c: any) => c.phase_code === ph).map((it: any) => (
                <div key={it.id} className="row-line">
                  <span className={`ds-ts ${it.status === "done" ? "is-sourced" : "is-assume"}`}><span className="dot" />{it.status === "done" ? "Fait" : "À faire"}</span>
                  <span className="grow"><span className="ttl">{it.title}{it.is_retroactive && <small style={{ display: "inline", color: "var(--ts-assume)" }}> · à reconstituer</small>}</span></span>
                  <button className="ds-btn" onClick={() => onTick(it.id, it.status === "done" ? "todo" : "done")}>{it.status === "done" ? "↺ Annuler" : "✓ Marquer fait"}</button>
                </div>
              ))}
            </div>
          ))}
        </div>
        <div className="card">
          <h3>Vos documents</h3>
          <p>Documents auxquels l&apos;atelier vous a donné accès.</p>
          {docs.length === 0 && <p className="spin">Aucun document partagé pour l&apos;instant.</p>}
          {docs.map((d: any) => (
            <div key={d.id} className="row-line">
              <span className={`ds-ts ${d.validation_level === "canonical" ? "is-sourced" : d.validation_level === "refused" ? "is-conflict" : "is-computed"}`}><span className="dot" />{d.validation_level}</span>
              <span className="grow"><span className="ttl">{d.official_name}</span><small> · {d.category}{d.confidential ? " · confidentiel (LPD)" : ""} · accès : {d.access_level}</small></span>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

/* ===================== EXIGENCES · BRS (W9 #223) ===================== */
const BRS_CHAN: Record<string, string> = { phone: "Téléphone", email: "E-mail", pv: "PV", meeting: "Séance", other: "Autre" };
const BRS_KIND: Record<string, string> = { requirement: "Exigence", change: "Changement", decision: "Décision" };
const BRS_STATUS: Record<string, [string, string]> = { active: ["is-sourced", "Actif"], superseded: ["is-computed", "Remplacé"], locked: ["is-decision", "Verrouillé"] };
function Brs({ data, intervenants, token, pid, onAdd, onPatch, onDel }: any) {
  const [f, setF] = useState<any>({ content: "", kind: "requirement", channel: "phone", emitter_intervenant_id: "", source_ref: "" });
  const [busy, setBusy] = useState("");
  if (!data) return <p className="spin">Chargement…</p>;
  const entries: any[] = data.entries || []; const s = data.summary || {};
  const people: any[] = intervenants?.people || [];
  const submit = async () => { if (!f.content.trim()) return; setBusy("add"); try { await onAdd({ ...f, emitter_intervenant_id: f.emitter_intervenant_id ? Number(f.emitter_intervenant_id) : null }); setF({ content: "", kind: f.kind, channel: f.channel, emitter_intervenant_id: f.emitter_intervenant_id, source_ref: "" }); } catch { } finally { setBusy(""); } };
  const act = async (p: Promise<any>, id: string) => { setBusy(id); try { await p; } catch { } finally { setBusy(""); } };
  return (
    <>
      <div className="vh"><div className="row"><h2>Exigences · BRS</h2><span className="badge live"><span className="d" />Opérationnel</span></div><p><b>Business Requirements Specifications</b> — le registre vivant des exigences du client / maître d&apos;ouvrage, qui changent en permanence. Chaque entrée est <b>sourcée</b> (canal), <b>attribuée</b> (émetteur) et <b>horodatée</b> : votre traçabilité pour vous protéger.</p></div>
      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Consigner une exigence / un changement</h3>
        <textarea className="fld" style={{ minHeight: 64, resize: "vertical", width: "100%" }} placeholder="Ce que le client / le maître d'ouvrage a demandé ou décidé…" value={f.content} onChange={(e) => setF({ ...f, content: e.target.value })} />
        <div className="g2">
          <select className="fld" value={f.kind} onChange={(e) => setF({ ...f, kind: e.target.value })}>{Object.entries(BRS_KIND).map(([v, lb]) => <option key={v} value={v}>{lb}</option>)}</select>
          <select className="fld" value={f.channel} onChange={(e) => setF({ ...f, channel: e.target.value })}>{Object.entries(BRS_CHAN).map(([v, lb]) => <option key={v} value={v}>Canal : {lb}</option>)}</select>
          <select className="fld" value={f.emitter_intervenant_id} onChange={(e) => setF({ ...f, emitter_intervenant_id: e.target.value })}><option value="">— émetteur —</option>{people.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
          <input className="fld" placeholder="Référence / pièce (facultatif)" value={f.source_ref} onChange={(e) => setF({ ...f, source_ref: e.target.value })} />
        </div>
        <div className="actbar"><span style={{ marginLeft: "auto" }} /><button className="ds-btn" disabled={busy === "add" || !f.content} onClick={submit}>{busy === "add" ? "…" : "Consigner"}</button></div>
      </div>
      <div className="card"><h3>Registre des exigences ({s.total || 0})</h3>
        {entries.length === 0 && <p className="spin">Aucune exigence consignée. La première entrée crée la base vivante.</p>}
        {entries.map((e: any) => { const [c, l] = BRS_STATUS[e.status] || ["is-unknown", e.status]; return (
          <div key={e.id} style={{ borderTop: "1px solid var(--line)", paddingTop: 10, marginTop: 10 }}>
            <div className="claim" style={{ marginBottom: 0 }}><span className={`ds-ts ${c}`}><span className="dot" />{l}</span>
              <div style={{ flex: 1 }}><div className="ttl">{e.content}</div><small>{[BRS_KIND[e.kind] || e.kind, "canal : " + (BRS_CHAN[e.channel] || e.channel), e.emitter ? "par " + e.emitter : null, (e.created_at || "").slice(0, 16).replace("T", " "), e.source_ref].filter(Boolean).join(" · ")}</small></div>
              <span className="row" style={{ gap: 6 }}>{e.status !== "locked" && <button className="toggle" disabled={busy === `l${e.id}`} onClick={() => act(onPatch(e.id, { status: "locked" }), `l${e.id}`)}>Verrouiller</button>}<button className="signout" style={{ padding: 0 }} onClick={() => act(onDel(e.id), `d${e.id}`)}>✕</button></span>
            </div>
            {token && pid && <AttachField token={token} projectId={pid} ownerKind="brs" ownerId={e.id} label="Pièces (PV, fichiers source)" />}
          </div>
        ); })}
      </div>
    </>
  );
}

/* ===================== TÂCHES & PRIORITÉS (W9 #226/#228) ===================== */
const PRIO: Record<string, [string, string]> = { p0: ["eleve", "P0"], p1: ["modere", "P1"], p2: ["faible", "P2"] };
const TSTATUS: Record<string, string> = { todo: "À faire", doing: "En cours", done: "Fait", blocked: "Bloqué" };
function Taches({ data, token, pid, onAdd, onPatch, onDel, onAddDep, onPredict }: any) {
  const [f, setF] = useState<any>({ title: "", priority: "p2", estimate_hours: "", due_date: "", assignee_user_id: "", is_quick_win: false });
  const [busy, setBusy] = useState("");
  const [pred, setPred] = useState<Record<number, any>>({});
  const [depFor, setDepFor] = useState<number | null>(null); const [depSel, setDepSel] = useState("");
  if (!data) return <p className="spin">Chargement…</p>;
  const tasks: any[] = data.tasks || []; const users: any[] = data.users || []; const s = data.summary || {};
  const submit = async () => { if (!f.title.trim()) return; setBusy("add"); try { await onAdd({ ...f, estimate_hours: f.estimate_hours ? Number(f.estimate_hours) : null, assignee_user_id: f.assignee_user_id ? Number(f.assignee_user_id) : null, due_date: f.due_date || null }); setF({ title: "", priority: f.priority, estimate_hours: "", due_date: "", assignee_user_id: f.assignee_user_id, is_quick_win: false }); } catch { } finally { setBusy(""); } };
  const act = async (p: Promise<any>, id: string) => { setBusy(id); try { await p; } catch { } finally { setBusy(""); } };
  const predict = async (id: number) => { setBusy("p" + id); try { const r = await onPredict(id); setPred((x) => ({ ...x, [id]: r })); } catch { } finally { setBusy(""); } };
  const addDep = async (id: number) => { if (!depSel) return; await act(onAddDep(id, Number(depSel)), "dep" + id); setDepFor(null); setDepSel(""); };
  const ordered = [...tasks].sort((a, b) => (a.priority > b.priority ? 1 : a.priority < b.priority ? -1 : 0) || ((a.status === "done" ? 1 : 0) - (b.status === "done" ? 1 : 0)));
  return (
    <>
      <div className="vh"><div className="row"><h2>Tâches &amp; priorités</h2><span className="badge live"><span className="d" />Opérationnel</span></div><p>On navigue par <b>priorité</b> (P0 / P1 / P2) et par <b>ce qui bloque</b>, pas par agenda. Le <b>planning Atelier</b> (multi-projet, Kanban + Gantt + collisions) vit dans <i>« Tous les projets »</i> — pour voir cette tâche dans le contexte de l&apos;atelier complet, repassez par là.</p></div>
      <div className="kpis">
        <div className="kpi"><div className="lab">P0 · bloquant</div><div className="num">{s.by_priority?.p0 || 0}</div></div>
        <div className="kpi"><div className="lab">Bloquées</div><div className="num">{s.blocked || 0}</div></div>
        <div className="kpi"><div className="lab">Quick wins</div><div className="num">{s.quick_wins || 0}</div></div>
        <div className="kpi"><div className="lab">Ouvertes</div><div className="num">{(s.total || 0) - (s.by_status?.done || 0)}</div></div>
      </div>
      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Nouvelle tâche</h3>
        <input className="fld" placeholder="Intitulé de la tâche" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} />
        <div className="g2">
          <select className="fld" value={f.priority} onChange={(e) => setF({ ...f, priority: e.target.value })}><option value="p0">P0 · bloquant</option><option value="p1">P1</option><option value="p2">P2</option></select>
          <input className="fld" type="number" placeholder="Estimation (h)" value={f.estimate_hours} onChange={(e) => setF({ ...f, estimate_hours: e.target.value })} />
          <input className="fld" type="date" value={f.due_date} onChange={(e) => setF({ ...f, due_date: e.target.value })} />
          <select className="fld" value={f.assignee_user_id} onChange={(e) => setF({ ...f, assignee_user_id: e.target.value })}><option value="">— assigner à —</option>{users.map((u) => <option key={u.id} value={u.id}>{u.name}</option>)}</select>
        </div>
        <div className="actbar"><label className="mono" style={{ display: "flex", alignItems: "center", gap: 7 }}><input type="checkbox" checked={f.is_quick_win} onChange={(e) => setF({ ...f, is_quick_win: e.target.checked })} /> Quick win</label><span style={{ marginLeft: "auto" }} /><button className="ds-btn" disabled={busy === "add" || !f.title} onClick={submit}>{busy === "add" ? "…" : "Ajouter"}</button></div>
      </div>
      <div className="card">
        <h3>Tâches ({tasks.length})</h3>
        {tasks.length === 0 && <p className="spin">Aucune tâche. Ajoutez-en une ci-dessus.</p>}
        {ordered.map((t) => { const [pc, pl] = PRIO[t.priority] || ["modere", t.priority]; const p = pred[t.id]; return (
          <div key={t.id} style={{ borderTop: "1px solid var(--line)", paddingTop: 8, marginTop: 8, opacity: t.status === "done" ? 0.6 : 1 }}>
            <div className="row-line" style={{ border: 0, padding: 0 }}>
              <span className={`lvl ${pc}`}>{pl}</span>
              <span className="grow"><span className="ttl">{t.title}{t.is_quick_win && <small style={{ display: "inline", color: "var(--ts-sourced)" }}> · quick win</small>}{t.is_blocked && t.status !== "done" && <small style={{ display: "inline", color: "var(--ts-conflict)" }}> · bloquée</small>}</span><small>{[TSTATUS[t.status], t.assignee ? "→ " + t.assignee : null, t.estimate_hours ? t.estimate_hours + " h" : null, t.due_date ? "éch. " + t.due_date : null, (t.blocked_by && t.blocked_by.length) ? "dépend de #" + t.blocked_by.join(", #") : null, p ? "≈ " + (p.prediction ?? "?") + " h prédit" : null].filter(Boolean).join(" · ")}</small></span>
              <span className="row" style={{ gap: 6 }}>
                <select className="fld" style={{ margin: 0, padding: "4px 6px", width: "auto" }} value={t.status} onChange={(e) => act(onPatch(t.id, { status: e.target.value }), "s" + t.id)}>{Object.entries(TSTATUS).map(([v, lb]) => <option key={v} value={v}>{lb}</option>)}</select>
                <button className="toggle" disabled={busy === "p" + t.id} onClick={() => predict(t.id)} title="Prédire la durée depuis l'historique de l'atelier">≈ h</button>
                {depFor === t.id ? <span className="row" style={{ gap: 4 }}><select className="fld" style={{ margin: 0, padding: "4px 6px", width: "auto" }} value={depSel} onChange={(e) => setDepSel(e.target.value)}><option value="">dépend de…</option>{tasks.filter((x) => x.id !== t.id).map((x) => <option key={x.id} value={x.id}>{x.title.slice(0, 24)}</option>)}</select><button className="toggle" disabled={!depSel} onClick={() => addDep(t.id)}>OK</button></span> : <button className="toggle" onClick={() => { setDepFor(t.id); setDepSel(""); }}>+ dép.</button>}
                <button className="signout" style={{ padding: 0 }} onClick={() => act(onDel(t.id), "d" + t.id)}>✕</button>
              </span>
            </div>
            {token && pid && <AttachField token={token} projectId={pid} ownerKind="task" ownerId={t.id} />}
          </div>
        ); })}
      </div>
    </>
  );
}

/* ===================== TEAM ===================== */
const ROLE_FR: Record<string, string> = { owner: "Propriétaire", member: "Membre", viewer: "Lecteur" };
function Team({ users, onAdd, onSetRole, hideTitle }: { users: any[] | null; onAdd?: (e: string, n: string, r: string) => Promise<string>; onSetRole?: (id: number, r: string) => Promise<void>; readOnly?: boolean; hideTitle?: boolean }) {
  const [inv, setInv] = useState(false); const [email, setEmail] = useState(""); const [role, setRole] = useState("member");
  const [busy, setBusy] = useState(false); const [newKey, setNewKey] = useState<string | null>(null);
  if (!users) return null;
  const add = async () => { if (!onAdd) return; setBusy(true); try { const k = await onAdd(email, email, role); setNewKey(k); setEmail(""); setInv(false); } catch { } finally { setBusy(false); } };
  return (
    <div style={{ marginTop: hideTitle ? 24 : 0 }}>
      {!hideTitle && (
        <div className="vh">
          <h2>Équipe de l&apos;atelier</h2>
          <p>
            Les <b>membres de votre atelier</b> avec un compte Aedifica (owner/member/viewer).
            {" "}<b>Pas les intervenants d&apos;un projet</b> (architectes externes, mandataires, entreprises) — ceux-ci se gèrent dans <i>Intervenants</i> à l&apos;intérieur de chaque projet, et peuvent y être invités en tant qu&apos;externes scopés.
          </p>
        </div>
      )}
      <div className="card">
        {hideTitle && <h3>Équipe ({users.length})</h3>}
        {users.map((u: any) => (
          <div className="member" key={u.id}><span className="grow"><span className="nm">{u.name}{u.is_you && <small style={{ display: "inline", color: "var(--mut)" }}> · vous</small>}</span><span className="em">{u.email}</span></span>
            {onSetRole ? <select value={u.role} disabled={u.is_you} onChange={(e) => onSetRole(u.id, e.target.value)}>{Object.entries(ROLE_FR).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select> : <span className="chip">{ROLE_FR[u.role] || u.role}</span>}
          </div>
        ))}
        {newKey && <div className="flash" style={{ margin: "12px 0 0" }}><b>Membre ajouté.</b> Clé à transmettre :<code>{newKey}</code><button className="signout" style={{ padding: 0 }} onClick={() => setNewKey(null)}>OK</button></div>}
        {onAdd && (inv ? (
          <div className="actbar" style={{ marginTop: 14 }}>
            <input className="fld" style={{ margin: 0, flex: 1 }} placeholder="e-mail du collaborateur" value={email} onChange={(e) => setEmail(e.target.value)} />
            <select className="fld" style={{ margin: 0, width: "auto" }} value={role} onChange={(e) => setRole(e.target.value)}>{Object.entries(ROLE_FR).map(([v, l]) => <option key={v} value={v}>{l}</option>)}</select>
            <button className="ds-btn" disabled={busy || !email} onClick={add}>{busy ? "…" : "Inviter"}</button>
          </div>
        ) : <button className="signout" style={{ padding: "10px 0 0" }} onClick={() => setInv(true)}>+ Inviter un collaborateur</button>)}
      </div>
    </div>
  );
}
