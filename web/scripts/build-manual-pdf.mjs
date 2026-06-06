// Generate the Aedifica manual as a PDF with the full Datum design identity.
// Runs Playwright's bundled Chromium against an inline HTML template that uses
// the same tokens (Datum DA) as the production app — surface, ink, datum red,
// Space Grotesk + IBM Plex Mono. Output: docs/manuals/aedifica-manuel-etienne.pdf.
//
// Usage (from repo root):
//   node scripts/manual/build-pdf.mjs
//
// Or with custom values:
//   AEDIFICA_URL=https://aedifica-demo.fly.dev \
//   AEDIFICA_LOGIN=etienne@carre-neuf.ch \
//   AEDIFICA_PWD=carre-neuf-2026 \
//   node scripts/manual/build-pdf.mjs
import { chromium } from "@playwright/test";
import { writeFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(__dirname, "..", "..");
const OUT = resolve(REPO, "docs", "manuals", "aedifica-manuel-etienne.pdf");

const URL = process.env.AEDIFICA_URL || "https://aedifica-demo.fly.dev";
const LOGIN = process.env.AEDIFICA_LOGIN || "etienne@carre-neuf.ch";
const PWD = process.env.AEDIFICA_PWD || "carre-neuf-2026";
const PROJECT = process.env.AEDIFICA_PROJECT || "Rehabilitation Bourg-Dessus, Lutry";
const VERSION = process.env.AEDIFICA_VERSION || "Wave 10 · multi-acteurs";
const DATE = new Date().toISOString().slice(0, 10);

const html = /* html */ `<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<title>Aedifica — Manuel · Atelier Carré-Neuf</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet" />
<style>
  /* Datum design tokens (mirrored from web/app/globals.css). */
  :root {
    --surface: #F3F1EC;
    --ink: #16171A;
    --accent: #C0392B;
    --line: rgba(22,23,26,0.14);
    --mute: rgba(22,23,26,0.62);
    --ts-sourced: #4F7B3A;
    --ts-computed: #7C6A2B;
    --ts-assume: #B7723A;
    --ts-unknown: #6A6F73;
    --ts-conflict: #C0392B;
    --ts-decision: #2C3E50;
  }
  @page {
    size: A4;
    margin: 0;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0;
    font-family: "Space Grotesk", "Inter", "Segoe UI", system-ui, sans-serif;
    color: var(--ink);
    background: var(--surface);
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .mono { font-family: "IBM Plex Mono", ui-monospace, monospace; letter-spacing: 0.01em; }
  .page {
    width: 210mm;
    height: 297mm;
    padding: 22mm 20mm;
    page-break-after: always;
    position: relative;
    display: flex;
    flex-direction: column;
  }
  .page:last-child { page-break-after: auto; }

  /* Page chrome — small top header except on the cover */
  .chrome {
    position: absolute;
    top: 12mm; left: 20mm; right: 20mm;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 9pt; color: var(--mute);
  }
  .chrome .word { font-weight: 600; letter-spacing: 0.04em; }
  .chrome .word .ae {
    display: inline-block; font-weight: 700; color: var(--accent);
    margin-right: 1px;
  }
  .chrome small { font-size: 8pt; }
  .footer {
    position: absolute;
    bottom: 12mm; left: 20mm; right: 20mm;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 8pt; color: var(--mute);
  }
  .footer .pageno { font-feature-settings: "tnum"; }

  /* ===== Cover ===== */
  .cover {
    background: var(--ink); color: var(--surface);
    display: flex; flex-direction: column; justify-content: center;
    padding: 30mm 22mm;
  }
  .cover .wordmark {
    font-size: 92pt; line-height: 1; font-weight: 600; letter-spacing: -0.02em;
    margin: 0 0 8mm 0;
  }
  .cover .wordmark .ae {
    color: var(--accent);
    font-weight: 700;
  }
  .cover .eyebrow {
    font-size: 11pt; letter-spacing: 0.18em; text-transform: uppercase;
    color: rgba(243,241,236,0.6); margin-bottom: 6mm;
  }
  .cover .sub {
    font-size: 22pt; font-weight: 400; line-height: 1.25;
    max-width: 130mm; margin: 4mm 0 18mm 0;
    border-left: 3px solid var(--accent); padding-left: 7mm;
  }
  .cover .who {
    font-size: 14pt; font-weight: 500; margin-top: auto;
  }
  .cover .who small {
    display: block; font-size: 9pt; font-weight: 400; color: rgba(243,241,236,0.55);
    margin-top: 2mm; letter-spacing: 0.02em;
  }
  .cover .ribbon {
    position: absolute; right: 0; top: 0; bottom: 0; width: 14mm;
    background: var(--accent);
  }
  .cover .footer { color: rgba(243,241,236,0.5); }

  /* ===== Section headings ===== */
  h2 {
    font-size: 24pt; font-weight: 600; letter-spacing: -0.015em;
    margin: 8mm 0 2mm 0;
    border-left: 3px solid var(--accent); padding-left: 6mm;
  }
  h2 .num {
    font-size: 10pt; color: var(--mute); font-weight: 400;
    display: block; letter-spacing: 0.16em; text-transform: uppercase;
    margin-bottom: 1.5mm;
  }
  h3 { font-size: 13pt; font-weight: 600; margin: 6mm 0 2mm 0; }

  p { font-size: 10.5pt; line-height: 1.55; margin: 0 0 3.5mm 0; }
  p.lead { font-size: 12pt; line-height: 1.5; color: var(--ink); }
  ul, ol { font-size: 10.5pt; line-height: 1.55; padding-left: 5mm; margin: 0 0 3mm 0; }
  ul li, ol li { margin: 0 0 1.5mm 0; }
  b { font-weight: 600; }

  /* Card */
  .card {
    background: rgba(255,255,255,0.55);
    border: 1px solid var(--line);
    border-radius: 4px;
    padding: 6mm 7mm;
    margin: 0 0 4mm 0;
  }
  .card h3 { margin-top: 0; }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }
  .grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 3mm; }

  /* Datum trust chip — same anatomy as in the app */
  .ts {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 8px 2px 6px;
    border: 1px solid var(--line); border-radius: 2px;
    font-size: 8.5pt; font-weight: 500; letter-spacing: 0.02em;
    background: rgba(255,255,255,0.6);
  }
  .ts .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--ts-unknown); display: inline-block; }
  .ts.sourced .dot { background: var(--ts-sourced); }
  .ts.computed .dot { background: var(--ts-computed); }
  .ts.assume .dot { background: var(--ts-assume); }
  .ts.conflict .dot { background: var(--ts-conflict); }
  .ts.decision .dot { background: var(--ts-decision); }

  /* Surface list (like the workspace row-line) */
  .row { display: flex; align-items: center; gap: 8px; padding: 2.5mm 0; border-bottom: 1px dashed var(--line); }
  .row:last-child { border-bottom: 0; }
  .row .ttl { font-size: 10pt; font-weight: 500; flex: 1; }
  .row small { color: var(--mute); font-size: 8.5pt; }

  /* Numbered steps */
  .steps { counter-reset: step; padding-left: 0; list-style: none; }
  .steps li {
    counter-increment: step; padding-left: 10mm; position: relative; margin: 0 0 4mm 0;
    font-size: 10.5pt; line-height: 1.5;
  }
  .steps li::before {
    content: counter(step); position: absolute; left: 0; top: 0;
    width: 7mm; height: 7mm; border-radius: 50%;
    background: var(--accent); color: var(--surface);
    font-weight: 600; font-size: 11pt; line-height: 7mm;
    text-align: center;
  }

  /* Phase rail (mini) */
  .rail { display: flex; gap: 2mm; margin: 4mm 0 5mm 0; flex-wrap: wrap; }
  .rail .ph {
    border: 1px solid var(--line); border-radius: 2px;
    padding: 2mm 3mm; font-size: 8pt; font-family: "IBM Plex Mono", monospace;
    background: rgba(255,255,255,0.55);
    display: inline-flex; flex-direction: column; min-width: 16mm;
  }
  .rail .ph b { font-size: 10pt; color: var(--ink); }
  .rail .ph.on { background: var(--ink); color: var(--surface); border-color: var(--ink); }
  .rail .ph.on b { color: var(--surface); }

  /* Excerpt table */
  table { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin: 2mm 0 4mm 0; }
  th, td { text-align: left; padding: 2mm 3mm; border-bottom: 1px solid var(--line); vertical-align: top; }
  th { font-weight: 600; font-size: 8.5pt; text-transform: uppercase; letter-spacing: 0.04em; color: var(--mute); }
  td b { font-weight: 600; }

  /* Quote / sidebar */
  .quote {
    border-left: 3px solid var(--accent);
    padding: 2mm 0 2mm 5mm;
    font-style: italic; font-size: 11pt; color: var(--ink);
    margin: 3mm 0 4mm 0;
  }
  .quote small { display: block; color: var(--mute); font-style: normal; margin-top: 1.5mm; font-size: 8.5pt; }

  /* Notice (guard-rail) */
  .notice {
    background: rgba(192, 57, 43, 0.06);
    border: 1px solid rgba(192, 57, 43, 0.35);
    border-radius: 2px;
    padding: 5mm 6mm;
    font-size: 10pt;
    margin: 4mm 0;
  }
  .notice b { color: var(--accent); }

  /* Credentials box (last page) */
  .creds {
    background: var(--ink); color: var(--surface);
    border-radius: 3px; padding: 6mm 7mm;
    font-family: "IBM Plex Mono", monospace; font-size: 10pt;
    margin: 4mm 0 6mm 0; letter-spacing: 0.01em;
  }
  .creds .lbl { color: rgba(243,241,236,0.55); display: inline-block; width: 38mm; }
  .creds .row { padding: 1.2mm 0; border: 0; }
</style>
</head>
<body>

<!-- ============ COVER ============ -->
<section class="page cover">
  <div class="ribbon"></div>
  <div class="eyebrow">ArchiOS Suisse · l'assistant de l'architecte</div>
  <h1 class="wordmark"><span class="ae">Æ</span>DIFICA</h1>
  <p class="sub">Manuel utilisateur — votre atelier opérationnel, par phase et par acteur.</p>
  <div class="who">
    Atelier Carré-Neuf · Etienne Piergiovanni
    <small>Édition ${VERSION} · ${DATE}</small>
  </div>
  <div class="footer">
    <span>aedifica-demo.fly.dev</span>
    <span>Manuel privé — ne pas diffuser</span>
  </div>
</section>

<!-- ============ 1 · À QUOI SERT AEDIFICA ============ -->
<section class="page">
  <div class="chrome"><span class="word"><span class="ae" style="color:var(--accent);">Æ</span> DIFICA</span> <small>1 · À quoi sert Aedifica</small></div>
  <h2><span class="num">Chapitre 1</span>À quoi sert Aedifica</h2>
  <p class="lead">Aedifica est l'<b>interface opérationnelle</b> de votre mandat. Pas un logiciel de dessin — un système qui structure ce qui se passe <i>autour</i> du dessin&nbsp;: les sources, les exigences, les intervenants, les devoirs de chacun, et les bloquants.</p>
  <p>La proposition de valeur tient en trois verbes — repris du carnet de séance&nbsp;:</p>
  <div class="grid3" style="margin-top:4mm;">
    <div class="card"><h3>Trier</h3><p style="margin:0;">Vos sources, vos exigences, vos décisions. Trois niveaux de validation&nbsp;: <i>canonique</i>, <i>indicatif</i>, <i>refusé</i> — vous êtes la référence finale.</p></div>
    <div class="card"><h3>Retrouver</h3><p style="margin:0;">Un projet repris en cours de route&nbsp;? Vous rejoignez à n'importe quelle phase, les étapes antérieures sont marquées rétroactives.</p></div>
    <div class="card"><h3>Transmettre</h3><p style="margin:0;">Vos mandataires et le maître d'ouvrage se connectent. Chacun voit sa part&nbsp;— pas le reste.</p></div>
  </div>
  <h3 style="margin-top:9mm;">Le contrat tacite</h3>
  <p>Aedifica <b>propose</b>, vous <b>validez</b>. Aucune décision n'est prise à votre place. Les sources sont sourcées ou inconnues, jamais inventées. L'IA n'est utilisée que pour la prédiction de durée (collision inter-projet) et le scan public&nbsp;— le reste est <i>du pur soft</i>.</p>
  <div class="notice"><b>Garde-fou.</b> L'architecte SIA reste la référence finale de validation systématique. Confidentialité&nbsp;: les documents marqués <i>confidentiels</i> sont traités selon la LPD et l'accès est restreint à l'atelier par défaut.</div>
  <div class="footer"><span class="mono">ÆDIFICA · Manuel utilisateur</span><span class="pageno">2</span></div>
</section>

<!-- ============ 2 · LE WORKSPACE EN UN COUP D'OEIL ============ -->
<section class="page">
  <div class="chrome"><span class="word"><span class="ae" style="color:var(--accent);">Æ</span> DIFICA</span> <small>2 · Le workspace en un coup d'œil</small></div>
  <h2><span class="num">Chapitre 2</span>Le workspace en un coup d'œil</h2>
  <p>La barre latérale gauche regroupe vos surfaces par bloc&nbsp;: <b>Pilotage</b>, <b>Coordination</b>, <b>Dossier réglementaire</b>, <b>Économie &amp; chantier</b>, <b>Atelier</b>. La barre du haut affiche la <i>phase rail</i> SIA — vous pouvez basculer le projet d'une sous-phase à l'autre d'un clic.</p>
  <div class="rail">
    <div class="ph"><span>11</span><b>Objectifs</b></div>
    <div class="ph"><span>21</span><b>Faisabilité</b></div>
    <div class="ph"><span>22</span><b>Mandataires</b></div>
    <div class="ph"><span>31</span><b>Avant-projet</b></div>
    <div class="ph on"><span>32</span><b>Projet</b></div>
    <div class="ph"><span>33</span><b>Autorisation</b></div>
    <div class="ph"><span>41</span><b>Offres</b></div>
    <div class="ph"><span>51</span><b>Exécution</b></div>
    <div class="ph"><span>52</span><b>Chantier</b></div>
    <div class="ph"><span>53</span><b>Mise en service</b></div>
  </div>
  <h3>Les cinq surfaces clés</h3>
  <div class="card"><b>① Coordination</b> — Point unique. <i>Qui doit quoi · où ça bloque · documents · ce qu'il reste à valider</i>. Le bon endroit pour démarrer chaque matin.</div>
  <div class="card"><b>② Checklist SIA</b> — Liste exhaustive issue de la feuille SIA Vaud officielle. Filtrable par <i>acteur</i> (vous, mandataire, entreprise, maître d'ouvrage).</div>
  <div class="card"><b>③ Tâches &amp; priorités</b> — Navigation P0/P1/P2 (pas un agenda). Dépendances, collision inter-projet, prédiction de durée à partir de votre historique.</div>
  <div class="card"><b>④ Documents &amp; sources</b> — Import local, versioning, validation 3 niveaux (canonique / indicatif / refusé), gestion d'accès par groupe ou personne, flag confidentiel (LPD).</div>
  <div class="card"><b>⑤ Exigences (BRS)</b> — La <i>base vivante de référence</i>&nbsp;: registre versionné des demandes du client, sourçage (téléphone, PV, e-mail, séance), émetteur attribué — votre traçabilité légale.</div>
  <div class="footer"><span class="mono">ÆDIFICA · Manuel utilisateur</span><span class="pageno">3</span></div>
</section>

<!-- ============ 3 · COORDINATION ============ -->
<section class="page">
  <div class="chrome"><span class="word"><span class="ae" style="color:var(--accent);">Æ</span> DIFICA</span> <small>3 · Coordination — qui doit quoi</small></div>
  <h2><span class="num">Chapitre 3</span>Coordination — qui doit quoi, où ça bloque</h2>
  <p class="lead">La page <b>Coordination</b> est le point unique du projet. Elle agrège, sur une seule vue, ce qui était auparavant éclaté sur quinze onglets et trois fichiers Excel.</p>
  <h3>Quatre cadrans</h3>
  <div class="grid2">
    <div class="card">
      <b>① Qui doit quoi</b>
      <p style="margin-top:2mm;">Les étapes <i>à faire</i> regroupées par acteur&nbsp;: maître d'ouvrage, atelier, mandataire, entreprise. Vous voyez immédiatement <i>ce que vous attendez de chacun</i>.</p>
      <div style="display:flex;gap:3mm;flex-wrap:wrap;margin-top:3mm;">
        <span class="ts decision"><span class="dot"></span>Maître d'ouvrage</span>
        <span class="ts sourced"><span class="dot"></span>Atelier</span>
        <span class="ts computed"><span class="dot"></span>Mandataire</span>
        <span class="ts assume"><span class="dot"></span>Entreprise</span>
      </div>
    </div>
    <div class="card">
      <b>② Où ça bloque</b>
      <p style="margin-top:2mm;">Deux colonnes&nbsp;: <i>en attente de l'extérieur</i> (le MO n'a pas fourni son budget, le géomètre n'a pas livré le plan…) et <i>atelier</i> (vos tâches bloquées par une dépendance).</p>
      <div style="display:flex;gap:3mm;margin-top:3mm;">
        <span class="ts conflict"><span class="dot"></span>Bloquants externes</span>
        <span class="ts assume"><span class="dot"></span>Bloquants atelier</span>
      </div>
    </div>
    <div class="card">
      <b>③ Documents</b>
      <p style="margin-top:2mm;">Les documents du projet triés par <i>statut de validation</i> — ceux <i>en attente</i> apparaissent en premier. Vous validez d'un clic&nbsp;: canonique, indicatif, refusé.</p>
    </div>
    <div class="card">
      <b>④ À valider</b>
      <p style="margin-top:2mm;">La file architecte&nbsp;: documents en attente + étapes checklist <i>todo</i>. C'est <i>le</i> bouton du matin&nbsp;: <i>« qu'est-ce qui m'attend ? »</i></p>
    </div>
  </div>
  <div class="quote">« Avoir un endroit, un dashboard, où je vois rapidement les trucs rouges en disant : OK, j'ai X trucs à valider. Je clique, je tombe dessus. »<small>Etienne Piergiovanni, séance kickoff du 5 juin 2026</small></div>
  <div class="footer"><span class="mono">ÆDIFICA · Manuel utilisateur</span><span class="pageno">4</span></div>
</section>

<!-- ============ 4 · CHECKLIST SIA PAR ACTEUR ============ -->
<section class="page">
  <div class="chrome"><span class="word"><span class="ae" style="color:var(--accent);">Æ</span> DIFICA</span> <small>4 · Checklist par acteur</small></div>
  <h2><span class="num">Chapitre 4</span>Checklist SIA — par phase ET par acteur</h2>
  <p class="lead">La checklist est <b>la feuille SIA Vaud retranscrite verbatim</b>. Chaque étape porte son acteur responsable — la liste du client se déduit par filtre&nbsp;: vous ne réinventez rien.</p>
  <p>L'idée fondatrice de la séance était simple&nbsp;: le client a <b>des devoirs</b>. Le mandataire a <b>des devoirs</b>. Et la feuille SIA Vaud les liste à chaque phase. Aedifica matérialise ce constat.</p>
  <h3>Exemple — phase 11 (Définition des objectifs)</h3>
  <table>
    <thead><tr><th style="width:30%;">Acteur</th><th>Étape (verbatim feuille SIA Vaud)</th></tr></thead>
    <tbody>
      <tr><td><span class="ts decision"><span class="dot"></span>Maître d'ouvrage</span></td><td>Fournir besoins, budget visé, terrain, délais souhaités.</td></tr>
      <tr><td><span class="ts sourced"><span class="dot"></span>Architecte</span></td><td>Traduire les rêves en programme (besoins, surfaces, nb de pièces).</td></tr>
      <tr><td><span class="ts sourced"><span class="dot"></span>Architecte</span></td><td>Évaluer le budget — conseils et scénarios de financement.</td></tr>
      <tr><td><span class="ts sourced"><span class="dot"></span>Architecte</span></td><td>Récolter les données du terrain (RDPPF, OEREB, règlements, plan de quartier…).</td></tr>
      <tr><td><span class="ts sourced"><span class="dot"></span>Architecte</span></td><td>Estimer les délais (de la planification à la réalisation).</td></tr>
    </tbody>
  </table>
  <h3>Onboarding mid-process</h3>
  <p>Si vous reprenez un projet déjà engagé, choisissez la <b>phase d'entrée</b> au moment d'initialiser la checklist&nbsp;: toutes les étapes antérieures seront marquées <span class="ts assume"><span class="dot"></span>rétroactif</span>, à reconstituer.</p>
  <h3>Bloquants externes</h3>
  <p>Une étape <b>non architecte</b> encore <i>todo</i> à une phase dépassée devient un <span class="ts conflict"><span class="dot"></span>bloquant externe</span> — affiché côte à côte avec vos blocages atelier. C'est l'unique manière de voir <i>réellement</i> sur quoi le projet attend.</p>
  <div class="footer"><span class="mono">ÆDIFICA · Manuel utilisateur</span><span class="pageno">5</span></div>
</section>

<!-- ============ 5 · PILOTAGE ============ -->
<section class="page">
  <div class="chrome"><span class="word"><span class="ae" style="color:var(--accent);">Æ</span> DIFICA</span> <small>5 · Pilotage</small></div>
  <h2><span class="num">Chapitre 5</span>Tâches, priorités, honoraires</h2>
  <p class="lead">L'angle mort historique de votre Excel — et celui d'Aedifica le plus IA. Vous ne naviguez pas dans un agenda&nbsp;: vous naviguez en <b>priorité</b> et en <b>bloquant</b>.</p>
  <h3>Priorités</h3>
  <div class="grid3">
    <div class="card"><b>P0</b><p style="margin:1mm 0 0;">Rendu officiel, concours, échéance couperet. Si raté → mort.</p></div>
    <div class="card"><b>P1</b><p style="margin:1mm 0 0;">Bloque autre chose. Doit avancer cette semaine.</p></div>
    <div class="card"><b>P2 / quick win</b><p style="margin:1mm 0 0;">Peu de temps, débarrassé d'un seul coup. À tacler entre deux blocs.</p></div>
  </div>
  <h3>Prédiction de durée et collision inter-projet</h3>
  <p>Chaque tâche peut porter une estimation. Quand vous fermez la tâche, vous saisissez le <i>temps réel</i>. Au fil des projets, Aedifica apprend votre <b>pondération personnelle</b> — vous savez (et Etienne l'a dit en séance) que vos tâches prennent souvent <i>×3 le temps estimé</i>. La <b>collision inter-projet</b> détecte quand deux rendus convergent et passe le voyant du rouge au vert.</p>
  <h3>Honoraires</h3>
  <p>Le calculateur applique la formule SIA basée sur le coût CFC2 (12–17&nbsp;% selon type) ou la méthode horaire (H&nbsp;=&nbsp;T&nbsp;×&nbsp;h). Une fois <i>deux projets</i> bouclés, Aedifica vous propose un tarif horaire calibré sur votre propre historique — pour répondre, factuellement, à&nbsp;: <i>«&nbsp;combien vaut vraiment mon temps&nbsp;?&nbsp;»</i>.</p>
  <div class="quote">« Pour un indépendant, c'est ultra important. C'est ce que je n'ai jamais fait. Avec ce type de prédiction, on peut faire un lien entre les honoraires, le temps que tu mets vraiment, et l'argent engagé dans ton projet. »<small>Séance kickoff, [17:34]</small></div>
  <div class="footer"><span class="mono">ÆDIFICA · Manuel utilisateur</span><span class="pageno">6</span></div>
</section>

<!-- ============ 6 · INVITER ============ -->
<section class="page">
  <div class="chrome"><span class="word"><span class="ae" style="color:var(--accent);">Æ</span> DIFICA</span> <small>6 · Inviter un client / un mandataire</small></div>
  <h2><span class="num">Chapitre 6</span>Inviter un client ou un mandataire</h2>
  <p class="lead">Le client et les mandataires ont leur propre vue de la plateforme. Vous décidez ce qu'ils voient — via la <b>gestion d'accès documentaire</b> et leur <b>checklist filtrée</b>.</p>
  <ol class="steps">
    <li>Dans <b>Intervenants</b>, ajoutez la personne (rôle, contact). Optionnel&nbsp;: rattachez-la à un groupe (Ingénieurs, Entreprises, Mandataires…) — l'accès aux documents passe par les groupes.</li>
    <li>Cliquez <b>«&nbsp;Inviter sur la plateforme&nbsp;»</b>, saisissez son e-mail. Aedifica génère un <i>code d'invitation</i>.</li>
    <li>Transmettez le code (e-mail, SMS, papier). La personne se rend sur le login, choisit <b>«&nbsp;J'ai reçu un code d'invitation&nbsp;»</b>, colle le code et définit son mot de passe.</li>
  </ol>
  <h3>Ce que le client voit (vue MO)</h3>
  <p>Une page épurée&nbsp;: <i>son projet</i>, <b>ce que vous attendez de lui</b> (sa checklist filtrée), <b>ses documents accessibles</b> (uniquement ceux qui lui ont été partagés). Le vocabulaire est <b>traduit pour lui</b>&nbsp;: <i>« Définition des objectifs »</i> devient <i>« On définit votre projet ensemble »</i>. Il coche d'un clic ce qu'il a fourni — vous le voyez immédiatement.</p>
  <h3>Ce que le mandataire voit</h3>
  <p>Idem mais avec le vocabulaire SIA standard&nbsp;: ses livrables (plans, calculs, justificatifs) et les documents qui le concernent (plans amont, programme, contraintes…).</p>
  <div class="notice"><b>Pourquoi c'est important.</b> Vous arrêtez de chasser le client par téléphone pour savoir s'il a transmis son budget. Sa case se coche, vous le savez. Et s'il bloque, vous le voyez côté <b>Coordination → en attente de l'extérieur</b>.</div>
  <div class="footer"><span class="mono">ÆDIFICA · Manuel utilisateur</span><span class="pageno">7</span></div>
</section>

<!-- ============ 7 · PREMIERS PAS + CREDENTIALS ============ -->
<section class="page">
  <div class="chrome"><span class="word"><span class="ae" style="color:var(--accent);">Æ</span> DIFICA</span> <small>7 · Premiers pas</small></div>
  <h2><span class="num">Chapitre 7</span>Premiers pas — votre atelier est prêt</h2>
  <p class="lead">Un projet de démonstration a été pré-rempli pour vous, basé sur les éléments de la séance du 5 juin (priorités, captures, BRS, intervenants). Connectez-vous et explorez.</p>
  <div class="creds">
    <div class="row"><span class="lbl">URL</span> <b>${URL}/workspace</b></div>
    <div class="row"><span class="lbl">Identifiant</span> <b>${LOGIN}</b></div>
    <div class="row"><span class="lbl">Mot de passe</span> <b>${PWD}</b></div>
    <div class="row"><span class="lbl">Projet seedé</span> <b>${PROJECT}</b></div>
  </div>
  <h3>Vos 3 premières actions, en 5 minutes</h3>
  <ol class="steps">
    <li><b>Allez dans Coordination.</b> Lisez les 4 cadrans. Vous y trouverez un bloquant externe (un devoir MO rétroactif), 2 documents à valider, des bloquants atelier (la tâche «&nbsp;Rendu permis CAMAC&nbsp;» est bloquée par 2 autres).</li>
    <li><b>Ouvrez Checklist SIA.</b> Filtrez par acteur <i>Maître d'ouvrage</i>. C'est ce que vous attendez du client. Filtrez par <i>Mandataire</i> : ce que vous attendez d'eux.</li>
    <li><b>Ouvrez Intervenants.</b> Invitez Mme Bourg-Pellet (le client) puis Anne Civilis (l'ing. civile) en cliquant sur leur bouton <i>«&nbsp;Inviter sur la plateforme&nbsp;»</i>. Donnez-leur les codes générés.</li>
  </ol>
  <h3>Ce qui n'est pas encore là</h3>
  <p>L'onglet <b>Opposition</b> n'a pas encore le scan public (jurisprudence locale, profil voisin). Le <b>règlement à l'étude</b> est saisi manuellement, pas encore moissonné depuis Vaud. Les <b>procès-verbaux</b> sont des documents — pas encore l'entité de premier ordre que vous avez décrite. Ces points sont sur la roadmap, dans l'ordre que vous avez indiqué.</p>
  <div class="footer"><span class="mono">ÆDIFICA · Manuel utilisateur</span><span class="pageno">8</span></div>
</section>

<!-- ============ COLOPHON ============ -->
<section class="page">
  <div class="chrome"><span class="word"><span class="ae" style="color:var(--accent);">Æ</span> DIFICA</span> <small>Colophon</small></div>
  <h2><span class="num">Colophon</span>À propos d'Aedifica</h2>
  <p class="lead">Aedifica est en cours de construction avec vous. La <b>Wave 10 — multi-acteurs</b> matérialise les retours de la séance du 5 juin 2026 (47 minutes utiles, retranscrites et analysées en profondeur dans <i>docs/strategy/session-2026-06-05-etienne-DEEP.md</i>).</p>
  <h3>Ce que la Wave 10 apporte</h3>
  <ul>
    <li>Checklist SIA exhaustive (≈ 47 étapes), retranscrite <i>verbatim</i> de la feuille SIA Vaud officielle, par phase ET par acteur.</li>
    <li>Surface <b>Coordination</b> — single point of truth, 4 cadrans.</li>
    <li>Accès multi-acteurs réel — invitation d'un intervenant comme utilisateur à périmètre réduit (rôle <i>external</i>).</li>
    <li>Vocabulaire client (mapping «&nbsp;Phase SIA ≠ Phase Client&nbsp;») pour la vue MO.</li>
    <li>Bloquants externes affichés côte à côte avec les blocages atelier.</li>
  </ul>
  <h3>Garde-fous</h3>
  <ul>
    <li><b>Pur soft.</b> L'IA n'intervient que sur la collision inter-projet, la prédiction de durée, et (à venir) le scan public d'opposition.</li>
    <li><b>L'architecte décide.</b> Aedifica propose, vous validez. Aucune décision n'est prise à votre place.</li>
    <li><b>Sourcé ou inconnu.</b> Jamais inventé.</li>
    <li><b>LPD.</b> Les documents confidentiels sont marqués comme tels et restent restreints.</li>
  </ul>
  <h3>Sources</h3>
  <ul>
    <li>SIA Vaud, <i>Construire dans les règles de l'art — Suivez le guide</i>, vd.sia.ch.</li>
    <li>SIA 102:2020 — Règlement concernant les prestations et honoraires des architectes.</li>
    <li>SIA 112:2014 — Modèle d'étude et conduite de projet.</li>
    <li>Norme SIA 380/1 (énergie), AEAI (incendie), SIA 500 (accessibilité), SIA 261 (sismique).</li>
  </ul>
  <p class="mono" style="margin-top:8mm;color:var(--mute);font-size:8.5pt;">Édition ${VERSION} · ${DATE} · Atelier Carré-Neuf · Aedifica est une plateforme privée, en phase de pilotage avec l'Atelier Carré-Neuf.</p>
  <div class="footer"><span class="mono">ÆDIFICA · Manuel utilisateur</span><span class="pageno">9</span></div>
</section>

</body>
</html>`;

const browser = await chromium.launch();
const ctx = await browser.newContext();
const page = await ctx.newPage();
await page.setContent(html, { waitUntil: "networkidle" });
await mkdir(dirname(OUT), { recursive: true });
await page.pdf({
  path: OUT,
  format: "A4",
  printBackground: true,
  preferCSSPageSize: true,
});
await browser.close();
console.log(`✓ Wrote ${OUT}`);
