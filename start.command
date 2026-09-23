#!/bin/bash
# Double-clic (macOS) ou ./start.command (Linux) : lance l'interface web.
cd "$(dirname "$0")" || exit 1
uv run python server.py
