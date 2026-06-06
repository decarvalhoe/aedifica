# Wave 14 — Vérité UX : dire la vérité, distinguer ce qui est mêlé, brancher ce qui est promis

## Pourquoi cette Wave

Retour utilisateur après W13 — bugs et dettes UX dont les pires :

1. **Ingestion commune ment** — « en queue » alors qu'aucun worker ne tourne. La demande reste à `seed` indéfiniment et l'utilisateur croit que ça travaille.
2. **Mémoire / Copilote / Foresight** disent des choses incompréhensibles (« endpoint Archicad », « pas assez de comparables »).
3. **Équipe sémantique floue** — un pêle-mêle où on ne sait pas qui est dans l'atelier, qui est dans le projet, qui est intervenant.
4. **Permis sans documents attachés** — le bouton « Fournir » bascule un état sans pouvoir lier le vrai PDF.
5. **Conformité sans lien vers les règlements** — devrait pointer vers les textes officiels + permettre d'attacher la pièce remplie.
6. **Documents / BRS / Intervenants** — pas d'import en lot.
7. **Coordination** — toute la mise en page à revoir.
8. **Gantt inutilisable** — écrasé, illisible à toute taille.
9. **Atelier · multi-projet liste** — OK pour 5 items, pas pour 100.
10. **AttachField collé au texte** — petits problèmes d'espacement partout.

## Doctrine W14

- **Ne pas mentir.** Quand quelque chose ne marche pas (ingestion), le dire honnêtement. Quand on attend une action humaine, l'expliquer.
- **Séparer ce qui est mêlé.** Équipe atelier ≠ intervenants projet ≠ membres avec compte. Chaque mot a un sens.
- **Brancher ce qui est promis.** Si on dit « connectez un endpoint Archicad », expliquer ce que c'est OU enlever la promesse.
- **Pas de surface vide.** Si Opposition/Chantier n'ont rien quand le projet est jeune, écrire ce qui les remplit et quand.
- **Concrétiser les seuils.** Au lieu de « pas assez de comparables », dire « il vous faut 5 tâches comparables, vous en avez 2 ».

## Tranches

### W14.A — Bugs visibles + clarté sémantique *(this PR)*
1. **Ingestion honnête** : backend retourne `required_inputs` + `job_age_days`. Front Terrain affiche un panneau « Demande consignée le X — pour rendre la commune exploitable, ces sources sont à capturer par un opérateur : [liste] ». Plus de « en queue » trompeur.
2. **Équipe atelier renommée + scopée** : copy explicite + lien vers Intervenants pour les acteurs projet.
3. **Intervenants — import depuis un projet voisin** : endpoint backend qui retourne les intervenants des autres projets de l'atelier matchant nom/email ; bouton frontend « Importer un intervenant déjà connu ».
4. **Foresight — seuils transparents** : la réponse expose les compteurs vs seuils par règle (`duration_min_comparables: 5, you_have: 2, by_phase: {...}`).
5. **AttachField espacement** : `marginTop` 14px + label sur sa propre ligne au lieu d'être collé en chip.

### W14.B — Documents partout
1. **Permis** : chaque pièce porte un AttachField (lien OU upload). « Fournir » → « Joindre la pièce » avec la possibilité immédiate d'attacher.
2. **Conformité** : pour chaque gate, un AttachField pour le document rempli ET un champ « Référence du texte officiel » (URL ou source canonique).
3. **Documents · sources** : bouton « Import en lot » (drop multiple files, valeurs par défaut).
4. **BRS · exigences** : import CSV (date, channel, content) + parsing d'email simple.

### W14.C — Reworks profonds
1. **Coordination** : redécouper en sections claires, virer le pêle-mêle.
2. **Mémoire** : header explicatif honnête sur ce qui va dedans (auto-journal + capture manuelle), retirer l'ambiguïté.
3. **Copilote** : remplacer le message d'endpoint Archicad par un guide pas-à-pas avec exemple OU masquer derrière un toggle « config avancée ».
4. **Opposition / Chantier** : empty-states qui expliquent ce qu'il leur faut pour se peupler.
5. **Gantt fix** : auto-fit, scroll horizontal, zoom in/out, dépendances visibles.
6. **Atelier multi-projet liste** : tri + filtre + pagination quand > 30 items.

## Garde-fou

Wave 14 ne touche pas aux engines (W12 Foresight stays intact, W11 attachments stays intact). Toutes les modifs sont du *vérité de surface* et du *câblage déjà disponible*.
