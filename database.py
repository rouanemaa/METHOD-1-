import sqlite3
import os
from werkzeug.security import generate_password_hash
import drive_links

DB_PATH = os.path.join(os.path.dirname(__file__), "method1.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    hours_estimate INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase_id INTEGER NOT NULL REFERENCES phases(id),
    position INTEGER NOT NULL,
    title TEXT NOT NULL,
    sub_count INTEGER NOT NULL DEFAULT 1,
    sub_unit TEXT NOT NULL DEFAULT 'leçon'
);

CREATE TABLE IF NOT EXISTS progress (
    user_id INTEGER NOT NULL REFERENCES users(id),
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    completed INTEGER NOT NULL DEFAULT 0,
    completed_at TEXT,
    PRIMARY KEY (user_id, lesson_id)
);

CREATE TABLE IF NOT EXISTS resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,          -- 'ebook' | 'theme' | 'bonus'
    title TEXT NOT NULL,
    subtitle TEXT NOT NULL,
    tag TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id INTEGER NOT NULL REFERENCES lessons(id),
    position INTEGER NOT NULL,
    name TEXT NOT NULL,
    drive_id TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS resource_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL REFERENCES resources(id),
    position INTEGER NOT NULL,
    name TEXT NOT NULL,
    drive_id TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT ''
);
"""

PHASES = [
    # (position, title, description, hours)
    (1, "Mindset & Fondations", "Pose les bases : l'état d'esprit entrepreneur, tes objectifs, et tout ce qu'il faut savoir légalement et fiscalement avant de te lancer.", 8),
    (2, "Trouver ton offre", "Recherche produit, sourcing, positionnement et branding : construis une offre solide avant même d'avoir un site.", 9),
    (3, "Créer ta boutique", "Mets en ligne ton site, paramètre-le, optimise-le pour la conversion — que tu partes d'un thème mono-produit ou multi-produits.", 14),
    (4, "Lancer tes premières pubs", "Créatives publicitaires, Facebook Ads et TikTok Ads : les fondamentaux pour générer tes premières ventes.", 11),
    (5, "Scaler ton trafic", "Google Ads, marketing d'influence et Snapchat Ads pour diversifier et augmenter ton trafic payant.", 9),
    (6, "Fidéliser & optimiser", "SEO, email marketing et automatisations : fais revenir tes clients et fais durer ton business.", 16),
    (7, "Bonus — Aller plus loin", "Ebooks, thèmes premium et ressources exclusives METHOD 1% pour continuer à progresser après le programme.", 0),
]

LESSONS = {
    1: [
        ("Mindset — état d'esprit & 7 commandements", 4, "leçons"),
        ("Finance & fiscalité (France, Belgique, Suisse, international)", 13, "leçons"),
    ],
    2: [
        ("IA en e-commerce", 1, "leçon"),
        ("Business model e-commerce", 1, "leçon"),
        ("Quelle source de trafic choisir", 1, "leçon"),
        ("Recherche de produit", 1, "leçon"),
        ("Le sourcing", 1, "leçon"),
        ("Positionnement & recherche de marché", 1, "leçon"),
        ("Le branding", 1, "leçon"),
        ("Masterclass sourcing avancé", 1, "leçon"),
        ("Étude de cas — marque en dropshipping", 1, "leçon"),
        ("Création de marque avec stock", 1, "leçon"),
        ("Étude de cas — marque avec stock", 1, "leçon"),
        ("Bonus — importation niveau avancé", 1, "leçon"),
    ],
    3: [
        ("Création & optimisation de site (mono-produit / multi-produits)", 11, "leçons"),
        ("Annexe & outils boutique (avis, upsells, RGPD, chatbot IA…)", 17, "leçons"),
        ("Thème signature METHOD 1%", 12, "leçons"),
    ],
    4: [
        ("Créatives publicitaires (structure, UGC, montage)", 12, "leçons"),
        ("Facebook Ads (compte, tracking, scaling)", 10, "leçons"),
        ("TikTok Ads (organique & payant)", 8, "leçons"),
    ],
    5: [
        ("Marketing d'influence (sourcing & campagnes)", 6, "leçons"),
        ("Google Ads (Shopping, Search, Performance Max)", 8, "leçons"),
        ("Snapchat Ads", 7, "leçons"),
    ],
    6: [
        ("Pinterest Ads", 5, "leçons"),
        ("SEO (mots-clés, backlinks, arborescence)", 21, "leçons"),
        ("Email marketing (flows, segmentation, campagnes)", 10, "leçons"),
        ("Interviews & retours d'expérience élèves", 14, "leçons"),
        ("Bonus — Print on Demand", 1, "leçon"),
    ],
    7: [
        ("Pack ebooks METHOD 1%", 14, "ebooks"),
        ("Pack thèmes Shopify premium", 22, "thèmes"),
        ("Ressources & guides complémentaires", 5, "ressources"),
    ],
}

RESOURCES = [
    # ebooks
    ("ebook", "La base — 100 000+ idées business", "Ressources", "PDF"),
    ("ebook", "100 Business — le guide complet", "Ressources", "PDF"),
    ("ebook", "25 Business Actifs", "Ressources", "PDF"),
    ("ebook", "25 à 50 Business Actifs", "Ressources", "PDF"),
    ("ebook", "25 Business Passifs", "Ressources", "PDF"),
    ("ebook", "25 à 50 Business Passifs", "Ressources", "PDF"),
    ("ebook", "Business Physique — guide complet", "Ressources", "PDF"),
    ("ebook", "Guide Expatriation — partie 1", "Ressources", "PDF"),
    ("ebook", "Guide Expatriation — partie 2", "Ressources", "PDF"),
    ("ebook", "Banque & fiscalité à l'étranger", "Ressources", "PDF"),
    ("ebook", "Créer sa boutique Shopify de A à Z", "Ressources", "PDF"),
    ("ebook", "L'art de la négociation fournisseur", "Ressources", "PDF"),
    ("ebook", "Logistique & transitaire — guide complet", "Ressources", "PDF"),
    ("ebook", "Marketing d'influence par plateforme", "TikTok · Instagram · YouTube · Twitch · X", "PDF"),
    # themes
    ("theme", "Basic", "Thème Shopify", "ZIP"),
    ("theme", "Sylys", "Thème Shopify", "ZIP"),
    ("theme", "Shrine Pro", "Thème Shopify", "ZIP"),
    ("theme", "Olivia", "Thème Shopify", "ZIP"),
    ("theme", "Minimog", "Thème Shopify", "ZIP"),
    ("theme", "Impulse", "Thème Shopify", "ZIP"),
    ("theme", "Shoptimizer", "Thème Shopify", "ZIP"),
    ("theme", "Mogo", "Thème Shopify", "ZIP"),
    ("theme", "Booster", "Thème Shopify", "ZIP"),
    ("theme", "Konversion", "Thème Shopify", "ZIP"),
    ("theme", "Speedfly", "Thème Shopify", "ZIP"),
    ("theme", "Fastlane 2019", "Thème Shopify", "ZIP"),
    ("theme", "Success Theme V2", "Thème Shopify", "ZIP"),
    ("theme", "Theme Optimized 2.3", "Thème Shopify", "ZIP"),
    ("theme", "Turbo4", "Thème Shopify", "ZIP"),
    ("theme", "Venue", "Thème Shopify", "ZIP"),
    ("theme", "Motion", "Thème Shopify", "ZIP"),
    ("theme", "Prestige", "Thème Shopify", "ZIP"),
    ("theme", "Pipeline", "Thème Shopify", "ZIP"),
    ("theme", "Triss", "Thème Shopify", "ZIP"),
    ("theme", "Shopify Master Theme", "Thème Shopify", "ZIP"),
    ("theme", "King Of Shopify", "Thème Shopify", "ZIP"),
    # bonus
    ("bonus", "Formation création & code custom", "Formation vidéo + bibliothèque de code Liquid", "Accès"),
    ("bonus", "Guide « 2ème cerveau » Notion", "Organisation & productivité", "Notion"),
    ("bonus", "Formation complémentaire — trafic & closing", "Accès formation externe", "Accès"),
    ("bonus", "Template planificateur personnel", "Organisation & productivité", "Notion"),
    ("bonus", "Code promo partenaire — outils de sourcing", "Réduction 30% à vie", "Code"),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(reset=False):
    fresh = reset or not os.path.exists(DB_PATH)
    conn = get_db()
    conn.executescript(SCHEMA)

    if fresh:
        cur = conn.cursor()

        cur.execute("DELETE FROM progress")
        cur.execute("DELETE FROM lesson_files")
        cur.execute("DELETE FROM lessons")
        cur.execute("DELETE FROM phases")
        cur.execute("DELETE FROM resource_files")
        cur.execute("DELETE FROM resources")
        cur.execute("DELETE FROM users")

        phase_ids = {}
        for position, title, description, hours in PHASES:
            cur.execute(
                "INSERT INTO phases (position, title, description, hours_estimate) VALUES (?,?,?,?)",
                (position, title, description, hours),
            )
            phase_ids[position] = cur.lastrowid

        lesson_ids_by_phase = {}
        for position, items in LESSONS.items():
            pid = phase_ids[position]
            ids = []
            for i, (title, sub_count, sub_unit) in enumerate(items, start=1):
                cur.execute(
                    "INSERT INTO lessons (phase_id, position, title, sub_count, sub_unit) VALUES (?,?,?,?,?)",
                    (pid, i, title, sub_count, sub_unit),
                )
                lesson_id = cur.lastrowid
                ids.append(lesson_id)

                for fpos, f in enumerate(drive_links.lesson_files(position, i), start=1):
                    cur.execute(
                        "INSERT INTO lesson_files (lesson_id, position, name, drive_id, mime_type) VALUES (?,?,?,?,?)",
                        (lesson_id, fpos, f["name"], f["drive_id"], f["mime_type"]),
                    )
            lesson_ids_by_phase[position] = ids

        for category, title, subtitle, tag in RESOURCES:
            cur.execute(
                "INSERT INTO resources (category, title, subtitle, tag) VALUES (?,?,?,?)",
                (category, title, subtitle, tag),
            )
            resource_id = cur.lastrowid

            if category == "ebook":
                files = drive_links.ebook_files(title)
            elif category == "theme":
                f = drive_links.theme_file(title)
                files = [f] if f else []
            else:
                f = drive_links.bonus_file(title)
                files = [f] if f else []

            for fpos, f in enumerate(files, start=1):
                cur.execute(
                    "INSERT INTO resource_files (resource_id, position, name, drive_id, mime_type) VALUES (?,?,?,?,?)",
                    (resource_id, fpos, f["name"], f["drive_id"], f["mime_type"]),
                )

        # admin account (Marouane)
        cur.execute(
            "INSERT INTO users (email, password_hash, name, is_admin) VALUES (?,?,?,1)",
            ("admin@method1.com", generate_password_hash("admin1%"), "Marouane"),
        )

        # demo student accounts
        demo_students = [
            ("eleve@method1.com", "method1%", "Léa Martin"),
            ("youssef@method1.com", "method1%", "Youssef B."),
            ("camille@method1.com", "method1%", "Camille R."),
        ]
        student_ids = []
        for email, password, name in demo_students:
            cur.execute(
                "INSERT INTO users (email, password_hash, name, is_admin) VALUES (?,?,?,0)",
                (email, generate_password_hash(password), name),
            )
            student_ids.append(cur.lastrowid)

        # seed progress so the admin view has something to show:
        # Léa Martin: phase 1 & 2 fully done, phase 3 partly done
        lea_id = student_ids[0]
        for lid in lesson_ids_by_phase[1] + lesson_ids_by_phase[2]:
            cur.execute(
                "INSERT INTO progress (user_id, lesson_id, completed, completed_at) VALUES (?,?,1,CURRENT_TIMESTAMP)",
                (lea_id, lid),
            )
        for lid in lesson_ids_by_phase[3][:2]:
            cur.execute(
                "INSERT INTO progress (user_id, lesson_id, completed, completed_at) VALUES (?,?,1,CURRENT_TIMESTAMP)",
                (lea_id, lid),
            )

        # Youssef B.: just started, phase 1 partly done
        youssef_id = student_ids[1]
        for lid in lesson_ids_by_phase[1][:1]:
            cur.execute(
                "INSERT INTO progress (user_id, lesson_id, completed, completed_at) VALUES (?,?,1,CURRENT_TIMESTAMP)",
                (youssef_id, lid),
            )

        # Camille R.: brand new, no progress yet

        conn.commit()

    conn.close()


def create_user(email, name, password, is_admin=0):
    """Create a new user account. Returns the new user id, or None if the email already exists."""
    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if existing:
        conn.close()
        return None
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (email, password_hash, name, is_admin) VALUES (?,?,?,?)",
        (email.strip().lower(), generate_password_hash(password), name.strip(), is_admin),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


if __name__ == "__main__":
    init_db(reset=True)
    print("Base de données initialisée :", DB_PATH)
