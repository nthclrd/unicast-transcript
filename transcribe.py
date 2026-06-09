#!/usr/bin/env python3
"""
Transcrit un ou plusieurs fichiers audio (MP3/MP4) avec Deepgram.
Le transcript est sauvegardé à côté du fichier source avec l'extension .txt.

Usage:
    python transcribe.py <fichier.mp3>
    python transcribe.py <fichier.mp4>
    python transcribe.py <dossier/>
"""

import argparse
import os
import subprocess
from pathlib import Path

from deepgram import DeepgramClient
from dotenv import load_dotenv


def _convert_to_mp3(input_path: Path) -> Path:
    mp3_path = input_path.with_suffix(".mp3")
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path), "-vn", "-acodec", "libmp3lame", "-ab", "64k", "-ac", "1", "-ar", "16000", str(mp3_path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg a échoué:\n{result.stderr.decode('utf-8', errors='ignore')}")
    print(f"  Converti : {input_path.name} → {mp3_path.name}")
    return mp3_path


def _get_client() -> DeepgramClient:
    load_dotenv()
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPGRAM_API_KEY manquant dans .env")
    return DeepgramClient(api_key=api_key)


def transcribe(audio_path: Path, language: str = "en") -> Path:
    """Transcrit un fichier audio et retourne le chemin du .txt généré."""
    if audio_path.suffix.lower() == ".mp4":
        mp3_path = _convert_to_mp3(audio_path)
    else:
        mp3_path = audio_path

    client = _get_client()
    with open(mp3_path, "rb") as f:
        response = client.listen.v1.media.transcribe_file(
            request=f.read(),
            model="nova-3",
            language=language,
            request_options={"timeout_in_seconds": 600, "max_retries": 2},
        )

    transcript = response.results.channels[0].alternatives[0].transcript
    out = audio_path.with_suffix(".txt")
    out.write_text(transcript, encoding="utf-8")
    print(f"  Transcript : {out.name}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", help="Fichier MP3/MP4 ou dossier contenant des MP3/MP4")
    parser.add_argument("--language", "-l", default="en",
                        help="Langue de l'audio (ex: en, fr, multi). Défaut: en")
    args = parser.parse_args()

    target = Path(args.input)

    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(f for f in target.iterdir() if f.suffix.lower() in (".mp3", ".mp4"))
        if not files:
            print(f"Aucun MP3/MP4 trouvé dans {target}")
            return
    else:
        print(f"Chemin introuvable : {target}")
        return

    print(f"{len(files)} fichier(s) à transcrire.\n")
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name}")
        try:
            transcribe(f, language=args.language)
        except Exception as e:
            print(f"  Erreur : {e}")

    print("\nTerminé.")


if __name__ == "__main__":
    main()
