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
    """
    Queries ChromaDB for relevant context documents.
    Returns a formatted string ready to inject into a prompt.
    """
    collection = get_collection()

    where_filter = {"module": module}
    if doc_types and len(doc_types) == 1:
        where_filter["type"] = doc_types[0]

    try:
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )

        documents = results.get("documents", [[]])[0]
        if not documents:
            return ""

        context_parts = []
        for i, doc in enumerate(documents):
            context_parts.append(f"[Context {i+1}]: {doc}")

        return "\n\n".join(context_parts)

    except Exception:
        return ""


def get_agent_context(module: str, level: str, agent_profile: str) -> str:
    return query_context(
        module=module,
        level=level,
        query_text=f"agent behavior {agent_profile}",
        doc_types=["agent_profile"],
        n_results=2
    )


def get_evaluation_context(module: str, level: str) -> str:
    return query_context(
        module=module,
        level=level,
        query_text=f"evaluation criteria {module} {level}",
        doc_types=["evaluation_criteria"],
        n_results=2
    )


def get_example_context(module: str, level: str) -> str:
    return query_context(
        module=module,
        level=level,
        query_text=f"example response {module} {level}",
        doc_types=["example_response"],
        n_results=1
    )


def get_full_context(module: str, level: str, agent_profile: str) -> dict:
    """
    Returns all relevant context for a challenge in a structured dict.
    """
    return {
        "agent_context": get_agent_context(module, level, agent_profile),
        "evaluation_context": get_evaluation_context(module, level),
        "example_context": get_example_context(module, level)
    }