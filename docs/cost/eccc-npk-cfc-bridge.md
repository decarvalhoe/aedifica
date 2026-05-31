# eCCC / NPK-CAN / CFC Bridge

Issue: #30  
Fixture: `pilot/cost/quantity_taxonomy_bridge.json`  
Validator: `pilot/validate_cost.py`

## Purpose

Aedifica should not replace Messerli, SORBA or CRB workflows. It should prepare and reconcile project
quantities, assumptions and mappings before handing them to mature Swiss tendering tools.

## Sources Checked

- CRB IfA18 / CRBX exchange: <https://public.crb.ch/Stories/IfA18.html>
- CRB CAN/NPK information 2026: <https://www.crb.ch/_Resources/Persistent/7/b/7/f/7b7f870a41996ec47d09b5c13a66a705dd7f7bf6/NPK_Information_2026_FR_digital.pdf>
- CRB home / standards context: <https://www.crb.ch/>

Checked on 2026-05-31.

## Bridge Contract

Each quantity row must preserve:

- source/version;
- quantity and unit;
- eCCC code;
- CFC code;
- NPK/CAN draft hint;
- assumptions and unresolved lookup status.

NPK/CAN positions remain draft until selected and validated in a licensed CRB-compatible workflow.

## CRBX Round-Trip Demo

The validator builds an in-memory `.crbx`-style ZIP with:

- `manifest.json`;
- `exchange.e1s`.

It parses the package back and verifies that row IDs, source refs and taxonomy mappings survive.

```bash
python pilot/validate_cost.py
```
