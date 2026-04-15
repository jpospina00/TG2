"""
RAG service — queries ChromaDB to retrieve relevant context
before sending prompts to Groq.
"""
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

BASE_DIR = Path(__file__).resolve().parent.parent / "chromadb_data"
CHROMA_DIR = str(BASE_DIR / "chroma_db")

_client = None
_collection = None


def get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        _collection = _client.get_or_create_collection(
            name="system_context",
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def query_context(
    module: str,
    level: str,
    query_text: str,
    doc_types: list[str] = None,
    n_results: int = 3
) -> str:
    collection = get_collection()

    # Filtro base por módulo
    where_filter = {"module": module}

    # Agregar filtro por level solo si no es "all"
    if level and level != "all":
        if doc_types and len(doc_types) == 1:
            where_filter = {
                "$and": [
                    {"module": {"$eq": module}},
                    {"level": {"$eq": level}},
                    {"type": {"$eq": doc_types[0]}},
                ]
            }
        else:
            where_filter = {
                "$and": [
                    {"module": {"$eq": module}},
                    {"level": {"$eq": level}},
                ]
            }
    else:
        if doc_types and len(doc_types) == 1:
            where_filter = {
                "$and": [
                    {"module": {"$eq": module}},
                    {"type": {"$eq": doc_types[0]}},
                ]
            }

    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )

        documents = results.get("documents", [[]])[0]
        if not documents:
            return ""

        return "\n\n".join([f"[Context {i+1}]: {doc}" for i, doc in enumerate(documents)])

    except Exception:
        return ""


def get_agent_context(module: str, level: str, agent_profile: str) -> str:
    return query_context(
        module=module,
        level=level,
        query_text=f"comportamiento del agente {agent_profile} {module}",
        doc_types=["agent_profile"],
        n_results=2
    )


def get_evaluation_context(module: str, level: str) -> str:
    return query_context(
        module=module,
        level=level,
        query_text=f"criterios de evaluación {module} {level}",
        doc_types=["evaluation_criteria"],
        n_results=2
    )


def get_example_context(module: str, level: str) -> str:
    return query_context(
        module=module,
        level=level,
        query_text=f"ejemplo de respuesta excelente {module} {level}",
        doc_types=["example_response"],
        n_results=1
    )


def get_challenge_pattern(module: str, level: str) -> str:
    return query_context(
        module=module,
        level=level,
        query_text=f"patrón de reto {module} nivel {level}",
        doc_types=["challenge_pattern"],
        n_results=1
    )


def get_personalization_guide(module: str) -> str:
    return query_context(
        module=module,
        level="all",
        query_text=f"guía de personalización {module}",
        doc_types=["personalization_guide"],
        n_results=1
    )


def get_full_context(module: str, level: str, agent_profile: str) -> dict:
    """
    Retorna todo el contexto relevante para un reto.
    Ahora incluye challenge_pattern y personalization_guide correctamente.
    """
    return {
        "agent_context": get_agent_context(module, level, agent_profile),
        "evaluation_context": get_evaluation_context(module, level),
        "example_context": get_example_context(module, level),
        "challenge_pattern": get_challenge_pattern(module, level),
        "personalization_guide": get_personalization_guide(module),
    }