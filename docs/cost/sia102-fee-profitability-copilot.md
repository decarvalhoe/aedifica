# SIA 102 Fee And Profitability Copilot

Issue: #29  
Fixture: `pilot/cost/sia102_fee_sample.json`  
Validator: `pilot/validate_cost.py`

## Purpose

Aedifica should help an office see whether a mandate is economically coherent before unpaid work accumulates.
The first copilot contract estimates hours/fees, flags absorbed special prestations, and ties them to phases
and project memory.

## Source Boundary

SIA 102 is a professional standard. Aedifica stores metadata and workflow contracts, but it must not hardcode
paid SIA tables, coefficients or proprietary details. Office-provided licensed factors can be used inside a
project, with provenance and assumptions logged.

Public metadata anchor:

- SIA 102:2020 product page: <https://shop.sia.ch/normenwerk/architekt/102_2020_f/F/Product/>

## Supported Fee Methods

- Legacy cost-determinant formula: accepted as an office-provided method, not hardcoded.
- Hour model `H = T x h`: default pilot method, where estimated hours and hourly rate are explicit.

## Demo Acceptance

The sample mandate includes:

- estimated hours;
- estimated CHF fee;
- target margin;
- special prestations with pricing status;
- absorbed-prestation flags for unpriced fire-safety coordination and opposition response support.

`pilot/validate_cost.py` also exposes a small profitability cockpit object and HTML renderer showing estimated
fee, absorbed cost, margin risk and assumptions.

Run:

```bash
python pilot/validate_cost.py
```

The validator fails if hours/fee/rate/margin are missing, if no special prestation is declared, or if no
absorbed-prestation flag exists.
