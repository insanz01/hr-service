import os
import warnings
import time
import random
import logging
from typing import List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore", category=ResourceWarning, message=".*unclosed.*SSL.*")
warnings.filterwarnings("ignore", message=".*Failed to send telemetry event.*")

try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception as e:
    raise RuntimeError(f"Chromadb tidak tersedia: {e}")


def _rag_retry_with_backoff(func, *args, max_retries=3, base_delay=0.5, **kwargs):
    """
    Enhanced retry function with exponential backoff for RAG operations.

    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        *args, **kwargs: Arguments to pass to function

    Returns:
        Function result if successful

    Raises:
        RuntimeError: If all retries fail
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            result = func(*args, **kwargs)
            if attempt > 0:
                logger.info(f"RAG operation succeeded after {attempt} retries")
            return result

        except Exception as e:
            last_exception = e
            error_str = str(e).lower()

            # ChromaDB specific error patterns
            is_retryable = (
                "connection" in error_str or
                "timeout" in error_str or
                "unavailable" in error_str or
                "busy" in error_str or
                "overloaded" in error_str or
                "failed to" in error_str or
                "i/o" in error_str or
                "permission" in error_str or
                "disk" in error_str or
                "memory" in error_str or
                "invalid collection" in error_str
            )

            if not is_retryable:
                logger.error(f"Non-retryable RAG error: {e}")
                raise RuntimeError(f"RAG operation failed with non-retryable error: {str(e)}")

            if attempt == max_retries:
                logger.error(f"Max retries ({max_retries}) reached for RAG operation")
                raise RuntimeError(f"RAG operation failed after {max_retries} retries: {str(e)}")

            # Calculate exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0.2, 0.8)
            delay = min(delay, 15)  # Cap at 15 seconds

            logger.warning(f"RAG operation failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {delay:.2f}s: {e}")
            time.sleep(delay)

    raise RuntimeError(f"RAG operation failed after {max_retries} retries. Last error: {last_exception}")

# Lokasi penyimpanan ChromaDB (persist)
RAG_DIR = os.path.join(os.path.dirname(__file__), "uploads", "chroma")
os.makedirs(RAG_DIR, exist_ok=True)

# Initialize ChromaDB with retry mechanism
def _initialize_chromadb():
    """Initialize ChromaDB with retry and recovery mechanisms"""
    try:
        client = chromadb.PersistentClient(path=RAG_DIR)
        embedder = embedding_functions.DefaultEmbeddingFunction()
        collection = client.get_or_create_collection(
            name="system_docs", embedding_function=embedder
        )
        logger.info("ChromaDB initialized successfully")
        return client, embedder, collection
    except Exception as e:
        logger.error(f"ChromaDB initialization failed: {e}")
        logger.info("Attempting to reset ChromaDB storage...")

        # Reset ChromaDB if schema incompatible
        import shutil

        if os.path.exists(RAG_DIR):
            try:
                shutil.rmtree(RAG_DIR)
                os.makedirs(RAG_DIR, exist_ok=True)
                logger.info("ChromaDB storage reset successfully")
            except Exception as reset_error:
                logger.error(f"Failed to reset ChromaDB storage: {reset_error}")
                raise RuntimeError(f"ChromaDB initialization and reset both failed: {e}, {reset_error}")

        # Re-initialize after reset
        client = chromadb.PersistentClient(path=RAG_DIR)
        embedder = embedding_functions.DefaultEmbeddingFunction()
        collection = client.get_or_create_collection(
            name="system_docs", embedding_function=embedder
        )
        logger.info("ChromaDB reinitialized successfully after reset")
        return client, embedder, collection

try:
    _client, _embedder, _collection = _rag_retry_with_backoff(
        _initialize_chromadb,
        max_retries=3,
        base_delay=1.0
    )
    logger.info("ChromaDB initialization completed with retry mechanism")
except Exception as e:
    logger.error(f"Failed to initialize ChromaDB after retries: {e}")
    raise RuntimeError(f"ChromaDB initialization failed after multiple attempts: {str(e)}")


def ingest_text(doc_id: str, text: str, metadata: Dict[str, Any] | None = None) -> None:
    """Ingest plain text ke koleksi Chroma dengan id unik dan retry mechanism."""
    if not text:
        return

    def _ingest_operation():
        _collection.add(documents=[text], metadatas=[metadata or {}], ids=[doc_id])
        return True

    return _rag_retry_with_backoff(_ingest_operation, max_retries=3, base_delay=0.8)


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
    """Query dokumen relevan dari koleksi dengan retry mechanism."""
    if not query_text:
        return []

    def _query_operation():
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

    return _rag_retry_with_backoff(_query_operation, max_retries=4, base_delay=0.5)


def test_rag_query() -> bool:
    """Test RAG query functionality with a simple query"""
    try:
        # Perform a simple test query
        result = query("test", n_results=1)
        return True  # If no exception occurs, consider it working
    except Exception:
        return False
