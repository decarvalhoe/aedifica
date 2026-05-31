# Language Policy

Aedifica is Swiss-first and multilingual, but the repository needs predictable defaults.

## Defaults

- Product/user-facing Swiss context docs may be in French.
- Architecture/spec/validator docs may be in English when it keeps contracts clearer.
- Canonical regulatory units must store language-neutral keys and renderings for FR/DE/IT when relevant.
- Source locators keep the language of the official source.

## Required For Regulatory Content

Every regulatory term that crosses languages should carry:

- canonical key;
- FR/DE/IT rendering when known;
- source refs;
- validity date;
- canton/adoption state where relevant.

See [`../architecture/multilingual-regulatory-graph.md`](../architecture/multilingual-regulatory-graph.md).
