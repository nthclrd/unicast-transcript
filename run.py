#!/usr/bin/env python3
"""
Script interactif tout-en-un : connexion, téléchargement et transcription
des podcasts Unicast en une seule commande.

Usage:
    uv run python run.py

Aucun argument : tout se passe via les questions posées à l'écran.
"""

import re
import sys
from pathlib import Path

import auth
import transcribe
import unicast

# Langues fréquentes proposées dans le menu. La langue n'est PAS figée :
# on peut toujours taper n'importe quel code accepté par Deepgram.
COMMON_LANGUAGES = [
    ("fr", "Français"),
    ("en", "Anglais"),
    ("multi", "Multilingue (détection auto)"),
    ("nl", "Néerlandais"),
    ("de", "Allemand"),
    ("es", "Espagnol"),
]
DEFAULT_LANGUAGE = "fr"


def ask(prompt: str, default: str = "") -> str:
    """Pose une question avec valeur par défaut (Entrée = défaut)."""
    suffix = f" [{default}]" if default else ""
    answer = input(f"{prompt}{suffix} : ").strip()
    return answer or default


def ensure_login() -> bool:
    """Vérifie la session ; lance la connexion si nécessaire."""
    if auth.load_cookies():
        print("Session existante détectée.")
        return True
    print("Aucune session trouvée, connexion à Unicast...")
    return auth.login()


def ask_url() -> str:
    print('\nExemple : https://my.unicast.uliege.be/mes_cours/INFO0902-A-a')
    while True:
        url = ask("URL de la page du cours")
        if "unicast.uliege.be" in url:
            return url
        print("URL invalide (doit contenir 'unicast.uliege.be'). Réessaie.")


def default_output_dir(url: str) -> str:
    """Devine un dossier de sortie à partir du code de cours dans l'URL."""
    code = re.search(r"[A-Z]{2,}\d{3,}", url)
    if code:
        return f"./{code.group(0)}"
    slug = url.rstrip("/").split("/")[-1] or "podcasts"
    return f"./{slug}"


def ask_language() -> str:
    print("\nLangue de transcription :")
    for i, (code, label) in enumerate(COMMON_LANGUAGES, 1):
        print(f"  {i}. {label} ({code})")
    print("  Ou tape directement un autre code Deepgram (ex: it, pt).")

    raw = ask("Choix", DEFAULT_LANGUAGE)
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(COMMON_LANGUAGES):
            return COMMON_LANGUAGES[idx][0]
        print(f"Numéro hors liste, utilisation de '{DEFAULT_LANGUAGE}'.")
        return DEFAULT_LANGUAGE
    return raw


def select_podcasts(podcasts: list[dict]) -> list[dict]:
    print(f"\n{len(podcasts)} podcast(s) disponibles :\n")
    for i, p in enumerate(podcasts, 1):
        print(f"  {i:>3}.  [{p['date']}]  {p['title']}")

    raw = ask("\nSélection (ex: 1,3,5-7  |  2026  |  all)", "all")
    indices = unicast._parse_selection(raw, podcasts)
    return [podcasts[i] for i in indices]


def main() -> None:
    print("=== Unicast : téléchargement + transcription ===")

    if not ensure_login():
        print("Connexion impossible. Vérifie tes identifiants dans .env.")
        return

    url = ask_url()

    student_id, podcasts, cookies = unicast.list_podcasts(url)
    if not podcasts:
        print("Aucun podcast trouvé sur cette page.")
        return

    selected = select_podcasts(podcasts)
    if not selected:
        print("Aucune sélection.")
        return

    output_dir = Path(ask("\nDossier de sortie", default_output_dir(url)))
    language = ask_language()

    print(f"\n{len(selected)} podcast(s) à traiter — langue : {language}")
    print(f"Dossier : {output_dir.resolve()}\n")

    downloaded = 0
    transcribed = 0
    for i, p in enumerate(selected, 1):
        print(f"[{i}/{len(selected)}] {p['title']}")
        try:
            mp3 = unicast.download(p, output_dir, cookies, student_id)
        except Exception as e:
            print(f"  Erreur téléchargement : {e}")
            continue
        if not mp3:
            continue
        downloaded += 1
        try:
            transcribe.transcribe(mp3, language=language)
            transcribed += 1
        except Exception as e:
            print(f"  Erreur transcription : {e}")

    print(f"\nTerminé. {downloaded} téléchargé(s), {transcribed} transcrit(s).")
    print(f"Fichiers dans : {output_dir.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompu.")
        sys.exit(130)
