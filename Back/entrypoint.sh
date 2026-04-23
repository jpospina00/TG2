#!/bin/bash
set -e

echo "Iniciando backend..."

python seed.py
python chromadb_data/load_chroma.py

exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}