"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DsTs, Wordmark } from "@/components/datum";

type Claim = { claim_id: string; title: string; state: string; value: unknown };
const DEMO_ID = "DEMO-LAUSANNE-PALUD";
const TABS = ["prochain", "parcelle", "permis", "opposition", "conformite", "actions", "memoire"] as const;
type Tab = (typeof TABS)[number];
const TAB_LABEL: Record<Tab, string> = {
  prochain: "Prochaine étape", parcelle: "Parcelle", permis: "Permis", opposition: "Opposition",
  conformite: "Conformité", actions: "Actions · modèle", memoire: "Mémoire",
};

export default function Workspace() {
  const [token, setToken] = useState("");
  const [projects, setProjects] = useState<string[]>([]);
  const [active, setActive] = useState("");
  const [tab, setTab] = useState<Tab>("prochain");
  const [data, setData] = useState<Record<string, any>>({});
  const [msg, setMsg] = useState("");

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("aedifica_token") || "" : "";
    if (t) setToken(t);
  }, []);
  useEffect(() => { if (token) refresh(token); }, [token]);

  async function refresh(t = token) {
    try { setProjects((await api<{ projects: string[] }>("/projects", { token: t })).projects); }
    catch (e: any) { setMsg(e.message); }
  }
  async function bootstrap() {
    try {
      const r = await api<{ token: string }>("/orgs", { method: "POST", body: { org_name: "Atelier démo", user_email: "demo@aedifica.ch" } });
      localStorage.setItem("aedifica_token", r.token); setToken(r.token); setMsg("Org démo créée.");
    } catch (e: any) { setMsg(e.message); }
  }
  async function createDemo() {
    try { await api("/projects", { method: "POST", token, body: { project_id: DEMO_ID, name: "Demo Lausanne Palud", commune: "Lausanne" } }); await refresh(); setMsg("Projet démo créé."); }
    catch (e: any) { setMsg(e.message); }
  }
  async function openProject(pid: string) {
    setActive(pid); setTab("prochain"); setData({});
    try {
      await api(`/projects/${pid}/intake`, { method: "POST", token, body: { query: "Place de la Palud, Lausanne", live: false } });
      await load("prochain", pid);
      setMsg(`Brief généré pour ${pid}.`);
    } catch (e: any) { setMsg(e.message); }
  }
  async function load(t: Tab, pid = active) {
    setTab(t);
    if (data[t] || t === "actions") return;
    try {
      const r =
        t === "prochain" ? (await api<any>(`/projects/${pid}/next-step`, { token })).steps
        : t === "parcelle" ? (await api<any>(`/projects/${pid}/claims`, { token })).claims
        : t === "permis" ? (await api<any>(`/projects/${pid}/permit`, { token })).permit
        : t === "opposition" ? (await api<any>(`/projects/${pid}/opposition`, { token })).opposition
        : t === "conformite" ? (await api<any>(`/projects/${pid}/compliance`, { token })).compliance
        : { unknowns: (await api<any>(`/projects/${pid}/memory/unknowns`, { token })).unknowns, changes: (await api<any>(`/projects/${pid}/memory/changes`, { token })).changes };
      setData((d) => ({ ...d, [t]: r }));
    } catch (e: any) { setMsg(e.message); }
  }

  return (
    <>
      <header className="hdr">
        <Wordmark />
        <span className="eyebrow">ArchiOS Suisse · workspace</span>
        <span className="eyebrow" style={{ marginLeft: "auto" }}>{token ? "● authentifié" : "non authentifié"}</span>
      </header>

      <main className="wrap">
        <section className="panel">
          <p className="eyebrow">Moteur + mémoire + API d&apos;action · pas une autorité</p>
          <h1 className="display">Workspace projet</h1>
          <div className="row" style={{ marginTop: 14 }}>
            {!token && <button className="ds-btn" onClick={bootstrap}>Créer une org démo</button>}
            {token && <button className="ds-btn" onClick={createDemo}>Créer le projet démo</button>}
            {token && <button className="ds-btn ghost" onClick={() => refresh()}>Rafraîchir</button>}
          </div>
          {msg && <p className="mono" style={{ marginTop: 12 }}>{msg}</p>}
        </section>

        <section className="panel" style={{ marginTop: 18 }}>
          <p className="sec">Projets ({projects.length})</p>
          <ul className="list">
            {projects.length === 0 && <li className="mono">Aucun projet — créez le projet démo.</li>}
            {projects.map((p) => (
              <li key={p} className="row"><span>{p}</span>
                <button className="ds-btn ghost" onClick={() => openProject(p)}>Ouvrir &amp; générer le brief</button></li>
            ))}
          </ul>
        </section>

        {active && (
          <section className="panel" style={{ marginTop: 18 }}>
            <div className="tabs">
              {TABS.map((t) => <button key={t} className={`tab ${tab === t ? "active" : ""}`} onClick={() => load(t)}>{TAB_LABEL[t]}</button>)}
            </div>
            <div style={{ paddingTop: 18 }}>
              {tab === "prochain" && <NextStep steps={data.prochain} />}
              {tab === "parcelle" && <Claims claims={data.parcelle} />}
              {tab === "permis" && <Permit d={data.permis} />}
              {tab === "opposition" && <Opposition d={data.opposition} />}
              {tab === "conformite" && <Compliance d={data.conformite} />}
              {tab === "actions" && <Actions token={token} pid={active} />}
              {tab === "memoire" && <Memory d={data.memoire} />}
            </div>
          </section>
        )}
      </main>
    </>
  );
}

function NextStep({ steps }: { steps?: any[] }) {
  if (!steps) return <p className="mono">Chargement…</p>;
  return (
    <>
      <p className="sec">Prochaine étape — recommandations sourcées (jamais une autorité)</p>
      {steps.length === 0 && <p className="mono">Aucune action en attente.</p>}
      {steps.map((s, i) => (
        <div className="claim" key={i}><DsTs state={s.state} />
          <div><div className="ttl">{s.title} <small style={{ display: "inline" }}>· {s.kind} · phase {s.phase}</small></div>
            {s.action && <div className="val" style={{ fontFamily: "var(--font-ui)", fontWeight: 400 }}>{s.action}</div>}</div></div>
      ))}
    </>
  );
}

function Actions({ token, pid }: { token: string; pid: string }) {
  const [caps, setCaps] = useState<any>(null);
  const [txn, setTxn] = useState<any>(null);
  const [ledger, setLedger] = useState<any[]>([]);
  const [msg, setMsg] = useState("");
  async function refreshLedger() { setLedger((await api<any>(`/projects/${pid}/ledger`, { token })).ledger); }
  useEffect(() => { (async () => { try { setCaps((await api<any>(`/adapters/archicad_json/capabilities`, { token })).capabilities); await refreshLedger(); } catch (e: any) { setMsg(e.message); } })(); }, []);
  async function dryRun() {
    try { const r = await api<any>(`/projects/${pid}/adapter/dry-run`, { method: "POST", token, body: { adapter_id: "archicad_json", operations: [{ op_id: "O1", kind: "set_property", target: "AC-SPACE-101", before: "", after: "office", undo: "restore" }] } }); setTxn(r.transaction); setMsg("Dry-run — aucune mutation. Plan prêt."); await refreshLedger(); }
    catch (e: any) { setMsg(e.message); }
  }
  async function approve() { try { await api(`/projects/${pid}/approvals`, { method: "POST", token, body: { scope: "adapter_execution", basis: "go" } }); setMsg("Approbation d'exécution tracée au ledger."); await refreshLedger(); } catch (e: any) { setMsg(e.message); } }
  async function execute() {
    if (!txn) { setMsg("Faites un dry-run d'abord."); return; }
    try { const r = await api<any>(`/projects/${pid}/adapter/execute`, { method: "POST", token, body: { transaction: txn } }); setMsg(r.executed ? "Exécuté + tracé au ledger." : `Bloqué : ${r.reason}`); await refreshLedger(); }
    catch (e: any) { setMsg(e.message); }
  }
  return (
    <>
      <p className="sec">Boucle agent → Archicad · dry-run → approbation → ledger</p>
      <p className="mono">Adapter archicad_json — transaction {caps?.transaction ? "supportée" : "—"} · mutation jamais sans approbation d&apos;exécution.</p>
      <div className="row" style={{ margin: "12px 0" }}>
        <button className="ds-btn" onClick={dryRun}>Dry-run</button>
        <button className="ds-btn ghost" onClick={approve}>Approuver l&apos;exécution</button>
        <button className="ds-btn ghost" onClick={execute}>Exécuter</button>
      </div>
      {msg && <p className="mono">{msg}</p>}
      {txn && <div className="claim"><DsTs state={txn.status === "dry_run" ? "computed" : "sourced"} /><div><div className="ttl">Transaction {txn.transaction_id}</div><div className="val">statut: {txn.status} · {txn.operation_count} op</div></div></div>}
      <p className="sec" style={{ marginTop: 14 }}>Ledger ({ledger.length})</p>
      {ledger.map((e, i) => (
        <div className="claim" key={i}><DsTs state={e.mutating ? "conflict" : e.event_type === "approval" ? "sourced" : "computed"} />
          <div><div className="ttl">{e.event_type}{e.mutating ? " · mutation" : ""}</div><div className="val">{e.summary}</div>{e.approval_scope && <small>scope: {e.approval_scope}</small>}</div></div>
      ))}
    </>
  );
}

function Memory({ d }: { d?: any }) {
  if (!d) return <p className="mono">Chargement…</p>;
  return (
    <>
      <p className="sec">Inconnues résiduelles ({d.unknowns.length})</p>
      {d.unknowns.map((c: any, i: number) => (
        <div className="claim" key={i}><DsTs state={c.state} /><div><div className="ttl">{c.title}</div>{c.next_action && <small>{c.next_action}</small>}</div></div>
      ))}
      <p className="sec" style={{ marginTop: 14 }}>Journal projet ({d.changes.length})</p>
      {d.changes.map((e: any, i: number) => (
        <div className="claim" key={i}><DsTs state={e.mutating ? "conflict" : "computed"} /><div><div className="ttl">{e.event_type}</div><div className="val">{e.summary}</div></div></div>
      ))}
    </>
  );
}

function Claims({ claims }: { claims?: Claim[] }) {
  if (!claims) return <p className="mono">Chargement…</p>;
  return (<><p className="sec">Contraintes parcelle</p>{claims.map((c) => (
    <div className="claim" key={c.claim_id}><DsTs state={c.state} /><div><div className="ttl">{c.title}</div><div className="val">{c.value == null ? "Inconnu" : String(c.value)}</div></div></div>
  ))}</>);
}

function Permit({ d }: { d?: any }) {
  if (!d) return <p className="mono">Chargement…</p>;
  return (
    <>
      <p className="sec">Complétude permis · {d.dossier_id}</p>
      <div className="claim"><DsTs state={d.ready_for_review ? "sourced" : "assumption"} />
        <div><div className="ttl">{d.ready_for_review ? "Dossier prêt pour revue" : `Dossier NON prêt — ${d.summary.required_blockers} blocker(s) requis`}</div><div className="val">état: {d.state}</div></div></div>
      {d.disclaimers?.map((x: string, i: number) => <p key={i} className="mono" style={{ borderLeft: "3px solid var(--accent)", paddingLeft: 10, margin: "8px 0" }}>{x}</p>)}
      {d.groups?.map((g: any, i: number) => (
        <div key={i}><p className="sec" style={{ marginTop: 14 }}>{g.actor} · {g.category}</p>
          {g.items.map((it: any, j: number) => (
            <div className="claim" key={j}><DsTs state={it.status} /><div><div className="ttl">{it.title}</div>{it.missing_message && (it.status === "missing" || it.status === "assumption") && <small>{it.missing_message}</small>}</div></div>
          ))}</div>
      ))}
    </>
  );
}

function Opposition({ d }: { d?: any }) {
  if (!d) return <p className="mono">Chargement…</p>;
  return (<><p className="sec">Radar d&apos;opposition — {d.overall} (score {d.score})</p><p className="mono">{d.disclaimer}</p>
    {d.signals?.map((s: any, i: number) => (
      <div className="claim" key={i}><span className={`lvl ${cls(s.level)}`}>{s.level}</span>
        <div><div className="ttl">{s.ground} <small style={{ display: "inline" }}>· {s.category} · {s.evidence_state}</small></div>
          <div className="val" style={{ fontFamily: "var(--font-ui)", fontWeight: 400 }}>{s.basis}</div></div></div>
    ))}</>);
}

function Compliance({ d }: { d?: any }) {
  if (!d) return <p className="mono">Chargement…</p>;
  const gate = (g: any, i: number) => (
    <div className="claim" key={i}><DsTs state={g.status === "satisfied" ? "sourced" : g.status === "unknown" ? "unknown" : "assumption"} />
      <div><div className="ttl">{g.title} <small style={{ display: "inline" }}>({g.domain} · {g.binding_type})</small></div>{g.next_action && <small>{g.next_action}</small>}</div></div>
  );
  return (<><p className="sec">Gates phase 33 · légal {d.summary.legal_blockers} blocker(s)</p>
    <p className="sec" style={{ marginTop: 14 }}>Obligations légales</p>{d.legal?.map(gate)}
    <p className="sec" style={{ marginTop: 14 }}>Conventions contractuelles (BIM)</p>{d.contractual?.map(gate)}</>);
}

function cls(s: string) { return (s || "").normalize("NFD").replace(/[̀-ͯ]/g, ""); }
