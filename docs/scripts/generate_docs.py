# -*- coding: utf-8 -*-
"""
Genere le rapport de projet et le guide technique (FR) en .docx.

Relancer ce script regenere les deux documents a l'identique -- c'est la
source de verite versionnee (le binaire .docx ne doit pas etre edite a la
main).

Usage:
    python docs/scripts/generate_docs.py
"""

from __future__ import annotations

import datetime
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from PIL import Image

DOCS_DIR = Path(__file__).resolve().parent.parent
UML_DIR = DOCS_DIR / "uml"
LOGO = DOCS_DIR / "assets" / "logo.png"

CRIMSON = RGBColor(0xDC, 0x14, 0x3C)
DARK = RGBColor(0x1F, 0x29, 0x37)
GRAY = RGBColor(0x6B, 0x72, 0x80)

TODAY = datetime.date.today().strftime("%d/%m/%Y")


# ---------------------------------------------------------------------------
# Aides de mise en forme
# ---------------------------------------------------------------------------

def set_base_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.font.color.rgb = DARK
    style.paragraph_format.space_after = Pt(8)

    for i, size in ((1, 22), (2, 16), (3, 13)):
        h = doc.styles[f"Heading {i}"]
        h.font.name = "Calibri"
        h.font.size = Pt(size)
        h.font.color.rgb = CRIMSON
        h.font.bold = True
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(8)


def title_page(doc: Document, title: str, subtitle: str) -> None:
    for _ in range(3):
        doc.add_paragraph()

    if LOGO.exists():
        with Image.open(LOGO) as im:
            ratio = im.size[0] / im.size[1]
        w = 3.2
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        run.add_picture(str(LOGO), width=Inches(w), height=Inches(w / ratio))
    else:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("5")
        run.font.size = Pt(54)
        run.font.bold = True
        run.font.color.rgb = CRIMSON

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run("edma.tn")
        run.font.size = Pt(30)
        run.font.bold = True
        run.font.color.rgb = DARK

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(title)
    run.font.size = Pt(22)
    run.font.bold = True
    run.font.color.rgb = DARK

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(subtitle)
    run.font.size = Pt(14)
    run.font.color.rgb = GRAY

    for _ in range(8):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"Document genere le {TODAY}")
    run.font.size = Pt(10)
    run.font.color.rgb = GRAY

    doc.add_page_break()


def add_landscape_section(doc: Document) -> None:
    section = doc.add_section()
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = section.page_height, section.page_width


def add_portrait_section(doc: Document) -> None:
    section = doc.add_section()
    section.orientation = WD_ORIENT.PORTRAIT
    section.page_width, section.page_height = min(section.page_width, section.page_height), max(
        section.page_width, section.page_height
    )


def add_image_fit(doc: Document, path: Path, max_w_in: float, max_h_in: float, caption: str = "") -> None:
    with Image.open(path) as im:
        px_w, px_h = im.size
    ratio = px_w / px_h
    w, h = max_w_in, max_w_in / ratio
    if h > max_h_in:
        h = max_h_in
        w = max_h_in * ratio
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(str(path), width=Inches(w), height=Inches(h))
    if caption:
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = cap.add_run(caption)
        r.italic = True
        r.font.size = Pt(9)
        r.font.color.rgb = GRAY


def shade_cell(cell, color_hex: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.makeelement(qn("w:shd"), {qn("w:val"): "clear", qn("w:color"): "auto", qn("w:fill"): color_hex})
    tc_pr.append(shd)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        run = hdr[i].paragraphs[0].add_run(h)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade_cell(hdr[i], "DC143C")
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
            for para_ in cells[i].paragraphs:
                para_.style = doc.styles["Normal"]
                for r in para_.runs:
                    r.font.size = Pt(10)
    if widths:
        for row in table.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()


def bullets(doc: Document, items: list[str], style: str = "List Bullet") -> None:
    for item in items:
        doc.add_paragraph(item, style=style)


def para(doc: Document, text: str) -> None:
    doc.add_paragraph(text)


def code_line(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    for r in p.runs:
        r.font.name = "Consolas"
        r.font.size = Pt(10)


def h1(doc: Document, text: str):
    return doc.add_heading(text, level=1)


def h2(doc: Document, text: str):
    return doc.add_heading(text, level=2)


# ---------------------------------------------------------------------------
# RAPPORT DE PROJET
# ---------------------------------------------------------------------------

def build_rapport() -> None:
    doc = Document()
    set_base_style(doc)
    title_page(doc, "Rapport de projet", "Plateforme de mise en relation pour services et emplois locaux")

    h1(doc, "1. Introduction")

    h2(doc, "1.1 Contexte")
    para(
        doc,
        "Le marché tunisien des petits travaux et services à la personne (plomberie, électricité, "
        "ménage, réparations, cours particuliers, etc.) repose encore largement sur le bouche-à-oreille "
        "et des annonces informelles (groupes Facebook, petites annonces). Cette situation rend difficile, "
        "pour un client, de vérifier la fiabilité d'un prestataire, et pour un travailleur qualifié, de se "
        "rendre visible auprès d'une clientèle plus large. 5edma.tn (« khedma », « travail » en "
        "dialecte tunisien) propose de structurer cette mise en relation au sein d'une plateforme web unique.",
    )

    h2(doc, "1.2 Objectifs du projet")
    bullets(
        doc,
        [
            "Permettre à des clients de publier des besoins ponctuels (offres d'emploi) et de recevoir des candidatures de travailleurs.",
            "Permettre à des travailleurs de proposer des services à prix fixe, consultables et réservables directement.",
            "Garantir un niveau de confiance minimal via une vérification d'identité gérée par un administrateur.",
            "Fournir aux deux parties un canal de communication (messagerie instantanée), un système d'avis, et un portefeuille interne pour les transactions.",
            "Faciliter la rédaction d'annonces (bio, description de poste) grâce à une assistance par intelligence artificielle.",
        ],
    )

    h2(doc, "1.3 Méthodologie")
    para(
        doc,
        "Le projet a été mené de manière itérative : une première version (MVP) a permis de valider "
        "l'authentification, la vérification des profils et la publication de services ; les itérations "
        "suivantes ont ajouté les candidatures aux offres, la messagerie, le portefeuille, les abonnements "
        "Premium et les avis. La dernière itération, documentée dans ce rapport, a consisté en une "
        "consolidation complète du projet : correction de bugs, migration de la base de données vers MySQL, "
        "durcissement de la sécurité, et finalisation de l'interface web couvrant l'ensemble des cas d'usage.",
    )

    h1(doc, "2. Présentation de la plateforme")

    h2(doc, "2.1 Les trois rôles")
    bullets(
        doc,
        [
            "Travailleur : propose ses compétences, soit en répondant à des offres publiées par des clients, soit en publiant ses propres services à tarif fixe.",
            "Client : publie des offres d'emploi ou réserve directement un service publié par un travailleur.",
            "Administrateur : vérifie l'identité des travailleurs et des clients avant de les autoriser à interagir pleinement avec la plateforme, et valide les demandes de recharge de portefeuille.",
        ],
    )

    h2(doc, "2.2 Deux parcours de mise en relation complémentaires")
    para(
        doc,
        "La plateforme propose volontairement deux parcours distincts, reflétant deux besoins différents "
        "qui ont chacun justifié leur propre modèle de données :",
    )
    bullets(
        doc,
        [
            "Offres et candidatures (« Jobs & Applications ») : un client décrit un besoin précis "
            "(ex. « réparer une fuite d'eau, budget 50-80 TND »), les travailleurs intéressés "
            "postulent avec un message de motivation, le client examine les candidatures et en accepte une.",
            "Services et réservations (« Services & Bookings ») : un travailleur publie un service "
            "standard à prix fixe (ex. « nettoyage de climatiseur — 60 TND »), qu'un client peut "
            "réserver directement pour une date donnée, sans phase de candidature.",
        ],
    )
    para(
        doc,
        "Ce choix permet de couvrir à la fois les besoins ponctuels/sur-mesure et les prestations "
        "répétables/standardisées, deux usages réels observés chez les artisans tunisiens.",
    )

    h1(doc, "3. Analyse et conception")

    h2(doc, "3.1 Diagramme de cas d'utilisation")
    para(
        doc,
        "Le diagramme ci-dessous recense les fonctionnalités réellement disponibles dans la version "
        "actuelle de la plateforme, regroupées par acteur.",
    )
    add_landscape_section(doc)
    add_image_fit(doc, UML_DIR / "use_case.png", 9.5, 6.2, "Figure 1 — Diagramme de cas d'utilisation")
    add_portrait_section(doc)

    h2(doc, "3.2 Diagramme de classes")
    para(
        doc,
        "Note méthodologique : contrairement à une conception orientée objet « riche » où le "
        "comportement (méthodes) serait porté par les classes du modèle, l'architecture retenue (FastAPI) "
        "place la logique métier dans les gestionnaires de routes (endpoints) ; les classes ci-dessous ne "
        "portent que les données persistées (mapping SQLAlchemy vers MySQL). Ce choix est cohérent avec le "
        "style architectural léger couramment adopté avec FastAPI, où le modèle reste une couche de données "
        "et la logique applicative vit dans la couche API.",
    )
    add_image_fit(doc, UML_DIR / "class_diagram.png", 6.0, 9.3, "Figure 2 — Diagramme de classes")

    h2(doc, "3.3 Modèle de données (MCD / ERD)")
    para(
        doc,
        "Le schéma relationnel ci-dessous correspond exactement au schéma MySQL utilisé en production "
        "(voir backend/database/schema.sql), lui-même dérivé des mêmes modèles SQLAlchemy que le "
        "diagramme de classes.",
    )
    add_landscape_section(doc)
    add_image_fit(doc, UML_DIR / "erd.png", 9.5, 6.2, "Figure 3 — Modèle conceptuel de données")
    add_portrait_section(doc)

    h1(doc, "4. Architecture technique")

    h2(doc, "4.1 Stack technologique")
    add_table(
        doc,
        ["Couche", "Technologie", "Rôle"],
        [
            ["Backend", "FastAPI (Python, async), SQLAlchemy 2.0", "API REST + WebSocket"],
            ["Base de données", "MySQL 8 (aiomysql / PyMySQL)", "Persistance"],
            ["Migrations", "Alembic", "Versionnement du schéma"],
            ["Authentification", "JWT (python-jose), passlib (pbkdf2_sha256)", "Sécurité"],
            ["IA", "Groq (modèles Llama, llama-3.3-70b-versatile)", "Génération de texte (bio, descriptions)"],
            ["Frontend", "Next.js 16 (React 19, TypeScript, Tailwind CSS)", "Interface web"],
        ],
        widths=[3.5, 7, 6],
    )

    h2(doc, "4.2 Architecture générale")
    para(
        doc,
        "Le backend FastAPI expose une API REST ainsi qu'un canal WebSocket dédié à la messagerie "
        "instantanée. Le frontend Next.js consomme cette API via un client HTTP centralisé (lib/api.ts) "
        "qui gère l'authentification (jeton JWT stocké côté client) et la mise en forme des erreurs. La "
        "base de données MySQL est la source unique de vérité pour l'ensemble des entités (utilisateurs, "
        "offres, services, réservations, portefeuilles, avis, abonnements).",
    )

    h2(doc, "4.3 Sécurité")
    bullets(
        doc,
        [
            "Mots de passe hachés (pbkdf2_sha256) — jamais stockés en clair.",
            "Authentification par jeton JWT signé (HS256), durée de validité configurable.",
            "Séparation des rôles via des dépendances FastAPI dédiées (get_verified_worker, "
            "get_verified_client, get_current_admin) vérifiées à chaque requête sensible.",
            "Le canal WebSocket de messagerie authentifie l'utilisateur via son jeton JWT (et non un "
            "identifiant transmis librement par le client).",
            "Limitation de débit (10 requêtes/minute/IP) sur les endpoints de connexion et d'inscription, "
            "contre les attaques par force brute.",
            "En-têtes de sécurité systématiques (X-Frame-Options, nosniff, HSTS en production) et gestion "
            "d'erreurs globale : aucune trace technique n'est jamais renvoyée au client.",
            "Origines CORS restreintes à une liste blanche configurable, documentation interactive "
            "(/docs, /redoc) désactivée en production.",
            "Secrets et données sensibles exclus du dépôt Git : fichier .env, photos de pièces d'identité "
            "(stockées localement, jamais versionnées).",
        ],
    )

    h2(doc, "4.4 Interface utilisateur")
    para(
        doc,
        "L'interface a fait l'objet d'une refonte visuelle complète : palette de couleurs extraite "
        "directement du logo officiel (bleu #0454B5, rouge #D8202B), animations d'entrée et de défilement "
        "(Framer Motion) sur la page d'accueil, transitions de page cohérentes sur l'ensemble du site, et "
        "favicon / image de partage (Open Graph) générés à partir du logo. Les pages de consultation des "
        "offres et des services ont été rendues accessibles sans connexion — condition nécessaire à leur "
        "indexation par les moteurs de recherche — l'action elle-même (postuler, réserver) restant réservée "
        "aux utilisateurs connectés.",
    )

    h1(doc, "5. Fonctionnalités implémentées")
    add_table(
        doc,
        ["Module", "Fonctionnalités"],
        [
            ["Authentification", "Inscription (avec ou sans envoi de pièce d'identité), connexion, gestion du profil."],
            ["Vérification", "File d'attente admin pour approuver/rejeter travailleurs et clients, avec motif de rejet."],
            ["Offres & candidatures", "Publication, recherche, candidature, acceptation/refus, clôture, boost."],
            ["Services & réservations", "Publication de services, réservation, confirmation, annulation, clôture."],
            ["Messagerie", "Historique REST + WebSocket temps réel, authentifié par jeton."],
            ["Avis", "Notation de 1 à 5 après une offre ou une réservation terminée, recalcul automatique de la note moyenne."],
            ["Portefeuille", "Solde, historique de transactions, demande de recharge, validation admin."],
            ["Abonnements", "Plans Premium, achat via le portefeuille, boost d'offre."],
            ["Intelligence artificielle", "Génération de bio (travailleur) et de description de poste (client) via Groq."],
            ["Référencement (SEO)", "Métadonnées complètes, plan de site, robots.txt, données structurées ; pages d'offres et de services consultables sans connexion."],
        ],
        widths=[4, 12.5],
    )

    h1(doc, "6. Choix techniques et justifications")
    h2(doc, "6.1 MySQL plutôt que PostgreSQL")
    para(
        doc,
        "Le projet a débuté sur PostgreSQL, mais a été migré vers MySQL pour correspondre à l'environnement "
        "d'hébergement cible. Cette migration a nécessité le remplacement des types propres à PostgreSQL "
        "(ARRAY, JSONB) par des colonnes JSON génériques, compatibles avec les deux moteurs, ainsi que le "
        "remplacement du pilote asynchrone (asyncpg → aiomysql).",
    )
    h2(doc, "6.2 Groq pour la génération de texte par IA")
    para(
        doc,
        "Groq a été retenu pour sa latence d'inférence très faible (infrastructure LPU dédiée) et la "
        "disponibilité de modèles Llama performants à coût réduit, adaptés à des tâches courtes comme la "
        "génération d'une bio ou d'une description de poste. En l'absence de clé API configurée, le système "
        "bascule automatiquement sur un texte de substitution afin que le reste de l'application continue "
        "de fonctionner.",
    )
    h2(doc, "6.3 Next.js pour le frontend")
    para(
        doc,
        "Next.js (App Router) a été choisi pour sa structure de routage par fichiers, son écosystème React "
        "mature et ses performances de rendu, adaptées à une application riche en tableaux de bord "
        "spécifiques à chaque rôle.",
    )

    h1(doc, "7. Difficultés rencontrées et corrections apportées")
    para(
        doc,
        "L'audit du code existant, mené avant cette itération, a mis en évidence plusieurs anomalies "
        "corrigées dans le cadre de ce travail :",
    )
    bullets(
        doc,
        [
            "La validation d'un compte client par l'administrateur ne persistait jamais en base (appel "
            "de sauvegarde manquant) — corrigé.",
            "Deux erreurs bloquantes (variable non définie) survenaient lors de la mise à jour d'un profil "
            "précédemment rejeté — corrigées.",
            "Plusieurs routes étaient définies deux fois dans le code (dont l'annulation de réservation et "
            "la vérification de travailleur), la seconde définition masquant silencieusement la première "
            "— doublons supprimés.",
            "La création de compte ne provisionnait pas systématiquement de portefeuille pour le nouvel "
            "utilisateur — corrigé.",
            "Le boost d'une offre (fonctionnalité payante) ne modifiait pas le champ réellement utilisé par "
            "le tri des résultats de recherche : la fonctionnalité était payée mais sans effet — corrigé.",
            "Le canal de messagerie WebSocket faisait confiance à un identifiant utilisateur transmis "
            "librement par le client, permettant à n'importe qui de se faire passer pour un autre "
            "utilisateur — l'authentification par jeton JWT a été ajoutée.",
            "Plusieurs fichiers du dépôt (dont le point d'entrée du serveur) étaient enregistrés dans un "
            "encodage incorrect (UTF-16 au lieu d'UTF-8), les rendant illisibles par l'interpréteur Python "
            "sur un poste différent — corrigé.",
            "Un fichier de configuration contenant un mot de passe de base de données en clair était "
            "versionné dans l'historique Git — l'historique complet du dépôt a été purgé de ce secret.",
            "L'approbation d'un travailleur par l'administrateur mettait à jour le champ verified mais pas "
            "le champ status — or c'est ce second champ que vérifient tous les endpoints réservés aux "
            "travailleurs vérifiés. Un travailleur « approuvé » restait donc bloqué. Anomalie détectée en "
            "testant le parcours complet contre la base de données réelle plutôt qu'en relisant "
            "uniquement le code — corrigée et couverte par un test de non-régression.",
            "L'endpoint d'inscription (formulaire avec pièce d'identité) acceptait le rôle « admin » "
            "directement, permettant à quiconque de créer un compte administrateur — faille corrigée.",
            "La feuille de style principale du frontend utilisait la syntaxe Tailwind CSS v3 alors que le "
            "projet utilise Tailwind v4 ; la compilation réussissait sans erreur mais aucune classe "
            "utilitaire n'était générée, laissant l'interface quasiment sans mise en forme. Anomalie "
            "invisible aux vérifications automatiques (compilation, typage) et détectée uniquement en "
            "affichant réellement l'application dans un navigateur — corrigée, puis chaque page modifiée "
            "a été revérifiée visuellement par capture d'écran.",
        ],
    )

    h1(doc, "8. Tests automatisés")
    para(
        doc,
        "Une suite de tests automatisés (pytest) couvre les parcours critiques du backend — inscription, "
        "connexion, vérification par l'administrateur, cycle de vie complet d'une offre et d'une "
        "candidature, portefeuille — en s'exécutant contre une base de données SQLite en mémoire, sans "
        "dépendance à MySQL. Elle inclut un test de non-régression dédié au bug de vérification décrit "
        "ci-dessus. L'ensemble du parcours applicatif a en complément été rejoué manuellement contre la "
        "base de données MySQL réelle (inscription, vérification admin, publication d'offre, candidature, "
        "acceptation, recharge de portefeuille, génération IA, avis) avant d'être nettoyé.",
    )

    h1(doc, "9. Déploiement")
    para(
        doc,
        "Le projet est conteneurisé : un Dockerfile pour le backend, un pour le frontend (construction "
        "Next.js autonome, sans node_modules dans l'image finale), et un fichier docker-compose.yml à la "
        "racine orchestrant MySQL, le backend et le frontend ensemble pour un déploiement reproductible.",
    )

    h1(doc, "10. Perspectives d'évolution")
    bullets(
        doc,
        [
            "Intégration d'une véritable passerelle de paiement (D17, Flouci) — nécessite un accord "
            "commercial et des identifiants marchands auprès de ces prestataires.",
            "Table dédiée au suivi des documents d'identité (statut par soumission, historique, motif "
            "détaillé), en complément du statut simple actuellement porté par le profil.",
            "Notifications push et par e-mail (nouvelle candidature, message reçu, réservation confirmée).",
            "Application mobile (probablement React Native, en réutilisant la même API).",
            "Tableaux de bord analytiques pour l'administrateur (revenus, activité, taux de conversion).",
        ],
    )

    h1(doc, "11. Conclusion")
    para(
        doc,
        "Cette itération a transformé un ensemble de prototypes fonctionnels mais fragiles en une base de "
        "code cohérente, sécurisée, testée, conteneurisée et entièrement reliée à une interface utilisateur "
        "soignée couvrant les trois rôles de la plateforme. Les fondations techniques (base de données "
        "MySQL, authentification, architecture API, déploiement Docker) sont désormais prêtes à accueillir "
        "les évolutions futures, au premier rang desquelles l'intégration d'un moyen de paiement réel.",
    )

    out = DOCS_DIR / "RAPPORT_5edma.tn.docx"
    doc.save(out)
    print(f"Ecrit : {out}")


# ---------------------------------------------------------------------------
# GUIDE TECHNIQUE
# ---------------------------------------------------------------------------

def build_guide() -> None:
    doc = Document()
    set_base_style(doc)
    title_page(doc, "Guide technique", "Installation, exploitation et architecture du projet")

    h1(doc, "1. Introduction")
    para(
        doc,
        "Ce guide s'adresse aux développeurs qui installent, exploitent ou font évoluer la plateforme "
        "5edma.tn. Il complète le Rapport de projet, orienté conception, en se concentrant sur les aspects "
        "pratiques : installation, configuration, structure du code et de l'API.",
    )

    h1(doc, "2. Prérequis")
    bullets(
        doc,
        [
            "Python 3.11 ou supérieur",
            "Node.js 20 ou supérieur (pour le frontend Next.js)",
            "MySQL 8 ou supérieur",
            "Une clé API Groq (console.groq.com) pour activer la génération de texte par IA — "
            "facultatif, une valeur de repli est utilisée en son absence",
        ],
    )

    h1(doc, "3. Structure du dépôt")
    para(doc, "Organisation générale du projet :")
    add_table(
        doc,
        ["Chemin", "Contenu"],
        [
            ["backend/", "API FastAPI (Python)"],
            ["backend/app/", "Code applicatif : modèles, routes, configuration"],
            ["backend/database/schema.sql", "Schéma MySQL complet, prêt à être importé"],
            ["backend/migrations/", "Migrations Alembic"],
            ["backend/tests/", "Scripts de test manuels"],
            ["frontend/", "Application web Next.js"],
            ["frontend/app/", "Pages (routage par dossier, App Router)"],
            ["frontend/lib/", "Client API, types TypeScript, hooks partagés"],
            ["docs/", "Documentation : architecture, UML, rapport, présent guide"],
            ["docs/uml/", "Diagrammes (sources Mermaid + images rendues)"],
        ],
        widths=[5, 11.5],
    )

    h1(doc, "4. Installation du backend")
    para(doc, "Depuis la racine du dépôt :")
    code_line(doc, "cd backend")
    code_line(doc, "python -m venv venv")
    code_line(doc, "venv\\Scripts\\activate          (Windows)   ou   source venv/bin/activate (Linux/Mac)")
    code_line(doc, "pip install -r requirements.txt")
    code_line(doc, "copy .env.example .env          (puis renseigner les valeurs, voir section 6)")

    h1(doc, "5. Base de données")
    para(doc, "Deux méthodes équivalentes pour initialiser le schéma, au choix :")
    h2(doc, "5.1 Import direct du schéma SQL")
    code_line(doc, "mysql -u <utilisateur> -p <base> < backend/database/schema.sql")
    h2(doc, "5.2 Via Alembic (recommandé en développement continu)")
    code_line(doc, "cd backend")
    code_line(doc, "alembic upgrade head")
    para(
        doc,
        "Les deux méthodes produisent un schéma strictement identique : le fichier schema.sql et la "
        "migration Alembic initiale (0001_initial_schema.py) sont maintenus manuellement en parallèle, "
        "tous deux dérivés des mêmes modèles SQLAlchemy.",
    )
    para(doc, "Table des entités principales du schéma :")
    add_table(
        doc,
        ["Table", "Rôle"],
        [
            ["users", "Compte de base (email, téléphone, mot de passe, rôle)"],
            ["worker_profiles / client_profiles", "Profil spécifique au rôle, statut de vérification"],
            ["job_offers / job_applications", "Parcours Offres & candidatures"],
            ["services / bookings", "Parcours Services & réservations"],
            ["reviews", "Avis (liés à une réservation ou à une candidature acceptée)"],
            ["wallets / transactions", "Portefeuille et historique financier"],
            ["messages", "Messagerie instantanée"],
            ["subscription_plans / user_subscriptions / job_boosts", "Abonnements Premium et boosts"],
        ],
        widths=[5, 11.5],
    )

    h1(doc, "6. Variables d'environnement (backend/.env)")
    add_table(
        doc,
        ["Variable", "Description"],
        [
            ["DATABASE_URL", "Chaîne de connexion SQLAlchemy, ex. mysql+aiomysql://user:pass@host:3306/nom_base"],
            ["SECRET_KEY", "Clé secrète de signature des jetons JWT — générer une valeur aléatoire longue"],
            ["ALGORITHM", "Algorithme de signature JWT (HS256 par défaut)"],
            ["ACCESS_TOKEN_EXPIRE_MINUTES", "Durée de validité d'un jeton, en minutes"],
            ["GROQ_API_KEY", "Clé API Groq pour la génération de texte par IA (facultatif)"],
            ["ENVIRONMENT", "« development » (défaut) ou « production » — désactive /docs et /redoc en production"],
            ["DEBUG", "Active les logs SQL détaillés et les erreurs de validation verbeuses (lié à ENVIRONMENT par défaut)"],
            ["ALLOWED_ORIGINS", "Liste d'origines CORS autorisées, séparées par des virgules"],
            ["RATE_LIMIT_ENABLED", "Active la limitation de débit sur les endpoints d'authentification (true par défaut)"],
        ],
        widths=[6, 10.5],
    )
    para(
        doc,
        "Le fichier .env n'est jamais versionné (voir .gitignore) ; backend/.env.example documente les "
        "clés attendues sans valeurs réelles.",
    )

    h1(doc, "7. Installation du frontend")
    code_line(doc, "cd frontend")
    code_line(doc, "npm install")
    code_line(doc, "# créer .env.local avec NEXT_PUBLIC_API_URL (voir tableau ci-dessous)")
    add_table(
        doc,
        ["Variable", "Description"],
        [["NEXT_PUBLIC_API_URL", "URL de base de l'API backend, ex. http://127.0.0.1:8000"]],
        widths=[6, 10.5],
    )

    h1(doc, "8. Lancement en développement")
    h2(doc, "8.1 Backend")
    code_line(doc, "uvicorn main:app --reload")
    para(doc, "L'API est servie sur http://localhost:8000, documentation interactive sur /docs.")
    h2(doc, "8.2 Frontend")
    code_line(doc, "npm run dev")
    para(doc, "L'application est servie sur http://localhost:3000.")

    h1(doc, "9. Aperçu de l'API par module")
    add_table(
        doc,
        ["Préfixe", "Module", "Exemples d'endpoints"],
        [
            ["/auth", "Authentification", "POST /auth/register, POST /auth/login, GET /auth/me"],
            ["/admin", "Vérification", "GET /admin/workers/pending, POST /admin/workers/{id}/verify"],
            ["/jobs", "Offres & candidatures", "GET /jobs, POST /jobs/{id}/apply, GET /jobs/applications/mine"],
            ["/services", "Services", "GET /services, POST /services, GET /services/{id}"],
            ["/bookings", "Réservations", "POST /bookings, POST /bookings/{id}/confirm"],
            ["/reviews", "Avis", "POST /reviews/jobs/{job_id}/applications/{id}/review-as-client"],
            ["/wallet", "Portefeuille", "GET /wallet/me, POST /wallet/top-up"],
            ["/chat", "Messagerie", "GET /chat/history/{job_id}, WS /chat/ws?token=..."],
            ["/subscriptions", "Abonnements", "GET /subscriptions/plans, POST /subscriptions/boost-job"],
            ["/ai", "Intelligence artificielle", "POST /ai/generate-bio, POST /ai/generate-job-description"],
        ],
        widths=[3, 4, 9.5],
    )
    para(doc, "La liste complète et interactive des endpoints est disponible sur /docs (Swagger UI) une fois le serveur lancé.")

    h1(doc, "10. Tests")
    code_line(doc, "cd backend && pytest")
    para(
        doc,
        "S'exécute contre une base SQLite en mémoire (voir tests/conftest.py) — ni MySQL ni fichier .env "
        "requis. Les scripts dans tests/manual/ nécessitent en revanche un serveur et une base réels et ne "
        "sont pas ramassés par pytest (nommage volontairement différent de test_*.py).",
    )
    para(
        doc,
        "Le frontend est vérifié via le compilateur TypeScript (npx tsc --noEmit), ESLint (npm run lint) "
        "et une compilation de production (npm run build). Pour les changements d'interface, une "
        "vérification visuelle réelle (navigateur) est indispensable : cette itération a justement révélé "
        "un bug (voir le Rapport de projet, section 7) invisible à ces trois vérifications automatiques.",
    )

    h1(doc, "11. Déploiement")
    h2(doc, "11.1 Avec Docker (recommandé)")
    code_line(doc, "copy .env.example .env   # racine du dépôt")
    code_line(doc, "docker compose up --build")
    para(
        doc,
        "Démarre MySQL, le backend et le frontend ensemble. backend/Dockerfile et frontend/Dockerfile sont "
        "tous deux multi-étapes ; le frontend construit le bundle autonome de Next.js (output: "
        "'standalone'), qui ne nécessite pas node_modules dans l'image finale.",
    )
    h2(doc, "11.2 Sans Docker — notes générales")
    bullets(
        doc,
        [
            "Backend : servir via un serveur ASGI de production (ex. uvicorn derrière un reverse proxy, "
            "ou gunicorn avec des workers uvicorn), avec les variables d'environnement de production "
            "(ENVIRONMENT=production notamment).",
            "Frontend : npm run build puis npm run start, ou déploiement sur une plateforme compatible "
            "Next.js.",
            "Base de données : sauvegardes régulières, et ne jamais accorder au compte MySQL applicatif "
            "des droits d'administration complets.",
            "Ne jamais réutiliser en production les secrets (SECRET_KEY, mots de passe) présents dans un "
            "environnement de développement.",
        ],
    )

    h1(doc, "12. Dépannage")
    add_table(
        doc,
        ["Symptôme", "Piste de résolution"],
        [
            ["Erreur de connexion à la base au démarrage", "Vérifier DATABASE_URL, que MySQL est démarré, et que la base existe."],
            ["Erreur CORS dans le navigateur", "Vérifier que l'origine du frontend figure dans la liste `origins` de backend/app/main.py."],
            ["La génération IA renvoie un texte générique", "GROQ_API_KEY absente ou invalide — le système bascule alors sur un texte de repli."],
            ["Le WebSocket de chat se ferme immédiatement", "Le jeton JWT transmis en paramètre `token` est absent, expiré ou invalide."],
            ["« Module not found » au démarrage du backend", "Environnement virtuel non activé, ou dépendances non installées (pip install -r requirements.txt)."],
        ],
        widths=[6, 10.5],
    )

    out = DOCS_DIR / "GUIDE_TECHNIQUE_5edma.tn.docx"
    doc.save(out)
    print(f"Ecrit : {out}")


if __name__ == "__main__":
    build_rapport()
    build_guide()
