# Unicast Transcriber

Télécharge et transcrit automatiquement les podcasts de cours depuis [Unicast ULiège](https://my.unicast.uliege.be).

## Prérequis

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — gestionnaire de paquets Python
- [ffmpeg](https://ffmpeg.org/) — conversion audio (MP4 → MP3)

```bash
# macOS
brew install uv ffmpeg

# Linux (Debian/Ubuntu)
sudo apt update && sudo apt install ffmpeg
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
winget install astral-sh.uv
winget install Gyan.FFmpeg
```

## Installation

```bash
git clone <repo>
cd unicast-transcriber

# Installer les dépendances
uv sync

# Installer le navigateur pour la connexion automatique
uv run playwright install chromium
```

## Configuration

Copie le fichier `.env.example` et remplis tes identifiants :

```bash
cp .env.example .env
```

```env
ULIEGE_USER=s1234567          # ton matricule ULiège
ULIEGE_PASS=ton_mot_de_passe

DEEPGRAM_API_KEY=...          # https://console.deepgram.com/ (compte gratuit)
```

## Utilisation

### 1. Connexion

À faire une seule fois (ou si la session expire) :

```bash
uv run python auth.py
```

### 2. Télécharger des podcasts

```bash
uv run python unicast.py "https://my.unicast.uliege.be/mes_cours/INFO0902-A-a"

# Avec un dossier de sortie
uv run python unicast.py "https://my.unicast.uliege.be/mes_cours/INFO0902-A-a" -o ./cours/
```

Une liste interactive s'affiche :

```
31 podcast(s) disponibles :

    1.  [06/02/2026]  INFO0902 - Introduction
    2.  [13/02/2026]  INFO0902 - Complexité (partie 1)
  ...

Sélection (ex: 1,3,5-7  |  2026  |  all) :
```

| Syntaxe | Résultat |
|---------|----------|
| `1,3,5` | podcasts 1, 3 et 5 |
| `3-7`   | podcasts 3 à 7 |
| `2026`  | tous ceux de l'année 2026 |
| `all`   | tout télécharger |

### 3. Transcrire

```bash
# Un seul fichier (MP3 ou MP4)
uv run python transcribe.py cours.mp3

# Tout un dossier
uv run python transcribe.py ./cours/
```

Le transcript est sauvegardé à côté du fichier audio avec l'extension `.txt`.

## Workflow typique

```bash
uv run python auth.py
uv run python unicast.py "https://my.unicast.uliege.be/mes_cours/INFO0902-A-a" -o ./info0902/
uv run python transcribe.py ./info0902/
```
