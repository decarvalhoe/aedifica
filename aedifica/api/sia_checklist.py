"""SIA checklist template — the parametric, **per-actor** step list seeded per project.

Grounded in the official SIA 112/102 sub-phases (see docs/strategy/architect-reality.md
§3) and the deep session reading (docs/strategy/session-2026-06-05-etienne-DEEP.md §3.2).

Key insight recovered in the deep re-analysis: the SIA process is **multi-actor**. Each
sub-phase carries deliverables owned by *different* actors — the maître d'ouvrage (client)
has formal *devoirs* (SIA 112 even has a phase 0 made exclusively of client prestations),
the mandataires/specialists deliver studies, the entreprises execute. So every step is
tagged with its **responsible actor**; filtering by actor yields the client's checklist,
a mandataire's checklist, etc., and the architect sees them in parallel. A non-architect
step still ``todo`` is an **external** devoir — and, past its phase, an external blocker.

A project is seeded at its entry phase; steps in earlier phases are flagged
``retroactive`` (back-filled when onboarding mid-process). The atelier then makes each step
parametric: todo / done / deferred / skipped.
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

# The responsible actor for a step. Everything that is not the atelier is "external"
# (the client and the mandataires/entreprises) — used to derive their own checklists and
# to surface external blockers (≠ atelier blockers).
ACTOR_LABEL = {
    "mo": "Maître d'ouvrage",
    "architecte": "Architecte / atelier",
    "mandataire": "Mandataire / spécialiste",
    "entreprise": "Entreprise",
}
ACTORS = tuple(ACTOR_LABEL)
EXTERNAL_ACTORS = ("mo", "mandataire", "entreprise")  # not the atelier

# (phase_code, actor, title) — exhaustive ordinary deliverables per sub-phase, by actor.
# Sources: feuille SIA section Vaud (Etienne) + SIA 102 prestations list + SIA 112 model.
TEMPLATE: list[tuple[str, str, str]] = [
    # 11 · Définition des objectifs — le client fournit, l'architecte traduit/cadre.
    ("11", "mo", "Fournir les besoins/rêves, le budget visé, le terrain et les délais souhaités"),
    ("11", "architecte", "Traduire les rêves en programme (besoins, surfaces, nombre de pièces)"),
    ("11", "architecte", "Évaluer le budget — conseils et scénarios de financement"),
    ("11", "architecte", "Récolter les données du terrain (ensoleillement, affectation, règlements, RDPPF/OEREB, protection des eaux, plan de quartier, exigences communales)"),
    ("11", "architecte", "Estimer les délais (de la planification à la réalisation)"),
    # 21 · Études préliminaires · faisabilité.
    ("21", "architecte", "Étude de faisabilité"),
    ("21", "architecte", "Recommander les types de mandataires nécessaires (thermicien, acousticien…)"),
    ("21", "architecte", "Cahier des charges sommaire — programme + estimation coûts/honoraires (ordre de grandeur)"),
    ("21", "architecte", "Récolte des données légales et environnementales"),
    ("21", "mo", "Signer le contrat SIA avec le mandataire principal"),
    # 22 · Choix des mandataires / concours.
    ("22", "architecte", "Procédure de choix des mandataires (concours SIA 142/143 si applicable)"),
    ("22", "mo", "Valider le choix des mandataires"),
    # 31 · Avant-projet.
    ("31", "mandataire", "Contraintes des mandataires intégrées (civil, CVCS, géotechnique…)"),
    ("31", "architecte", "Concept architectural — implantation, forme, matérialisation (bois/béton/métal/verre)"),
    ("31", "mandataire", "Structure porteuse et objectifs énergétiques définis"),
    ("31", "architecte", "Estimation sommaire des coûts (± 15 %)"),
    ("31", "architecte", "Calendrier général"),
    ("31", "mo", "Signer les contrats de mandataires"),
    # 32 · Projet de l'ouvrage.
    ("32", "mandataire", "Développement — calcul et dimensionnement des éléments et des techniques"),
    ("32", "architecte", "Direction de projet — organisation et coordination des mandataires"),
    ("32", "architecte", "Plans, coupes, façades à l'échelle d'autorisation + détails constructifs"),
    ("32", "architecte", "Choix des matériaux"),
    ("32", "architecte", "Devis général (± 10 %)"),
    # 33 · Autorisation / mise à l'enquête.
    ("33", "architecte", "Élaboration du dossier d'enquête / demande d'autorisation (CAMAC)"),
    ("33", "architecte", "Justificatifs énergie (SIA 380/1), incendie (AEAI), accessibilité (SIA 500)"),
    ("33", "architecte", "Démarches auprès des pouvoirs publics + services techniques (suivi administratif)"),
    ("33", "architecte", "Suivi des oppositions"),
    # 41 · Appel d'offres.
    ("41", "architecte", "Plans d'appel d'offres (échelle appropriée)"),
    ("41", "architecte", "Descriptif détaillé matériaux + construction (avec quantitatifs)"),
    ("41", "mandataire", "Intégration des propositions des spécialistes"),
    ("41", "architecte", "Lancement des appels d'offres"),
    ("41", "architecte", "Comparaison/analyse des offres + proposition d'adjudication"),
    ("41", "mo", "Adjudication des travaux et des fournitures"),
    ("41", "architecte", "Révision des coûts et des délais"),
    # 51 · Projet d'exécution.
    ("51", "mo", "Signer les contrats d'entreprises"),
    ("51", "architecte", "Plans d'exécution + mise au point des détails"),
    ("51", "entreprise", "Optimisations d'exécution proposées et intégrées"),
    ("51", "mo", "Choix définitif des matériaux et appareils (entente avec l'architecte)"),
    ("51", "architecte", "Calendrier définitif"),
    # 52 · Exécution / chantier.
    ("52", "architecte", "Coordination des mandataires, entreprises et fournisseurs"),
    ("52", "architecte", "Direction architecturale — concordance exécution ↔ conception"),
    ("52", "architecte", "Direction des travaux — surveillance, conduite, métrés"),
    ("52", "architecte", "Contrôle des coûts & délais + PV de chantier"),
    ("52", "entreprise", "Exécution des travaux conforme aux plans"),
    # 53 · Mise en service.
    ("53", "architecte", "Réception des travaux — séances + PV"),
    ("53", "entreprise", "Levée des défauts constatés"),
    ("53", "architecte", "Documentation de l'ouvrage (dossier conforme à l'exécution) remise au MO"),
    ("53", "architecte", "Décompte final"),
    # 61 · Exploitation.
    ("61", "entreprise", "Travaux de garantie (délai 2 ans)"),
    ("61", "architecte", "Mémoire du projet / suivi d'exploitation"),
]


def actors_by_phase() -> dict[str, list[str]]:
    """W21-5 — SIA-expected actors with deliverables, per sub-phase.

    Derived from TEMPLATE (the feuille SIA Vaud source), never declared
    separately — so the dashboard's « intervenants par phase » can't drift
    from the checklist it summarizes.
    """
    out: dict[str, list[str]] = {ph: [] for ph in PHASE_ORDER}
    for phase, actor, _title in TEMPLATE:
        if actor not in out[phase]:
            out[phase].append(actor)
    return out


def _rank(phase_code: str) -> int:
    try:
        return PHASE_ORDER.index(phase_code)
    except ValueError:
        return 0


def seed_rows(entry_phase: str = "11") -> list[dict]:
    """Return rows to insert for a project onboarded at ``entry_phase``.

    Steps in phases earlier than the entry phase are flagged retroactive (to back-fill).
    Each row carries its responsible ``actor`` so the per-actor checklists (client,
    mandataire…) and external-blocker detection derive directly from the seed.
    """
    entry_rank = _rank(entry_phase)
    rows: list[dict] = []
    for idx, (phase, actor, title) in enumerate(TEMPLATE):
        rows.append({
            "phase_code": phase,
            "actor": actor,
            "title": title,
            "order_index": idx,
            "is_retroactive": _rank(phase) < entry_rank,
        })
    return rows
