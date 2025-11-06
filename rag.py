import os
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception as e:
    raise RuntimeError(f"Chromadb tidak tersedia: {e}")

# Lokasi penyimpanan ChromaDB (persist)
RAG_DIR = os.path.join(os.path.dirname(__file__), 'uploads', 'chroma')
os.makedirs(RAG_DIR, exist_ok=True)

_client = chromadb.PersistentClient(path=RAG_DIR)
_embedder = embedding_functions.DefaultEmbeddingFunction()
_collection = _client.get_or_create_collection(name="system_docs", embedding_function=_embedder)


def ingest_text(doc_id: str, text: str, metadata: Dict[str, Any] | None = None) -> None:
    """Ingest plain text ke koleksi Chroma dengan id unik."""
    if not text:
        return
    _collection.add(documents=[text], metadatas=[metadata or {}], ids=[doc_id])


def ingest_file(path: str, doc_type: str | None = None, title: str | None = None) -> str:
    """Baca file (PDF atau TXT) dan ingest ke Chroma. Mengembalikan document id."""
    text = ''
    try:
        if path.lower().endswith('.pdf'):
            from PyPDF2 import PdfReader
            reader = PdfReader(path)
            text = "\n\n".join((p.extract_text() or '') for p in reader.pages)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
    except Exception:
        pass

    doc_id = f"file:{os.path.basename(path)}:{abs(hash(path))}"
    ingest_text(doc_id, text, metadata={
        'path': path,
        'doc_type': doc_type or 'unknown',
        'title': title or os.path.basename(path),
    })
    return doc_id


def has_id(doc_id: str) -> bool:
    try:
        res = _collection.get(ids=[doc_id])
        return bool(res and res.get('ids'))
    except Exception:
        return False


def query(query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """Query dokumen relevan dari koleksi."""
    if not query_text:
        return []
    res = _collection.query(query_texts=[query_text], n_results=n_results)
    docs = []
    for i, d in enumerate(res.get('documents', [[]])[0]):
        docs.append({
            'document': d,
            'metadata': res.get('metadatas', [[]])[0][i],
            'id': res.get('ids', [[]])[0][i],
            'distance': res.get('distances', [[]])[0][i] if 'distances' in res else None,
        })
    return docs