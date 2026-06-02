"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { DsTs, Wordmark } from "@/components/datum";

type Claim = { claim_id: string; title: string; state: string; value: unknown };
const DEMO_ID = "DEMO-LAUSANNE-PALUD";

export default function Workspace() {
  const [token, setToken] = useState<string>("");
  const [projects, setProjects] = useState<string[]>([]);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [active, setActive] = useState<string>("");
  const [msg, setMsg] = useState<string>("");

  useEffect(() => {
    const t = typeof window !== "undefined" ? window.localStorage.getItem("aedifica_token") || "" : "";
    if (t) setToken(t);
  }, []);

  async function refresh(t = token) {
    if (!t) return;
    try {
      const r = await api<{ projects: string[] }>("/projects", { token: t });
      setProjects(r.projects);
    } catch (e: any) {
      setMsg(e.message);
    }
  }
  useEffect(() => {
    if (token) refresh(token);
  }, [token]);

  async function bootstrap() {
    try {
      const r = await api<{ token: string }>("/orgs", { method: "POST", body: { org_name: "Atelier démo", user_email: "demo@aedifica.ch" } });
      window.localStorage.setItem("aedifica_token", r.token);
      setToken(r.token);
      setMsg("Org démo créée, token enregistré.");
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  async function createDemo() {
    try {
      await api("/projects", { method: "POST", token, body: { project_id: DEMO_ID, name: "Demo Lausanne Palud", commune: "Lausanne" } });
      await refresh();
      setMsg("Projet démo créé.");
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  async function open(pid: string) {
    setActive(pid);
    try {
      await api(`/projects/${pid}/intake`, { method: "POST", token, body: { query: "Place de la Palud, Lausanne", live: false } });
      const r = await api<{ claims: Claim[] }>(`/projects/${pid}/claims`, { token });
      setClaims(r.claims);
      setMsg(`Brief généré et persisté pour ${pid}.`);
    } catch (e: any) {
      setMsg(e.message);
    }
  }

  return (
    <>
      <header className="hdr">
        <Wordmark />
        <span className="eyebrow">Workspace · ArchiOS Suisse</span>
        <span className="eyebrow" style={{ marginLeft: "auto" }}>{token ? "● authentifié" : "non authentifié"}</span>
      </header>

      <main className="wrap">
        <section className="panel">
          <p className="eyebrow">Projet · route · contraintes sourcées</p>
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
              <li key={p} className="row">
                <span>{p}</span>
                <button className="ds-btn ghost" onClick={() => open(p)}>Ouvrir &amp; générer le brief</button>
              </li>
            ))}
          </ul>
        </section>

        {active && (
          <section className="panel" style={{ marginTop: 18 }}>
            <p className="sec">Claim review · {active}</p>
            {claims.length === 0 && <p className="mono">Aucune claim chargée.</p>}
            {claims.map((c) => (
              <div className="claim" key={c.claim_id}>
                <DsTs state={c.state} />
                <div>
                  <div className="ttl">{c.title}</div>
                  <div className="val">{c.value == null ? "Inconnu" : String(c.value)}</div>
                </div>
              </div>
            ))}
          </section>
        )}
      </main>
    </>
  );
}
