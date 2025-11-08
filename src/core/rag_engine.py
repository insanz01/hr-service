import os
import warnings
from typing import List, Dict, Any

# Suppress warnings
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*SSL.*")
warnings.filterwarnings("ignore", message=".*Failed to send telemetry event.*")

try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception as e:
    raise RuntimeError(f"Chromadb tidak tersedia: {e}")

# Lokasi penyimpanan ChromaDB (persist)
RAG_DIR = os.path.join(os.path.dirname(__file__), "uploads", "chroma")
os.makedirs(RAG_DIR, exist_ok=True)

# Initialize ChromaDB with fallback for schema issues
try:
    _client = chromadb.PersistentClient(path=RAG_DIR)
    _embedder = embedding_functions.DefaultEmbeddingFunction()
    _collection = _client.get_or_create_collection(
        name="system_docs", embedding_function=_embedder
    )
except Exception as e:
    print(f"Warning: ChromaDB initialization failed: {e}")
    print("Attempting to reset ChromaDB storage...")

    # Reset ChromaDB if schema incompatible
    import shutil

    if os.path.exists(RAG_DIR):
        shutil.rmtree(RAG_DIR)
        os.makedirs(RAG_DIR, exist_ok=True)

    # Re-initialize
    _client = chromadb.PersistentClient(path=RAG_DIR)
    _embedder = embedding_functions.DefaultEmbeddingFunction()
    _collection = _client.get_or_create_collection(
        name="system_docs", embedding_function=_embedder
    )
    print("ChromaDB reinitialized successfully")


def ingest_text(doc_id: str, text: str, metadata: Dict[str, Any] | None = None) -> None:
    """Ingest plain text ke koleksi Chroma dengan id unik."""
    if not text:
        return
    _collection.add(documents=[text], metadatas=[metadata or {}], ids=[doc_id])


def ingest_file(
    path: str, doc_type: str | None = None, title: str | None = None
) -> str:
    """Baca file (PDF atau TXT) dan ingest ke Chroma. Mengembalikan document id."""
    text = ""
    try:
        if path.lower().endswith(".pdf"):
            # Use PyMuPDF for better PDF reading (same as worker)
            try:
                import fitz  # PyMuPDF

                doc = fitz.open(path)
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                print(
                    f"✅ RAG Engine: Successfully read PDF with PyMuPDF: {len(text)} characters"
                )
            except ImportError:
                print(
                    "⚠️  RAG Engine: PyMuPDF (fitz) not available, trying PyPDF2 fallback"
                )
                # Fallback to PyPDF2 if available
                try:
                    from PyPDF2 import PdfReader

                    reader = PdfReader(path)
                    text = "\n\n".join((p.extract_text() or "") for p in reader.pages)
                    print(
                        f"✅ RAG Engine: Fallback to PyPDF2 successful: {len(text)} characters"
                    )
                except ImportError:
                    print("❌ RAG Engine: PyPDF2 also not available")
                    text = ""
                except Exception as e:
                    print(f"❌ RAG Engine: PyPDF2 reading failed: {e}")
                    text = ""
            except Exception as e:
                print(f"❌ RAG Engine: Error reading PDF with PyMuPDF {path}: {e}")
                text = ""
        else:
            # Read as text file
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            print(f"✅ RAG Engine: Successfully read text file: {len(text)} characters")
    except Exception as e:
        print(f"❌ RAG Engine: Error reading file {path}: {e}")
        text = ""

    doc_id = f"file:{os.path.basename(path)}:{abs(hash(path))}"
    if text:  # Only ingest if we got content
        ingest_text(
            doc_id,
            text,
            metadata={
                "path": path,
                "doc_type": doc_type or "system",
                "title": title or os.path.basename(path),
            },
        )
        print(f"✅ RAG Engine: Successfully ingested document {doc_id}")
    else:
        print(f"⚠️  RAG Engine: No content found in file {path}, skipping ingest")

    return doc_id


def has_id(doc_id: str) -> bool:
    try:
        res = _collection.get(ids=[doc_id])
        return bool(res and res.get("ids"))
    except Exception:
        return False


def query(query_text: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """Query dokumen relevan dari koleksi."""
    if not query_text:
        return []
    res = _collection.query(query_texts=[query_text], n_results=n_results)
    docs = []
    for i, d in enumerate(res.get("documents", [[]])[0]):
        docs.append(
            {
                "document": d,
                "metadata": res.get("metadatas", [[]])[0][i],
                "id": res.get("ids", [[]])[0][i],
                "distance": res.get("distances", [[]])[0][i]
                if "distances" in res
                else None,
            }
        )
    return docs


def test_rag_query() -> bool:
    """Test RAG query functionality with a simple query"""
    try:
        # Perform a simple test query
        result = query("test", n_results=1)
        return True  # If no exception occurs, consider it working
    except Exception:
        return False
