# Release Checklist

Before tagging or opening a release PR:

- Run `python tests/contracts/run_contracts.py`.
- Run `python pilot/selfcheck.py`.
- Confirm GitHub Actions CI is green on the release branch.
- Confirm no direct push to `main`; use PR review.
- Confirm generated reports include source refs, unknowns and trust footer.
- Confirm privacy checklist has no blocker for fixture or project data.
