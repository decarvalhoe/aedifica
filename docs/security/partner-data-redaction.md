# Partner data redaction & handling limits

> Status: active for the R1B → R6 waves. Companion to
> [`project-data-privacy-checklist.md`](project-data-privacy-checklist.md).

Partner project material (demo transcripts, generated reports, adapter evidence
exports) can contain client-identifying and model-sensitive data. Before any
artifact leaves the local project folder — shared in an issue, a PR, a demo
recording — it must pass through the redaction pass (`pilot/redaction.py`).

## What the pass removes

The shareable copy replaces these with `[redacted]`:

- **Identifying names**: `client_name`, `owner_name`, `contact_name`, `author`,
  `participants`.
- **Contact data**: `email`, `phone`/`tel`, `address`, and any email or Swiss
  phone number found in free text.
- **Local file paths**: `local_path`, `file_path`, `absolute_path`, and any
  absolute local path found in free text (e.g. `C:\Users\...`, `/Users/...`).
- **Precise location**: `gps`, `coordinates`.

## What the pass keeps (so the artifact still validates)

- Structural / validation fields: `schema_version`, `report_id`, `claim_id`,
  `source_id`, `evidence_id`, `state`/`claim_state`, `kind`, `phase_code`,
  `project_id`.
- Integrity hashes: `sha256`, `content_sha256`.
- Public regulatory references: EGRID, zone designations, article references,
  source titles.

## Handling limits (read before sharing anything)

1. **The pass is a safety net, not a guarantee.** It targets known shapes;
   review every shared artifact by eye. Free-text prose can still carry
   identifying context the regexes do not catch.
2. **The original stays local.** Redaction returns a *new* object; the source
   evidence under `project/<id>/evidence/` is never copied into shareable output
   and is never mutated by the pass.
3. **No client material in the repo.** Fixtures committed to the repository must
   be synthetic (see `pilot/fixtures/sensitive_artifact_fixture.json`).
4. **Model files are out of scope for sharing.** IFC/PLN/RVT exports may embed
   client geometry and metadata; share only derived, redacted summaries.

## Validation

`python pilot/validate_redaction.py` (also in CI) proves a fixture with sensitive
fields produces an artifact with zero residual sensitive findings while keeping
ids, claim states, source ids and hashes intact.
