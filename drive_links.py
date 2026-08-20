"""
Relie chaque leçon / ressource de l'app au(x) vrai(s) fichier(s) sur Google Drive
de Marouane, à partir d'un manifest pré-généré (drive_manifest.json).

Le manifest a été construit une fois via l'API Drive (voir build_manifest.py côté
session Claude) et n'est PAS re-interrogé en direct par l'appli — les liens sont
donc figés au moment du seed. Si le contenu du Drive change, il faut régénérer
drive_manifest.json et relancer `python database.py`.
"""
import json
import os
import re

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "drive_manifest.json")

JUNK_NAMES = {".DS_Store"}
JUNK_MIME = {"application/octet-stream"}


def _natural_key(name):
    """Sort files the way a human expects: '1 - Les fondations.mp4' before
    '2 - ...', numbers before un-numbered names, then alphabetically."""
    m = re.match(r"^\s*(\d+)", name)
    prefix = int(m.group(1)) if m else float("inf")
    return (prefix, name.lower())


def _load_manifest():
    if not os.path.exists(MANIFEST_PATH):
        return {}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f).get("folders", {})


_FOLDERS = _load_manifest()  # name -> {id, parent_path, files}
_BY_ID = {info["id"]: (name, info) for name, info in _FOLDERS.items()}


def _full_path(name, info):
    return f"{info['parent_path']}/{name}" if info["parent_path"] else name


def _collect(folder_id, _seen):
    """Recursively collect every real (non-junk) file under a Drive folder id,
    including files in nested subfolders at any depth."""
    if folder_id not in _BY_ID or folder_id in _seen:
        return []
    _seen.add(folder_id)

    name, info = _BY_ID[folder_id]
    my_path = _full_path(name, info)

    out = []
    for f in info["files"]:
        if f["name"] in JUNK_NAMES or f["mimeType"] in JUNK_MIME:
            continue
        out.append({"name": f["name"], "drive_id": f["id"], "mime_type": f["mimeType"]})

    # find direct child folders (parent_path == my_path) and recurse
    for other_name, other_info in _FOLDERS.items():
        if other_info["parent_path"] == my_path:
            out.extend(_collect(other_info["id"], _seen))

    return out


def files_under(folder_id):
    """Public entry point: collect + sort so students see files in a sane,
    human order (numbered filenames first, in numeric order)."""
    out = _collect(folder_id, set())
    out.sort(key=lambda f: _natural_key(f["name"]))
    return out


def file_by_name(folder_key, filename):
    """Look up a single file's drive id by exact filename inside a top-level folder."""
    info = _FOLDERS.get(folder_key)
    if not info:
        return None
    for f in info["files"]:
        if f["name"] == filename:
            return {"name": f["name"], "drive_id": f["id"], "mime_type": f["mimeType"]}
    return None


# ---------------------------------------------------------------------------
# Lesson -> Drive folder id, keyed as (phase_position, lesson_position)
# Folder ids come straight from the manifest crawl.
# ---------------------------------------------------------------------------
LESSON_FOLDERS = {
    (1, 1): "1BpOwg4RmT3NKKheiB-Nl-AR805WOiCtw",   # Mindset
    (1, 2): "1JbRn8ghX6Z-iYarIy0YxMfkBIboOURQy",   # Finance et Fiscalité

    (2, 1): "1kaaLzUAaARx6bNP4656GP16vEv3STw7X",   # IA en e-commerce
    (2, 2): "1gdkc36B66tuB-cCmXp3AQo4W8CXPbZ4q",   # Business model
    (2, 3): "1MNW3y40YyUcRc8FGbKHO97n_6NeOOGSJ",   # Source de trafic
    (2, 4): "1BevKTvp1TyDCL26mXqN4gMJl0Ucn9yza",   # Recherche de produit
    (2, 5): "1_arZAdP3suCir4KuGAzukC7IlDdgfsNM",   # Sourcing
    (2, 6): "1tdPaBbyVH1tZbEjUWBr_hx048uGmi_n2",   # Positionnement & marché
    (2, 7): "1kphR_QGFJqDzyp9wJMYWK2Ze9cwBdd1G",   # Branding
    (2, 8): "1xQAA9O6QDapeCHMyI5aalkrWToQupDvb",   # Masterclass sourcing
    (2, 9): "1wRH9Z_TjPRT3w-03-4ttgXokqr4lhpqy",   # Étude de cas dropshipping
    (2, 10): "1iiF2PGZQk16FxWbIdA_ZGWqW80G7j52v",  # Marque avec stock
    (2, 11): "1bcTdPQM7sgj8_Nset0SEGp4lNHYpo9X7",  # Étude de cas stock
    (2, 12): "1ikWRcxsfSmei2OMyCJx0cW0wlKOHRb41",  # Bonus importation

    (3, 1): "1YbRy-lJC_X73w5NZeXkaKT54umVZohN7",   # Création & optimisation de site
    (3, 2): "1mr0r-gRJ3tdgO3bPHMXkWkuWC2qOfn6-",   # Annexe & outils (récursif, ~19 sous-dossiers)
    (3, 3): "1tI-ZYPkg6oli09eq6TKsHjZ0pjQ0Q4vm",   # Thème Shopiweb

    (4, 1): "1mhzRguo8Uc6NaABEOwF3tKGZD5aXUja3",   # Créatives publicitaires (récursif)
    (4, 2): "1dP1wNkqnQ-vPCuEgcZduwjeFU0ofu7uk",   # Facebook Ads (récursif)
    (4, 3): "1FxrkWzScF1LX6TG4oK1C4tWXpqY1xrFF",   # TikTok Ads (récursif)

    (5, 1): "14QDSssdyTOGSdesgt8RACu3hi-dFHXGJ",   # Marketing d'influence (récursif)
    (5, 2): "1LDo2BEQc_gwvHiHBwzXsRvmT328pB_GV",   # Google Ads
    (5, 3): "1ZNMwh0rtQukudWkVNwVBh_TQCWW_haU4",   # Snapchat Ads

    (6, 1): "1zm3QVo76VQKotABx2lS6wS-OQA5kHcgo",   # Pinterest Ads
    (6, 2): "1DrgjfRRtgPiDWB7b8gYEalHqsEVsHDVx",   # SEO (récursif, 2 études de cas nichées)
    (6, 3): "1Ux6zEzOyEP_EMG4ZwiMai-fZ9GmaXfVW",   # Email marketing (récursif)
    (6, 4): "1tbanuxfsXYSA14WOunNU7Y4HOzro3rPW",   # Interviews YomNation
    (6, 5): "1RyqxD013wvG4ydqXePMrBX3oLfxLl9og",   # Bonus Print on Demand
}


def lesson_files(phase_position, lesson_position):
    folder_id = LESSON_FOLDERS.get((phase_position, lesson_position))
    if not folder_id:
        return []
    return files_under(folder_id)


# ---------------------------------------------------------------------------
# Resources (ebooks / thèmes / bonus) -> Drive file id(s)
# ---------------------------------------------------------------------------

def ebook_files(title):
    mapping = {
        "La base — 100 000+ idées business": [
            f["name"] for f in _FOLDERS.get("EBOOK HMI 100K", {}).get("files", [])
            if f["name"].startswith("_EBOOK 100K")
        ],
        "100 Business — le guide complet": ["EBOOK-100-BUSINESS.pdf"],
        "25 Business Actifs": ["25 BUSINESS ACTIF .pdf"],
        "25 à 50 Business Actifs": ["25-50 BUSINESS ACTIF .pdf"],
        "25 Business Passifs": ["25 BUSINESS PASSIF.pdf"],
        "25 à 50 Business Passifs": ["25-50 BUSINESS PASSIF.pdf"],
        "Business Physique — guide complet": ["EBOOK POWER BUSINESS PHYSIQUE.pdf"],
        "Guide Expatriation — partie 1": ["EBOOK EXPATRIATION 1 (1).pdf"],
        "Guide Expatriation — partie 2": ["EBOOK EXPATRIATION 2 (1).pdf"],
        "Banque & fiscalité à l'étranger": ["banque.pdf", "Expat.pdf"],
        "Créer sa boutique Shopify de A à Z": ["EBOOK POWER CRÉATION D'UNE BOUTIQUE SHOPIFY DE A à Z.pdf"],
        "L'art de la négociation fournisseur": ["L'ART DE LA NEGOCIATION FOURNISSEUR EBOOK POWER 50K.pdf"],
        "Logistique & transitaire — guide complet": ["E-BOOK LOGISTIQUE+TRANSITAIRE.pdf"],
        "Marketing d'influence par plateforme": [
            "Twitch Marketing d'influence.pdf",
            "Youtube Marketing d'influence.pdf",
            "Instagram Marketing d'influence.pdf",
            "Tiktok Marketing d'influence.pdf",
            "X (Twitter) Marketing d'influence.pdf",
        ],
    }
    names = mapping.get(title, [])
    out = []
    for n in names:
        f = file_by_name("EBOOK HMI 100K", n)
        if f:
            out.append(f)
    return out


def theme_file(title):
    mapping = {
        "Basic": "Basic 3.1.0.zip",
        "Sylys": "Sylys 3.1.0.zip",
        "Shrine Pro": "Shrine_Pro_v1.1.4__186_sections (1).zip",
        "Olivia": "Olivia-15-2-7 (1).zip",
        "Minimog": "minimog-2.5.0.zip",
        "Impulse": "impulsetheme_1.zip",
        "Shoptimizer": "shoptimizer.zip",
        "Mogo": "mogo.zip",
        "Booster": "booster.zip",
        "Konversion": "konversion.zip",
        "Speedfly": "speedfly-1-13.zip",
        "Fastlane 2019": "Fastlane2019.zip",
        "Success Theme V2": "successTheme-V2.zip",
        "Theme Optimized 2.3": "theme_optimized_2-3.zip",
        "Turbo4": "turbo4.zip",
        "Venue": "venue.zip",
        "Motion": "motion.zip",
        "Prestige": "prestige.zip",
        "Pipeline": "pipeline (1).zip",
        "Triss": "Triss.zip",
        "Shopify Master Theme": "Shopify MASTER Theme.zip",
        "King Of Shopify": "Thème 🎁 King Of Shopify .zip",
    }
    filename = mapping.get(title)
    if not filename:
        return None
    return file_by_name("Thème payant shopify", filename)


def bonus_file(title):
    mapping = {
        "Formation création & code custom": "FORMA MATHYS + CODE CUSTOM",
        "Guide « 2ème cerveau » Notion": "2eme cerveau notion.pdf",
        "Formation complémentaire — trafic & closing": "Formation Marcus .txt",
        "Template planificateur personnel": "Islam Planner Notion.txt",
        "Code promo partenaire — outils de sourcing": "bonus ecom pro 2024.rtf",
    }
    filename = mapping.get(title)
    if not filename:
        return None
    return file_by_name("1%🧠", filename)


def drive_view_url(drive_id, mime_type=""):
    if mime_type == "application/vnd.google-apps.document":
        return f"https://docs.google.com/document/d/{drive_id}/view"
    return f"https://drive.google.com/file/d/{drive_id}/view"


def drive_preview_url(drive_id):
    return f"https://drive.google.com/file/d/{drive_id}/preview"
