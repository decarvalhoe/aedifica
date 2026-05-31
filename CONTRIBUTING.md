# Contributing

This repository is currently a product/research prototype. Contributions should keep the source-of-truth
contracts explicit and verifiable.

## Rules

- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Keep regulatory claims sourced or explicitly marked as assumptions/unknowns.
- Do not embed secrets, paid SIA/CRB text, or proprietary office documents.
- Do not make Aedifica an authority: outputs are preparation and evidence for human review.
- Add or update validators when introducing structured pilot assets.

## Checks

Before pushing:

```bash
python pilot/validate_packs.py
python pilot/validate_matrix.py
python pilot/validate_permit.py
python pilot/validate_compliance.py
python pilot/validate_research.py
python pilot/validate_memory.py
python pilot/validate_cost.py
python pilot/selfcheck.py
```

CI runs the same checks on `main`.

## Pull Requests

Each PR should state:

- issue covered;
- files changed;
- source/provenance impact;
- validation commands run;
- residual assumptions or production caveats.
