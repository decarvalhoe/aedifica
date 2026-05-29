"""Shared output trust contract for pilot renderers."""

PROVENANCE_TAGS = frozenset({"api", "RPGA", "calc", "assumption", "hyp", "unknown"})

FOOTERS = {
    "fr": (
        "Préparation sourcée par Aedifica, jamais une autorité.\n"
        "L'architecte vérifie les sources citées, hypothèses, conflits et faits propres au projet avant de s'y appuyer."
    ),
    "en": (
        "Preparation sourced by Aedifica. Not an authority.\n"
        "The architect verifies the cited sources, assumptions, conflicts, and project-specific facts before relying on it."
    ),
}


def render_footer(language="fr"):
    """Return the standardized non-authority footer for rendered pilot outputs."""
    return FOOTERS.get(language, FOOTERS["en"])


def print_footer(language="fr"):
    for line in render_footer(language).splitlines():
        print(line)
