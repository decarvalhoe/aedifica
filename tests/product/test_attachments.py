"""W11.B attachments — link OR upload, polymorphic owner.

Doctrine validated by the owner: Aedifica is the index + the rights + the
traceability, NOT a Dropbox bis. So a single Attachment table backs every
domain object (Document, BRS, Checklist, Task, Capture, Permit item) and
supports two modes: a link to the atelier's existing host (Drive/OneDrive/
…) or an inline-uploaded blob for the small cases.
"""
from __future__ import annotations

import io


def _project_with_doc(client, h, pid="ATT"):
    client.post("/api/projects", json={"project_id": pid, "name": pid, "commune": "Lausanne"}, headers=h)
    d = client.post(f"/api/projects/{pid}/documents",
                    json={"official_name": "Permis CAMAC 2026-001", "category": "permit"},
                    headers=h).json()["document"]
    return pid, d


def test_create_link_attachment_on_document(client, owner):
    h = owner["headers"]
    pid, d = _project_with_doc(client, h)
    r = client.post(f"/api/projects/{pid}/attachments/link",
                    json={"owner_kind": "document", "owner_id": str(d["id"]),
                          "title": "Plan PDF — Drive de l'atelier",
                          "url": "https://drive.google.com/file/d/abc123",
                          "provider": "gdrive"}, headers=h)
    assert r.status_code == 201, r.text
    a = r.json()["attachment"]
    assert a["kind"] == "link" and a["provider"] == "gdrive" and a["url"].endswith("abc123")
    # listing by owner returns it
    lst = client.get(f"/api/projects/{pid}/attachments?owner_kind=document&owner_id={d['id']}", headers=h).json()
    assert len(lst["attachments"]) == 1 and lst["attachments"][0]["title"].startswith("Plan PDF")


def test_create_upload_attachment_and_download(client, owner, tmp_path, monkeypatch):
    h = owner["headers"]
    pid, d = _project_with_doc(client, h, "ATT2")
    monkeypatch.setenv("AEDIFICA_UPLOAD_ROOT", str(tmp_path))
    payload = b"PDF-1.4 fake plan content " * 50
    files = {"file": ("plan.pdf", io.BytesIO(payload), "application/pdf")}
    data = {"owner_kind": "document", "owner_id": str(d["id"]),
            "title": "Plan local", "note": "petit fichier"}
    r = client.post(f"/api/projects/{pid}/attachments/upload", data=data, files=files, headers=h)
    assert r.status_code == 201, r.text
    a = r.json()["attachment"]
    assert a["kind"] == "upload" and a["size_bytes"] == len(payload) and a["sha256"]
    # download returns the bytes
    dl = client.get(a["download_path"], headers=h)
    assert dl.status_code == 200 and dl.content == payload


def test_upload_cap_enforced(client, owner, monkeypatch, tmp_path):
    h = owner["headers"]
    pid, d = _project_with_doc(client, h, "ATT3")
    monkeypatch.setenv("AEDIFICA_UPLOAD_ROOT", str(tmp_path))
    monkeypatch.setenv("AEDIFICA_UPLOAD_MAX_BYTES", "1024")
    # 1500 bytes — over the 1024-byte cap
    files = {"file": ("big.bin", io.BytesIO(b"\x00" * 1500), "application/octet-stream")}
    data = {"owner_kind": "document", "owner_id": str(d["id"]), "title": "trop gros"}
    r = client.post(f"/api/projects/{pid}/attachments/upload", data=data, files=files, headers=h)
    assert r.status_code == 413
    assert r.json()["detail"]["code"] == "TOO_LARGE"


def test_owner_kind_must_be_known_and_owner_must_exist(client, owner):
    h = owner["headers"]
    pid, d = _project_with_doc(client, h, "ATT4")
    # bad owner_kind
    bad = client.post(f"/api/projects/{pid}/attachments/link",
                      json={"owner_kind": "nope", "owner_id": "1",
                            "title": "x", "url": "https://x"}, headers=h)
    assert bad.status_code == 400 and bad.json()["detail"]["code"] == "BAD_OWNER_KIND"
    # owner that doesn't exist
    ghost = client.post(f"/api/projects/{pid}/attachments/link",
                        json={"owner_kind": "document", "owner_id": "9999",
                              "title": "x", "url": "https://x"}, headers=h)
    assert ghost.status_code == 404


def test_attachment_works_for_brs_checklist_task_capture(client, owner):
    """Same attachment plumbing for every domain object — verify each accepts a link."""
    h = owner["headers"]
    pid, d = _project_with_doc(client, h, "ATT5")
    client.post(f"/api/projects/{pid}/checklist/seed", json={"entry_phase": "11"}, headers=h)
    # build one of each owner kind
    brs = client.post(f"/api/projects/{pid}/brs", json={"content": "x", "channel": "phone"}, headers=h).json()["entry"]
    items = client.get(f"/api/projects/{pid}/checklist", headers=h).json()["items"]
    step = items[0]
    task = client.post(f"/api/projects/{pid}/tasks", json={"title": "T", "priority": "p1"}, headers=h).json()["task"]
    cap = client.post(f"/api/projects/{pid}/captures", json={"kind": "observation", "content": "obs"}, headers=h).json()["capture"]
    for kind, oid in [("brs", brs["id"]), ("checklist", step["id"]),
                      ("task", task["id"]), ("capture", cap["id"])]:
        r = client.post(f"/api/projects/{pid}/attachments/link",
                        json={"owner_kind": kind, "owner_id": str(oid),
                              "title": f"link for {kind}", "url": "https://x", "provider": "onedrive"},
                        headers=h)
        assert r.status_code == 201, f"{kind} attach failed: {r.text}"
    # the listing by kind = brs only returns the BRS one
    by_brs = client.get(f"/api/projects/{pid}/attachments?owner_kind=brs", headers=h).json()
    assert len(by_brs["attachments"]) == 1
    assert by_brs["attachments"][0]["owner_kind"] == "brs"


def test_delete_attachment_removes_payload(client, owner, tmp_path, monkeypatch):
    h = owner["headers"]
    pid, d = _project_with_doc(client, h, "ATT6")
    monkeypatch.setenv("AEDIFICA_UPLOAD_ROOT", str(tmp_path))
    files = {"file": ("note.txt", io.BytesIO(b"hello"), "text/plain")}
    data = {"owner_kind": "document", "owner_id": str(d["id"]), "title": "n"}
    a = client.post(f"/api/projects/{pid}/attachments/upload", data=data, files=files, headers=h).json()["attachment"]
    fp = a["file_ref"]
    import os
    assert os.path.exists(fp)
    r = client.delete(f"/api/projects/{pid}/attachments/{a['id']}", headers=h)
    assert r.status_code == 200
    assert not os.path.exists(fp)
