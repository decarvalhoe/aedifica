"""SIA checklist template — the parametric step list seeded per project.

Grounded in the official SIA 112/102 sub-phases (see docs/strategy/architect-reality.md
§3). A project is seeded from this template at its entry phase; steps belonging to
earlier phases are flagged ``retroactive`` (back-filled when onboarding mid-process).
The atelier then makes each step parametric: todo / done / deferred / skipped.
"""
from __future__ import annotations

# Official SIA sub-phase order (both referentials share this spine).
PHASE_ORDER = ["11", "21", "22", "31", "32", "33", "41", "51", "52", "53", "61"]

PHASE_LABEL = {
    "11": "Définition des objectifs", "21": "Études préliminaires · faisabilité",
    "22": "Choix des mandataires (concours)", "31": "Avant-projet", "32": "Projet de l'ouvrage",
    "33": "Autorisation / mise à l'enquête", "41": "Appel d'offres", "51": "Projet d'exécution",
    "52": "Exécution / chantier", "53": "Mise en service", "61": "Exploitation",
}

# (phase_code, title) — representative ordinary deliverables per sub-phase.
TEMPLATE: list[tuple[str, str]] = [
    ("11", "Énoncer les besoins du maître d'ouvrage (programme)"),
    ("11", "Cadre légal et budgétaire défini"),
    ("11", "Analyse du terrain — contraintes, RDPPF / OEREB"),
    ("11", "Estimation des délais"),
    ("21", "Étude de faisabilité"),
    ("21", "Recommandation des mandataires nécessaires"),
    ("22", "Procédure de choix des mandataires (concours SIA 142/143 si applicable)"),
    ("31", "Concept architectural — parti, implantation, matérialisation"),
    ("31", "Structure porteuse et objectifs énergétiques définis"),
    ("31", "Estimation sommaire des coûts (± 15 %)"),
    ("31", "Calendrier général + contrats de mandataires"),
    ("32", "Développement du projet — calcul et dimensionnement"),
    ("32", "Coordination des mandataires (interfaces de responsabilité)"),
    ("32", "Plans, coupes, façades à l'échelle d'autorisation"),
    ("32", "Devis général (± 10 %)"),
    ("33", "Dossier d'enquête / demande d'autorisation (CAMAC)"),
    ("33", "Justificatifs énergie (SIA 380/1), incendie (AEAI), accessibilité (SIA 500)"),
    ("33", "Suivi des oppositions"),
    ("41", "Plans et descriptifs d'appel d'offres (avec quantitatifs)"),
    ("41", "Lancement des appels d'offres"),
    ("41", "Comparaison des offres + proposition d'adjudication"),
    ("51", "Plans d'exécution + détails"),
    ("51", "Contrats d'entreprises"),
    ("52", "Direction des travaux — surveillance, métrés"),
    ("52", "PV de chantier + suivi des coûts / délais"),
    ("53", "Réception des travaux — PV, levée des défauts"),
    ("53", "Documentation de l'ouvrage (dossier conforme à l'exécution)"),
    ("61", "Décompte final + suivi de garantie (2 ans)"),
]


def _rank(phase_code: str) -> int:
    try:
        return PHASE_ORDER.index(phase_code)
    except ValueError:
        return 0


def seed_rows(entry_phase: str = "11") -> list[dict]:
    """Return rows to insert for a project onboarded at ``entry_phase``.

    Steps in phases earlier than the entry phase are flagged retroactive (to back-fill).
    """
    entry_rank = _rank(entry_phase)
    rows: list[dict] = []
    for idx, (phase, title) in enumerate(TEMPLATE):
        rows.append({
            "phase_code": phase,
            "title": title,
            "order_index": idx,
            "is_retroactive": _rank(phase) < entry_rank,
        })
    return rows
