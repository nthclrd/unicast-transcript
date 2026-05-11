#!/usr/bin/env python3
"""
Liste les podcasts d'une page de cours Unicast, permet la sélection interactive,
puis télécharge les fichiers choisis.

Usage:
    python unicast.py <url_du_cours> [--output-dir <dossier>]

Exemple:
    python unicast.py "https://my.unicast.uliege.be/mes_cours/INFO0902-A-a"
    python unicast.py "https://my.unicast.uliege.be/mes_cours/INFO0902-A-a" -o ./cours/

Sélection:
    1,3,5     individuel
    3-7       plage
    2026      tous ceux de l'année 2026
    all       tout
"""

import argparse
import re
import shutil
import subprocess
from pathlib import Path

import requests

import auth

UUID_RE = r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}"
BASE_URL = "https://my.unicast.uliege.be"


def _headers(cookies: str) -> dict:
    return {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/135.0", "Cookie": cookies}


def _fetch_html(url: str) -> tuple[str, str] | tuple[None, None]:
    cookies = auth.load_cookies()
    if not cookies:
        print("Pas de session. Lance d'abord: python auth.py")
        return None, None

    r = requests.get(url, headers=_headers(cookies))
    if r.status_code != 200:
        print("Session expirée, reconnexion...")
        auth.login()
        cookies = auth.load_cookies()
        r = requests.get(url, headers=_headers(cookies))

    if r.status_code != 200:
        print(f"Erreur {r.status_code} sur {url}")
        return None, None

    return r.text, cookies


def list_podcasts(course_url: str) -> tuple[str, list[dict], str]:
    """Retourne (student_id, podcasts, cookies). Chaque podcast: {id, title, date}."""
    html, cookies = _fetch_html(course_url)
    if html is None:
        return "", [], None

    student_match = re.search(r"window\.studentId\s*=\s*'([^']+)'", html)
    student_id = student_match.group(1) if student_match else ""

    blocks = re.findall(
        rf'class="podcast__link"[^>]*href="[^"]*?/({UUID_RE})[?"][^"]*".*?'
        r'class="podcast__title">([^<]+)</div>.*?'
        r'class="podcast__date[^"]*">([^<]+)</div>',
        html, re.DOTALL,
    )

    if blocks:
        podcasts = [{"id": pid, "title": t.strip(), "date": d.strip()} for pid, t, d in blocks]
    else:
        ids = re.findall(rf'data-podcast-id="({UUID_RE})"', html)
        seen: set = set()
        podcasts = [{"id": pid, "title": pid, "date": ""} for pid in ids if not (pid in seen or seen.add(pid))]

    return student_id, podcasts, cookies


def _parse_selection(raw: str, podcasts: list[dict]) -> list[int]:
    raw = raw.strip().lower()
    if raw in ("all", "a", ""):
        return list(range(len(podcasts)))
    if raw.isdigit() and len(raw) == 4:
        return [i for i, p in enumerate(podcasts) if raw in p.get("date", "")]
    indices: set = set()
    for part in raw.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            indices.update(range(int(a) - 1, int(b)))
        else:
            indices.add(int(part) - 1)
    return sorted(i for i in indices if 0 <= i < len(podcasts))


def download(podcast: dict, output_dir: Path, cookies: str, student_id: str = "") -> Path | None:
    """Télécharge un podcast et retourne le chemin du MP3."""
    pid = podcast["id"]
    headers = {**_headers(cookies), "Accept": "application/json"}
    params = {"studentId": student_id} if student_id else {}

    item = None
    for url in [f"{BASE_URL}/podcasts/{pid}", f"{BASE_URL}/api/podcasts/{pid}"]:
        r = requests.get(url, headers=headers, params=params)
        if r.status_code == 200:
            item = r.json().get("result", r.json())
            break

    if not item or not item.get("m3u8Urls"):
        print(f"  Impossible de récupérer le lien pour {pid}")
        return None

    title = re.sub(r'[\\/*?:"<>|]', "", item.get("name", pid)).strip()
    date = item.get("createdAt", "")[:10]
    filepath = output_dir / f"{date} - {title}.mp3"
    output_dir.mkdir(parents=True, exist_ok=True)

    if filepath.exists() and filepath.stat().st_size > 0:
        print(f"  Déjà présent : {filepath.name}")
        return filepath

    if not shutil.which("yt-dlp"):
        print("yt-dlp introuvable. Installe-le: pip install yt-dlp")
        return None

    result = subprocess.run(
        ["yt-dlp", item["m3u8Urls"][0], "--add-header", f"Cookie:{cookies}", "-x", "--audio-format", "mp3", "-o", str(filepath)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"  Erreur yt-dlp: {result.stderr[-300:]}")
        return None

    print(f"  Téléchargé : {filepath.name}")
    return filepath


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("url", help="URL de la page du cours Unicast")
    parser.add_argument("--output-dir", "-o", default=".", help="Dossier de sortie (défaut: .)")
    args = parser.parse_args()

    student_id, podcasts, cookies = list_podcasts(args.url)
    if not podcasts:
        print("Aucun podcast trouvé.")
        return

    print(f"\n{len(podcasts)} podcast(s) disponibles :\n")
    for i, p in enumerate(podcasts, 1):
        print(f"  {i:>3}.  [{p['date']}]  {p['title']}")

    print("\nSélection (ex: 1,3,5-7  |  2026  |  all) : ", end="")
    raw = input()
    indices = _parse_selection(raw, podcasts)
    if not indices:
        print("Aucune sélection.")
        return

    selected = [podcasts[i] for i in indices]
    print(f"\n{len(selected)} podcast(s) à télécharger.\n")

    output_dir = Path(args.output_dir)
    for i, p in enumerate(selected, 1):
        print(f"[{i}/{len(selected)}] {p['title']}")
        download(p, output_dir, cookies, student_id)

    print(f"\nTerminé. Fichiers dans : {output_dir.resolve()}")


if __name__ == "__main__":
    main()
