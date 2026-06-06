"use client";
import { useEffect, useState } from "react";
import { api, apiUpload } from "../../lib/api";

// W11.B: shared *« pièces jointes »* control. Used inline under every domain
// row that can carry files (Documents, BRS, Permis pieces, Mémoire captures,
// Checklist steps, Tasks). Two modes per attachment: a *link* to the atelier's
// existing host (Drive, OneDrive, Dropbox, intranet) or an *upload* to the Fly
// volume (≤ 25 MB by default). The doctrine: Aedifica is the index + the
// rights + the traceability, NOT a Dropbox bis — so the default mode is link.

export type AttachOwnerKind = "document" | "brs" | "checklist" | "task" | "capture" | "permit";

type Attachment = {
  id: number;
  kind: "link" | "upload";
  title: string;
  url: string | null;
  provider: string;
  mime: string | null;
  size_bytes: number | null;
  created_by: string | null;
  created_at: string | null;
  download_path: string | null;
};

const PROVIDERS: { value: string; label: string }[] = [
  { value: "url", label: "Lien web" },
  { value: "gdrive", label: "Google Drive" },
  { value: "onedrive", label: "OneDrive" },
  { value: "dropbox", label: "Dropbox" },
  { value: "sharepoint", label: "SharePoint" },
  { value: "icloud", label: "iCloud" },
  { value: "other", label: "Autre" },
];

function humanSize(b: number | null): string {
  if (!b) return "";
  if (b < 1024) return `${b} o`;
  if (b < 1024 * 1024) return `${Math.round(b / 1024)} ko`;
  return `${(b / (1024 * 1024)).toFixed(1)} Mo`;
}

export function AttachField({
  token, projectId, ownerKind, ownerId, label = "Pièces jointes",
}: {
  token: string; projectId: string; ownerKind: AttachOwnerKind; ownerId: string | number; label?: string;
}) {
  const [rows, setRows] = useState<Attachment[] | null>(null);
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<"link" | "upload">("link");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [url, setUrl] = useState("");
  const [provider, setProvider] = useState("url");
  const [file, setFile] = useState<File | null>(null);
  const path = `/projects/${projectId}/attachments?owner_kind=${ownerKind}&owner_id=${ownerId}`;

  async function refresh() {
    try { setRows((await api<any>(path, { token })).attachments); }
    catch (e: any) { setErr(e?.message || "Chargement impossible"); }
  }
  useEffect(() => { refresh(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [projectId, ownerKind, ownerId]);

  async function addLink() {
    if (!title.trim() || !url.trim()) return;
    setBusy(true); setErr(null);
    try {
      await api(`/projects/${projectId}/attachments/link`, {
        method: "POST", token,
        body: { owner_kind: ownerKind, owner_id: String(ownerId), title, url, provider },
      });
      setTitle(""); setUrl(""); setOpen(false); await refresh();
    } catch (e: any) { setErr(e?.message || "Échec"); }
    finally { setBusy(false); }
  }
  async function addUpload() {
    if (!file || !title.trim()) return;
    setBusy(true); setErr(null);
    try {
      const fd = new FormData();
      fd.append("owner_kind", ownerKind);
      fd.append("owner_id", String(ownerId));
      fd.append("title", title);
      fd.append("file", file);
      await apiUpload(`/projects/${projectId}/attachments/upload`, fd, token);
      setTitle(""); setFile(null); setOpen(false); await refresh();
    } catch (e: any) { setErr(e?.message || "Upload échoué"); }
    finally { setBusy(false); }
  }
  async function remove(id: number) {
    try { await api(`/projects/${projectId}/attachments/${id}`, { method: "DELETE", token }); await refresh(); }
    catch (e: any) { setErr(e?.message || "Suppression échouée"); }
  }

  const list = rows || [];
  return (
    <div style={{ marginTop: 8 }}>
      <div className="row" style={{ gap: 6, flexWrap: "wrap", alignItems: "center" }}>
        <span className="mono" style={{ fontSize: 10, color: "var(--mut)" }}>{label} :</span>
        {list.length === 0 && !open && <span className="mono" style={{ fontSize: 10, color: "var(--mut)" }}>aucune</span>}
        {list.map((a) => (
          <span key={a.id} className="chip" style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
            <svg width="13" height="13" viewBox="0 0 24 24" aria-hidden="true" style={{ verticalAlign: "middle", marginRight: 4 }}>
              <use href={`/assets/functional-icons.svg#${a.kind === "link" ? "ic-source" : "ic-export"}`} />
            </svg>
            {a.kind === "link" && a.url
              ? <a href={a.url} target="_blank" rel="noreferrer" style={{ color: "var(--ink)", textDecoration: "underline" }}>{a.title}</a>
              : a.download_path
                ? <a href={a.download_path} target="_blank" rel="noreferrer" style={{ color: "var(--ink)", textDecoration: "underline" }}>{a.title}</a>
                : <span>{a.title}</span>}
            <small style={{ color: "var(--mut)" }}>
              {a.kind === "link" ? PROVIDERS.find((p) => p.value === a.provider)?.label || a.provider : humanSize(a.size_bytes)}
            </small>
            <button className="signout" style={{ padding: 0 }} title="Retirer" onClick={() => remove(a.id)}>×</button>
          </span>
        ))}
        {!open ? (
          <button className="toggle" style={{ padding: "3px 8px" }} onClick={() => setOpen(true)}>+ joindre</button>
        ) : (
          <span className="row" style={{ gap: 4 }}>
            <span className="row" style={{ gap: 2 }}>
              <button className={`toggle ${mode === "link" ? "on" : ""}`} style={{ padding: "3px 8px" }} onClick={() => setMode("link")}>Lien</button>
              <button className={`toggle ${mode === "upload" ? "on" : ""}`} style={{ padding: "3px 8px" }} onClick={() => setMode("upload")}>Upload</button>
            </span>
            <input className="fld" style={{ margin: 0, padding: "4px 8px", width: 160 }} placeholder="Titre" value={title} onChange={(e) => setTitle(e.target.value)} />
            {mode === "link" ? (
              <>
                <input className="fld" style={{ margin: 0, padding: "4px 8px", width: 220 }} placeholder="https://drive…" value={url} onChange={(e) => setUrl(e.target.value)} />
                <select className="fld" style={{ margin: 0, padding: "4px 8px", width: "auto" }} value={provider} onChange={(e) => setProvider(e.target.value)}>
                  {PROVIDERS.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                </select>
                <button className="toggle" style={{ padding: "3px 8px" }} disabled={busy || !title || !url} onClick={addLink}>OK</button>
              </>
            ) : (
              <>
                <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                <button className="toggle" style={{ padding: "3px 8px" }} disabled={busy || !title || !file} onClick={addUpload}>OK</button>
              </>
            )}
            <button className="signout" style={{ padding: 0 }} onClick={() => { setOpen(false); setErr(null); }}>annuler</button>
          </span>
        )}
        {err && <small style={{ color: "var(--ts-conflict)" }}>{err}</small>}
      </div>
    </div>
  );
}
