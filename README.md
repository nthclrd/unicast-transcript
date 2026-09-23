# Unicast Transcriber

Télécharge et transcrit automatiquement les podcasts de cours depuis [Unicast ULiège](https://my.unicast.uliege.be), depuis une interface web locale.

## 1. Installer les prérequis (une seule fois)

- [uv](https://docs.astral.sh/uv/getting-started/installation/) : lance le programme et installe ses dépendances Python
- [ffmpeg](https://ffmpeg.org/) : conversion audio

```bash
# macOS
brew install uv ffmpeg

# Windows (PowerShell)
winget install astral-sh.uv
winget install Gyan.FFmpeg

# Linux (Debian/Ubuntu)
sudo apt update && sudo apt install ffmpeg
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Puis récupère le projet :

```bash
git clone https://github.com/nthclrd/unicast-transcript.git
cd unicast-transcript
```

> Pas besoin de Node.js : l'interface est déjà compilée dans `frontend/dist`.

## 2. Lancer l'application

- **Windows** : double-clic sur `start.bat`
- **macOS** : double-clic sur `start.command` (au premier lancement : clic droit, puis **Ouvrir**)
- **Linux** : `./start.command` dans un terminal
- **N'importe où** : `uv run python server.py`

Le premier lancement prend une minute (installation des dépendances et du navigateur de connexion). Ton navigateur s'ouvre ensuite sur **http://127.0.0.1:8000**. Garde la fenêtre du terminal ouverte tant que tu utilises l'application.

## 3. Utilisation

1. **Réglages** (s'ouvrent tout seuls au premier lancement) : ton matricule ULiège, ton mot de passe et une clé API [Deepgram](https://console.deepgram.com/) (compte gratuit, nécessaire seulement pour la transcription).
2. **Cours** : clique sur un de tes cours. La liste vient directement de ta page « Mes cours » Unicast. Tu peux aussi coller l'URL d'une page de cours.
3. **Podcasts** : coche ceux à traiter. Tu peux filtrer par titre ou par date, ou tout sélectionner.
4. **Options** : dossier de sortie (par défaut `./CODE_DU_COURS`), langue du cours, et transcription activée ou non.
5. **Lancer** : suis la progression. À la fin, **Voir le texte** affiche le transcript et **Ouvrir le dossier** ouvre les fichiers.

Chaque podcast donne un `.mp3`, plus un `.txt` avec le transcript si la transcription est activée.

### Où sont stockées mes infos ?

Tout reste sur ton ordinateur. Les identifiants et la clé Deepgram sont dans le fichier `.env`, et la session Unicast dans `cookies.json`. Les deux sont ignorés par git. Le serveur écoute uniquement sur `127.0.0.1`, il n'est pas accessible depuis le réseau.

### Problèmes fréquents

| Message | Solution |
|---------|----------|
| « Cours introuvable (500) » | L'URL est fausse, ou tu n'es pas inscrit à ce cours. Choisis-le plutôt dans la liste. |
| « Aucun podcast publié pour ce cours » | Le cours n'a encore aucun enregistrement sur Unicast. |
| Échec de la connexion | Vérifie ton matricule et ton mot de passe dans **Réglages**, puis **Se reconnecter**. |
| « Clé Deepgram manquante » | Ajoute la clé dans **Réglages**, ou décoche la transcription. |
| `yt-dlp` / `ffmpeg` introuvable | Réinstalle ffmpeg (étape 1) puis relance l'application. |

La session Unicast expire régulièrement. L'application se reconnecte automatiquement avec tes identifiants.

---

## Utilisation en ligne de commande (avancé)

Les scripts d'origine restent disponibles. Configure d'abord `.env` à la main :

```bash
cp .env.example .env
uv sync
uv run playwright install chromium
```

```env
ULIEGE_USER=s1234567
ULIEGE_PASS=ton_mot_de_passe
DEEPGRAM_API_KEY=...
```

**Tout-en-un interactif** (connexion, sélection, téléchargement, transcription) :

```bash
uv run python run.py
```

**Étape par étape** :

```bash
uv run python auth.py                                                    # connexion
uv run python unicast.py "https://my.unicast.uliege.be/mes_cours/INFO0902-A-a" -o ./info0902/
uv run python transcribe.py ./info0902/ --language fr                     # fichier ou dossier MP3/MP4
```

Syntaxe de sélection dans le terminal :

| Syntaxe | Résultat |
|---------|----------|
| `1,3,5` | podcasts 1, 3 et 5 |
| `3-7`   | podcasts 3 à 7 |
| `2026`  | tous ceux de l'année 2026 |
| `all`   | tout |

## Développement de l'interface

Frontend : Vite, React, Tailwind et [shadcn/ui](https://ui.shadcn.com/), dans `frontend/`. Backend : FastAPI (`server.py`), qui réutilise `auth.py`, `unicast.py` et `transcribe.py`.

```bash
# Terminal 1 : API
uv run python server.py

# Terminal 2 : frontend avec rechargement à chaud (proxy /api vers le port 8000)
cd frontend
pnpm install
pnpm dev
```

Après une modification du frontend, recompile avec `pnpm build` et versionne `frontend/dist` : les utilisateurs n'ont pas Node.
