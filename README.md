# METHOD 1% — Espace élève

Application web fonctionnelle (Flask + SQLite) : connexion, tableau de bord,
feuille de route avec suivi de progression réel, et bibliothèque de contenu.

## Lancer en local

```bash
pip install -r requirements.txt
python database.py     # crée et remplit la base de données (method1.db)
python app.py           # démarre le serveur sur http://localhost:5050
```

Compte de démonstration (pré-rempli sur l'écran de connexion) :
- Email : `eleve@method1.com`
- Mot de passe : `method1%`

## Ce qui est réellement fonctionnel

- **Comptes & connexion** : mots de passe hachés (Werkzeug), sessions sécurisées.
- **Base de données SQLite** : `users`, `phases`, `lessons`, `progress`, `resources`.
- **Suivi de progression réel** : chaque sous-module de chaque étape est cochable ;
  les pourcentages, badges "Terminé / En cours / Verrouillé" et le déblocage de
  l'étape suivante sont calculés en direct depuis la base — rien n'est en dur.
- **Contenu réel** : les 7 étapes avec leurs vrais sous-modules, les 14 ebooks,
  les 22 thèmes Shopify et les bonus, tels qu'inventoriés dans le dossier Drive.

## Ce qu'il reste à faire avant d'ouvrir ça à de vrais élèves

1. **Hébergement des fichiers eux-mêmes** (vidéos, PDF, ZIP de thèmes). Ce
   projet ne stocke que les *métadonnées* (titres, descriptions) — pas les
   fichiers. Vu le volume (~60-100 Go de vidéo, 38 PDF, 22 thèmes), il faudra
   un service de stockage/streaming vidéo adapté (ex. Bunny.net, Mux, Vimeo
   Pro, ou un bucket S3/R2 + un lecteur vidéo) plutôt que de tout héberger
   soi-même — coûts et bande passante à anticiper.
2. **Créer les comptes élèves** : pour l'instant il n'y a qu'un compte de
   démo. Il faudra soit un formulaire d'inscription, soit un système où toi
   (l'admin) crées les comptes après une vente.
3. **Déploiement en ligne** : ce projet tourne en local pour l'instant. Pour
   le mettre en ligne, des options simples : Render, Railway ou Fly.io
   (gratuit ou pas cher pour démarrer). Il faudra remplacer SQLite par une
   base plus robuste pour la production (ex. PostgreSQL) si le nombre
   d'élèves grandit.
4. **Nom de domaine** (ex. app.method1.fr) à connecter une fois déployé.
5. Optionnel : paiement/abonnement intégré (Stripe) si tu veux que le SaaS
   gère lui-même l'accès payant plutôt que de créer les comptes à la main.

## Structure du projet

```
app.py              # routes Flask (connexion, dashboard, roadmap, bibliothèque)
database.py         # schéma SQLite + contenu (à modifier pour changer le programme)
templates/
  base.html          # structure commune (sidebar, styles)
  login.html
  dashboard.html
  roadmap.html
  library.html
```

Pour changer le contenu (titres de modules, ebooks, thèmes, bonus), tout se
modifie dans `database.py` (listes `PHASES`, `LESSONS`, `RESOURCES`) puis on
relance `python database.py` pour régénérer la base.
