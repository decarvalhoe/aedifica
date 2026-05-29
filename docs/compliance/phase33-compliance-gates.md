# Phase 33 Compliance Gates

This contract models permit-readiness checks as explicit gates instead of generic advice. It separates legal or
authority-triggered obligations from project-conventional BIM requirements.

Product spec: [`../specs/mvp2-permit-dossier-assistant.md`](../specs/mvp2-permit-dossier-assistant.md).

## Files

- Gates: `pilot/compliance/ch_phase33_gates.json`
- Validator: `pilot/validate_compliance.py`

## Sources Checked

- Etat de Vaud, energy forms for authorization requests:
  <https://www.vd.ch/environnement/energie/formulaires-energie>
- Etat de Vaud, constructions and energy:
  <https://publication.vd.ch/publications/dgaic/aide-memoire/domaines-batiments/constructions-et-energie>
- ECA Vaud, fire-safety permit procedure:
  <https://www.eca-vaud.ch/collectivites-publiques/batiment/constructions-renovations/procedure-permis-de-construire/>
- Internal synthesis: `docs/strategy/architect-reality.md` section 5.

These sources were checked on 2026-05-29 and are recorded in the gates file with `valid_as_of`.

## Gate

```json
{
  "gate_id": "ENERGY-SIA-380-1-VD",
  "title": "Energy dossier and SIA 380/1 justification",
  "domain": "energy",
  "binding_type": "binding_law_when_applicable",
  "phase_code": "33",
  "blocking": true,
  "required_evidence": ["energy_form", "sia_380_1_calculation"]
}
```

## Binding Types

| Type | Meaning |
| --- | --- |
| `binding_law` | Direct legal obligation. |
| `binding_law_when_applicable` | Legal/authority obligation when the project triggers it. |
| `technical_norm_by_reference` | Technical norm required by authority, mandate, or professional responsibility. |
| `contractual_not_legal` | Project convention only; not a legal permit gate by itself. |

The pilot deliberately includes a BIM/digital-information gate with `contractual_not_legal`. This prevents the
product from treating BIM or SIA 2051 as a Swiss legal permit requirement.

## Validation

```bash
python pilot/validate_compliance.py
python pilot/selfcheck.py
```

The validator requires gates for energy, fire, accessibility, and structure, plus at least one
`contractual_not_legal` gate to prove the distinction is represented.

## Boundaries

- These gates are a permit-readiness checklist, not a legal opinion.
- Applicability depends on project type, use, size, authority requirements, and specialist mandates.
- The architect or mandated specialist remains responsible for confirming which gate is triggered.
