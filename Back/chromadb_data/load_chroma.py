"""
Script to load curated JSON content into ChromaDB.
Run once before starting the system: python chromadb_data/load_chroma.py
"""
import json
import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = str(BASE_DIR / "chroma_db")
EMPATHY_JSON = BASE_DIR / "empathy.json"
NETWORKING_JSON = BASE_DIR / "networking.json"

# ── ChromaDB client ───────────────────────────────────────────────────────────
client = chromadb.PersistentClient(path=CHROMA_DIR)

# Usar el embedding function por defecto de ChromaDB (sentence-transformers)
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# ── Colección única ───────────────────────────────────────────────────────────
collection = client.get_or_create_collection(
    name="system_context",
    embedding_function=embedding_fn,
    metadata={"hnsw:space": "cosine"}
)

def load_json(filepath: Path) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_to_chroma(documents: list[dict]):
    ids = []
    contents = []
    metadatas = []

    for i, doc in enumerate(documents):
        # Soportar tanto formato inglés como español
        module = doc.get("module") or doc.get("modulo")
        type_ = doc.get("type") or doc.get("tipo")
        level = doc.get("level") or doc.get("nivel")
        content = doc.get("content") or doc.get("contenido")

        doc_id = f"{module}_{type_}_{level}_{i}"
        ids.append(doc_id)
        contents.append(content)
        metadatas.append({
            "module": module,
            "type": type_,
            "level": level
        })

    existing = collection.get(ids=ids)
    existing_ids = set(existing["ids"])

    new_ids, new_contents, new_metadatas = [], [], []
    for id_, content, metadata in zip(ids, contents, metadatas):
        if id_ not in existing_ids:
            new_ids.append(id_)
            new_contents.append(content)
            new_metadatas.append(metadata)

    if new_ids:
        collection.add(
            ids=new_ids,
            documents=new_contents,
            metadatas=new_metadatas
        )
        print(f"Added {len(new_ids)} documents to ChromaDB.")
    else:
        print("All documents already exist in ChromaDB. Skipping.")

if __name__ == "__main__":
    print("Loading empathy documents...")
    empathy_docs = load_json(EMPATHY_JSON)
    load_to_chroma(empathy_docs)

    print("Loading networking documents...")
    networking_docs = load_json(NETWORKING_JSON)
    load_to_chroma(networking_docs)

    print(f"\nTotal documents in collection: {collection.count()}")
    print("ChromaDB loaded successfully.")