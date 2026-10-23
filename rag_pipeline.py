"""
RAG Pipeline for Academic Assignment Evaluation System.

Provides local, persistent vector storage and semantic retrieval of
course notes, lecture PDFs, and reference materials using Sentence Transformers
and ChromaDB.

Workflow:
Reference Documents -> Text Extraction -> Overlapping Chunking ->
Local Embeddings -> ChromaDB Persistence -> Context Retrieval -> Rubric Evaluation

Guiding Principle:
Retrieved context serves strictly as supporting evidence. The approved rubric
remains the primary scoring authority.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on Windows consoles to prevent cp1252 charmap encoding errors
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import chromadb
from chromadb.api.models.Collection import Collection


def get_embedding_function(model_name: str = "all-MiniLM-L6-v2"):
    """
    Returns a local embedding function based on the Sentence Transformers model.
    
    Attempts to initialize chromadb's SentenceTransformerEmbeddingFunction first.
    If native PyTorch dynamic libraries are blocked by host OS security policies
    (e.g., Windows Application Control / WinError 4551), it seamlessly falls back to
    Chroma's ONNXMiniLM_L6_V2 / DefaultEmbeddingFunction, which executes the exact
    same all-MiniLM-L6-v2 model weights entirely locally via ONNX Runtime.
    """
    try:
        from chromadb.utils import embedding_functions
        # Test if PyTorch-based SentenceTransformer is importable and runnable
        fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
        # Probe one test embedding to verify DLL loading
        fn(["probe"])
        return fn
    except Exception:
        # Fallback to local ONNX runtime implementation of all-MiniLM-L6-v2
        from chromadb.utils import embedding_functions
        return embedding_functions.DefaultEmbeddingFunction()


def load_document(file_path: str | Path) -> List[Dict[str, Any]]:
    """
    Loads text from a single document file (.pdf, .txt, .md, .markdown).
    
    Returns a list of document units with keys:
    - 'text': string content
    - 'source': basename of the file
    - 'file_path': absolute or relative string path
    - 'page': integer page number (1-indexed for PDF; 1 for text/markdown)
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Reference file not found: {path}")

    ext = path.suffix.lower()
    source_name = path.name
    results: List[Dict[str, Any]] = []

    if ext == ".pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            for page_idx, page in enumerate(reader.pages, start=1):
                try:
                    page_text = page.extract_text() or ""
                except Exception:
                    page_text = ""
                cleaned_text = page_text.strip()
                if cleaned_text:
                    results.append({
                        "text": cleaned_text,
                        "source": source_name,
                        "file_path": str(path.as_posix()),
                        "page": page_idx
                    })
        except Exception as e:
            print(f"[!] Warning: Failed to parse PDF {path.name}: {e}", file=sys.stderr)

    elif ext in [".txt", ".md", ".markdown"]:
        content = ""
        for encoding in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                content = path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        cleaned_text = content.strip()
        if cleaned_text:
            results.append({
                "text": cleaned_text,
                "source": source_name,
                "file_path": str(path.as_posix()),
                "page": 1
            })
    else:
        # Unsupported format, return empty list
        pass

    return results


def load_reference_materials(directory_path: str | Path) -> List[Dict[str, Any]]:
    """
    Loads all supported reference documents (.pdf, .txt, .md, .markdown)
    from the specified directory.
    """
    dir_path = Path(directory_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Reference materials directory not found: {dir_path}")

    documents: List[Dict[str, Any]] = []
    valid_extensions = {".pdf", ".txt", ".md", ".markdown"}

    for item in sorted(dir_path.iterdir()):
        if item.is_file() and item.suffix.lower() in valid_extensions:
            docs = load_document(item)
            documents.extend(docs)

    return documents


def split_text_overlapping(
    text: str, chunk_size: int = 500, chunk_overlap: int = 100
) -> List[str]:
    """
    Splits text into overlapping chunks of approximately chunk_size characters,
    respecting paragraph or sentence boundaries where possible.
    """
    if not text:
        return []

    # Defensive bounds checking on chunk parameters
    chunk_size = max(chunk_size, 50)
    chunk_overlap = max(0, min(chunk_overlap, chunk_size - 10))

    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0
    text_len = len(text)
    step = max(chunk_size - chunk_overlap, 1)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        
        # If we haven't reached the end, try to break at a natural boundary (newline or period)
        if end < text_len:
            # Look backwards from end up to (chunk_size // 4) chars for a clean boundary
            boundary_found = -1
            boundary_window = text[max(start, end - 120):end]
            
            # Prefer double newline, single newline, or sentence end
            for delim in ("\n\n", "\n", ". "):
                last_pos = boundary_window.rfind(delim)
                if last_pos != -1:
                    boundary_found = max(start, end - 120) + last_pos + len(delim)
                    break

            if boundary_found > start + (chunk_size // 2):
                end = boundary_found

        chunk_str = text[start:end].strip()
        if chunk_str:
            chunks.append(chunk_str)

        if end >= text_len:
            break

        start = start + step
        # Guard against zero progress
        if start <= 0 or start >= text_len:
            break

    return chunks


def chunk_documents(
    documents: List[Dict[str, Any]],
    chunk_size: int = 500,
    chunk_overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Converts document units into chunk records with detailed metadata and unique IDs.
    """
    all_chunks: List[Dict[str, Any]] = []

    for doc in documents:
        raw_text = doc["text"]
        source = doc["source"]
        page = doc.get("page", 1)
        file_path = doc.get("file_path", "")

        text_pieces = split_text_overlapping(raw_text, chunk_size, chunk_overlap)
        total_pieces = len(text_pieces)

        for idx, piece in enumerate(text_pieces, start=1):
            # Clean identifier for ChromaDB
            clean_source = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", source)
            chunk_id = f"{clean_source}_p{page}_c{idx}"

            all_chunks.append({
                "id": chunk_id,
                "text": piece,
                "metadata": {
                    "source": source,
                    "page": int(page),
                    "file_path": file_path,
                    "chunk_index": idx,
                    "total_chunks": total_pieces
                }
            })

    return all_chunks


class RAGPipeline:
    """
    Manages persistent local vector database indexing and retrieval
    for academic reference materials.
    """

    def __init__(
        self,
        persist_directory: str = "chroma_db",
        collection_name: str = "course_reference_materials",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.model_name = model_name

        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize local persistent client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.embedding_function = get_embedding_function(model_name=self.model_name)

        # Get or create collection
        self.collection: Collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"description": "Approved course notes, lecture PDFs, and references", "hnsw:space": "cosine"}
        )

    def ingest_directory(
        self,
        directory_path: str = "Data/reference_materials",
        chunk_size: int = 500,
        chunk_overlap: int = 100
    ) -> Dict[str, Any]:
        """
        Loads all reference files, splits them into overlapping chunks,
        and stores them in persistent local ChromaDB.
        """
        docs = load_reference_materials(directory_path)
        if not docs:
            return {
                "status": "EMPTY",
                "message": f"No supported reference documents found in {directory_path}",
                "chunks_ingested": 0,
                "files": []
            }

        chunks = chunk_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        if not chunks:
            return {
                "status": "EMPTY",
                "message": "Documents contained no extractable text chunks",
                "chunks_ingested": 0,
                "files": []
            }

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        # ChromaDB upsert handles additions and updates idempotently
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

        unique_files = sorted(list({c["metadata"]["source"] for c in chunks}))

        return {
            "status": "SUCCESS",
            "message": f"Successfully ingested {len(chunks)} chunks into ChromaDB",
            "chunks_ingested": len(chunks),
            "files": unique_files,
            "collection_count": self.collection.count()
        }

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves the top_k most relevant chunks for a given query.
        
        Each result contains:
        - 'content': text chunk
        - 'source': reference filename
        - 'page': page number (where applicable)
        - 'distance': distance metric (lower is more similar)
        - 'similarity_score': 1 - distance (normalized cosine proximity)
        - 'metadata': complete chunk metadata
        """
        total_items = self.collection.count()
        if total_items == 0 or top_k <= 0:
            return []

        actual_k = max(1, min(top_k, total_items))

        query_args: Dict[str, Any] = {
            "query_texts": [query],
            "n_results": actual_k
        }
        if where_filter:
            query_args["where"] = where_filter

        results = self.collection.query(**query_args)

        retrieved: List[Dict[str, Any]] = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, dists):
                sim_score = round(1.0 - dist, 4) if dist is not None else None
                retrieved.append({
                    "content": doc_text,
                    "source": meta.get("source", "Unknown Reference"),
                    "page": meta.get("page", 1),
                    "distance": dist,
                    "similarity_score": sim_score,
                    "metadata": meta
                })

        return retrieved

    def retrieve_for_rubric_evaluation(
        self,
        question_title: str,
        criterion_text: str,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Retrieves supporting academic reference context for a specific rubric criterion.
        Enforces the principle that retrieved context is supporting evidence only,
        and flags if no relevant reference context is found.
        """
        query = f"{question_title}: {criterion_text}"
        chunks = self.retrieve(query=query, top_k=top_k)

        if not chunks:
            return {
                "question": question_title,
                "criterion": criterion_text,
                "status": "UNAVAILABLE",
                "message": "No reference context available in course repository. Evaluated strictly against approved rubric.",
                "chunks": []
            }

        return {
            "question": question_title,
            "criterion": criterion_text,
            "status": "AVAILABLE",
            "message": "Supporting reference context retrieved.",
            "chunks": chunks
        }

    def format_context_for_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved chunks into clear, cited text suitable for inclusion
        in the rubric-evaluation stage.
        """
        if not chunks:
            return "No supporting reference context available in course database. Scoring strictly based on rubric."

        lines: List[str] = [
            "### Retrieved Reference Material (Supporting Evidence Only)",
            "> NOTE: The approved rubric remains the primary scoring authority. "
            "Use retrieved context only as supporting academic evidence.\n"
        ]

        for i, chunk in enumerate(chunks, start=1):
            source = chunk.get("source", "Reference")
            page = chunk.get("page", 1)
            content = chunk.get("content", "").replace("\n", " ").strip()
            lines.append(f"[{i}] Source: `{source}` | Page: {page}")
            lines.append(f'    "{content}"\n')

        return "\n".join(lines)


# Standalone functions for external modules
_default_pipeline: Optional[RAGPipeline] = None


def get_pipeline(
    persist_directory: str = "chroma_db",
    collection_name: str = "course_reference_materials"
) -> RAGPipeline:
    """Returns a singleton or configured RAGPipeline instance."""
    global _default_pipeline
    if _default_pipeline is None or _default_pipeline.persist_directory != persist_directory:
        _default_pipeline = RAGPipeline(
            persist_directory=persist_directory,
            collection_name=collection_name
        )
    return _default_pipeline


def ingest_reference_materials(
    directory_path: str = "Data/reference_materials",
    persist_directory: str = "chroma_db"
) -> Dict[str, Any]:
    """Ingests all files from the reference materials directory."""
    pipeline = get_pipeline(persist_directory=persist_directory)
    return pipeline.ingest_directory(directory_path=directory_path)


def retrieve_context(
    query: str,
    top_k: int = 4,
    persist_directory: str = "chroma_db"
) -> List[Dict[str, Any]]:
    """Retrieves top_k context chunks for a query."""
    pipeline = get_pipeline(persist_directory=persist_directory)
    return pipeline.retrieve(query=query, top_k=top_k)


def main():
    parser = argparse.ArgumentParser(
        description="RAG Pipeline for Assignment Evaluation System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest reference materials")
    ingest_parser.add_argument(
        "--data-dir",
        default="Data/reference_materials",
        help="Path to reference materials folder (default: Data/reference_materials)"
    )
    ingest_parser.add_argument(
        "--db-dir",
        default="chroma_db",
        help="Path to ChromaDB persistent storage (default: chroma_db)"
    )

    # Query command
    query_parser = subparsers.add_parser("query", help="Retrieve relevant chunks for a query")
    query_parser.add_argument("query_text", type=str, help="Search query")
    query_parser.add_argument(
        "--top-k",
        type=int,
        default=4,
        help="Number of chunks to retrieve (default: 4)"
    )
    query_parser.add_argument(
        "--db-dir",
        default="chroma_db",
        help="Path to ChromaDB persistent storage (default: chroma_db)"
    )

    args = parser.parse_args()

    if args.command == "ingest":
        print(f"[*] Ingesting reference materials from: {args.data_dir}")
        pipeline = RAGPipeline(persist_directory=args.db_dir)
        summary = pipeline.ingest_directory(directory_path=args.data_dir)
        print(f"[+] Status: {summary['status']}")
        print(f"[+] Ingested Chunks: {summary.get('chunks_ingested', 0)}")
        print(f"[+] Files: {', '.join(summary.get('files', []))}")
        print(f"[+] Total Collection Count: {summary.get('collection_count', 0)}")

    elif args.command == "query":
        print(f"[*] Querying ChromaDB for: '{args.query_text}' (top {args.top_k})")
        pipeline = RAGPipeline(persist_directory=args.db_dir)
        results = pipeline.retrieve(query=args.query_text, top_k=args.top_k)
        if not results:
            print("[-] No relevant chunks found.")
            return

        for idx, res in enumerate(results, start=1):
            print(f"\n--- Result {idx} ---")
            print(f"Source: {res['source']} (Page {res['page']})")
            if res.get('similarity_score') is not None:
                print(f"Similarity Score: {res['similarity_score']}")
            print(f"Content:\n{res['content']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
