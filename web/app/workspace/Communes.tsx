"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

// W22-2 — « Communes · référentiels » : la surface admin du cache partagé de
// référentiels communaux (CommunePack). Un pack se suit ici de la DEMANDE à la
// PROMOTION : registre des sources officielles (autorité, validité, révision),
// jobs d'ingestion tracés, promotion après revue humaine. Canonical-first :
// rien n'entre sans source d'autorité — la récolte automatisée est la couture
// NOMOS (W22-3, #320), ce panneau pilote le circuit existant.

const PACK_STATUS: Record<string, [string, string]> = {
  seed: ["is-unknown", "Demandé"],
  ingested: ["is-computed", "Ingéré · à promouvoir"],
  supported: ["is-sourced", "Actif"],
};
const JOB_STATUS: Record<string, string> = { requested: "demandé", done: "terminé" };

export function Communes({ token }: { token: string }) {
  const [packs, setPacks] = useState<any[] | null>(null);
  const [fresh, setFresh] = useState<any>(null);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [busy, setBusy] = useState("");
  // Request form.
  const [commune, setCommune] = useState("");
  const [canton, setCanton] = useState("");
  const [cantons, setCantons] = useState<{ canton: string; name: string }[]>([]);
  const [authority, setAuthority] = useState("");
  // Advanced manual-ingest form (one open at a time, per seed pack).
  const [ingFor, setIngFor] = useState<number | null>(null);
  const [ing, setIng] = useState<any>({ version: "", source_authority: "", valid_as_of: "", review_due: "", zones: "" });

  async function load() {
    try { setPacks((await api<any>("/communes", { token })).communes || []); }
    catch (e: any) { setErr(e.message || "Chargement impossible."); }
  }
  useEffect(() => {
    load();
    api<any>("/jurisdictions/freshness?country=CH", {}).then(setFresh).catch(() => {});
    api<any>("/jurisdictions/regions?country=CH", {}).then((r) => setCantons(r.regions || [])).catch(() => {});
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [token]);

  async function request() {
    if (!commune.trim() || !canton) return;
    setBusy("req"); setErr(""); setMsg("");
    try {
      await api("/communes", { method: "POST", token, body: { commune: commune.trim(), canton, source_authority: authority.trim() || undefined } });
      setMsg(`Demande enregistrée pour ${commune.trim()} (${canton}) — pack en statut « Demandé », job tracé.`);
      setCommune(""); setAuthority("");
      await load();
    } catch (e: any) { setErr(e.message || "Demande impossible."); }
    finally { setBusy(""); }
  }

  async function promote(id: number) {
    setBusy(`p${id}`); setErr(""); setMsg("");
    try {
      await api(`/communes/${id}/promote`, { method: "POST", token });
      setMsg("Pack promu — il devient la version de référence exploitable de la commune.");
      await load();
    } catch (e: any) { setErr(e.message || "Promotion impossible."); }
    finally { setBusy(""); }
  }

  // W22-2b — withdraw a request scaffold (seed only; the server refuses
  // anything ingested/supported — referential versions are immutable).
  async function withdraw(id: number) {
    setBusy(`w${id}`); setErr(""); setMsg("");
    try {
      await api(`/communes/${id}`, { method: "DELETE", token });
      setMsg("Demande retirée.");
      await load();
    } catch (e: any) { setErr(e.message || "Retrait impossible."); }
    finally { setBusy(""); }
  }

  async function ingest(pack: any) {
    setBusy(`i${pack.id}`); setErr(""); setMsg("");
    try {
      let zones: any;
      try { zones = JSON.parse(ing.zones || "{}"); }
      catch { throw new Error("Zones illisibles — JSON attendu, ex. {\"Zone village\": {\"ius\": 0.4}}."); }
      await api(`/communes/${pack.id}/ingest`, {
        method: "POST", token,
        body: { version: ing.version.trim(), zones, source_authority: ing.source_authority.trim(), valid_as_of: ing.valid_as_of.trim(), review_due: ing.review_due.trim(), sources: [] },
      });
      setMsg(`Version ${ing.version.trim()} ingérée pour ${pack.commune} — à promouvoir après revue.`);
      setIngFor(null); setIng({ version: "", source_authority: "", valid_as_of: "", review_due: "", zones: "" });
      await load();
    } catch (e: any) { setErr(e.message || "Ingestion impossible."); }
    finally { setBusy(""); }
  }

  const canIngest = ing.version.trim() && ing.source_authority.trim() && ing.valid_as_of.trim() && ing.review_due.trim();
  return (
    <>
      <div className="vh"><div className="row"><h2>Communes · référentiels officiels</h2><span className="badge live"><span className="d" />Opérationnel</span></div>
        <p>Le cache partagé des règlements communaux, <b>capitalisé entre projets</b>. Un pack se suit de la <b>demande</b> à la <b>promotion</b> (revue humaine) — rien n&apos;entre sans source d&apos;autorité. La récolte automatisée arrive par la couture NOMOS (W22-3).</p>
      </div>
      {fresh?.snapshot_date && (
        <div className="banner" data-testid="ofs-freshness">
          <b>Registre des communes : OFS</b> · {fresh.n_communes?.toLocaleString?.() || fresh.n_communes} communes · instantané du {fresh.snapshot_date} · <span className="mono" style={{ fontSize: 11 }}>{fresh.source}</span>
        </div>
      )}
      <div className="card" style={{ marginBottom: 14 }}>
        <h3>Demander l&apos;ingestion d&apos;une commune</h3>
        <div className="g2">
          <input className="fld" placeholder="Commune (ex. Vevey)" value={commune} onChange={(e) => setCommune(e.target.value)} />
          <select className="fld" value={canton} onChange={(e) => setCanton(e.target.value)}>
            <option value="">— Canton —</option>
            {cantons.map((c) => <option key={c.canton} value={c.canton}>{c.canton} · {c.name}</option>)}
          </select>
          <input className="fld" placeholder="Autorité source (optionnel — ex. Commune de Vevey / géoportail VD)" value={authority} onChange={(e) => setAuthority(e.target.value)} />
        </div>
        <div className="actbar"><span style={{ marginLeft: "auto" }} /><button className="ds-btn" disabled={!commune.trim() || !canton || busy === "req"} onClick={request}>{busy === "req" ? "…" : "Demander l'ingestion"}</button></div>
      </div>
      {msg && <div className="banner ok" data-testid="communes-ok">{msg}</div>}
      {err && <div className="banner bad" data-testid="communes-err">{err}</div>}
      <div className="card" data-testid="packs-list">
        <h3>Packs ({(packs || []).length})</h3>
        {packs === null && <p className="spin">Chargement…</p>}
        {packs !== null && packs.length === 0 && <p className="spin">Aucun pack — demandez l&apos;ingestion d&apos;une première commune ci-dessus.</p>}
        {(packs || []).map((p) => {
          const [c, l] = PACK_STATUS[p.status] || ["is-unknown", p.status];
          return (
            <div key={p.id} style={{ borderTop: "1px solid var(--line)", paddingTop: 11, marginTop: 11 }} data-testid={`pack-${p.id}`}>
              <div className="row-line" style={{ border: 0, padding: 0 }}>
                <span className={`ds-ts ${c}`}><span className="dot" />{l}</span>
                <span className="grow">
                  <span className="ttl">{p.commune} ({p.canton}) · <span className="mono" style={{ fontSize: 12 }}>{p.version}</span>{p.nomos && <span className="ds-ts is-decision" style={{ marginLeft: 8 }}><span className="dot" />Feed NOMOS</span>}</span>
                  <small>{[p.source_authority, p.valid_as_of ? `valide au ${p.valid_as_of}` : null, p.review_due ? `révision ${p.review_due}` : null, p.n_zones ? `${p.n_zones} zone(s)` : null].filter(Boolean).join(" · ") || "—"}</small>
                </span>
                <span className="row" style={{ gap: 6 }}>
                  {p.status === "seed" && <button className="toggle" onClick={() => { setIngFor(ingFor === p.id ? null : p.id); setIng({ version: "", source_authority: p.source_authority || "", valid_as_of: "", review_due: "", zones: "" }); }}>{ingFor === p.id ? "Fermer" : "Ingestion manuelle…"}</button>}
                  {p.status === "seed" && <button className="signout" style={{ padding: 0 }} disabled={busy === `w${p.id}`} onClick={() => withdraw(p.id)}>{busy === `w${p.id}` ? "…" : "Retirer la demande"}</button>}
                  {p.status === "ingested" && <button className="toggle" disabled={busy === `p${p.id}`} onClick={() => promote(p.id)}>{busy === `p${p.id}` ? "…" : "Promouvoir"}</button>}
                </span>
              </div>
              {(p.jobs || []).map((j: any) => (
                <small key={j.id} className="mono" style={{ display: "block", color: "var(--mut)", fontSize: 11, marginTop: 4 }}>
                  job #{j.id} · {JOB_STATUS[j.status] || j.status}{j.requested_at ? ` · ${j.requested_at}` : ""}{j.n_sources ? ` · ${j.n_sources} source(s)` : ""}{j.notes ? ` — ${j.notes}` : ""}
                </small>
              ))}
              {ingFor === p.id && (
                <div className="card" style={{ marginTop: 8, borderLeft: "3px solid var(--ts-computed)" }} data-testid={`ingest-${p.id}`}>
                  <p style={{ marginTop: 0 }}><b>Capture manuelle du règlement officiel</b> — toutes les métadonnées de provenance sont requises (pas de valeur fabriquée). Les zones : JSON <span className="mono">{"{\"Zone\": {\"ius\": …}}"}</span>.</p>
                  <div className="g2">
                    <input className="fld" placeholder="Version (ex. vevey-rpga-2026-06)" value={ing.version} onChange={(e) => setIng({ ...ing, version: e.target.value })} />
                    <input className="fld" placeholder="Autorité source (ex. Commune de Vevey)" value={ing.source_authority} onChange={(e) => setIng({ ...ing, source_authority: e.target.value })} />
                    <input className="fld" placeholder="Valide au (ex. 2026-06-01)" value={ing.valid_as_of} onChange={(e) => setIng({ ...ing, valid_as_of: e.target.value })} />
                    <input className="fld" placeholder="Révision due (ex. 2026-12-01)" value={ing.review_due} onChange={(e) => setIng({ ...ing, review_due: e.target.value })} />
                  </div>
                  <textarea className="fld" rows={3} style={{ width: "100%", fontFamily: "var(--font-mono)", fontSize: 12 }} placeholder='{"Zone village": {"ius": 0.4, "hauteur_max_m": 9}}' value={ing.zones} onChange={(e) => setIng({ ...ing, zones: e.target.value })} />
                  <div className="row" style={{ gap: 6, marginTop: 8 }}>
                    <button className="ds-btn" disabled={!canIngest || busy === `i${p.id}`} onClick={() => ingest(p)}>{busy === `i${p.id}` ? "…" : "Ingérer cette version"}</button>
                    <button className="ds-btn ghost" onClick={() => setIngFor(null)}>Annuler</button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}
