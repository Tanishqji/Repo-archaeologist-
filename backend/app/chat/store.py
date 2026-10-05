import logging
import os
import re
from typing import Any, Dict, List, Optional
from app.chat.chunker import CodeChunk
from app.config import get_settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.settings = get_settings()
        self.chroma_client = None
        self._fallback_store: Dict[str, List[CodeChunk]] = {}

        try:
            # pyrefly: ignore [missing-import]
            import chromadb
            os.makedirs(self.settings.chroma_dir, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(path=self.settings.chroma_dir)
        except Exception as e:
            logger.warning(f"ChromaDB initialization failed: {e}. Using in-memory keyword retrieval fallback.")

    def _collection_name(self, owner: str, repo: str, sha: str) -> str:
        clean_sha = sha[:12] if sha else "latest"
        name = f"{owner.lower()}__{repo.lower()}__{clean_sha}".replace("-", "_").replace(".", "_")
        # Ensure collection name meets Chroma requirements (3-63 chars)
        return name[:63]

    async def index_chunks(self, owner: str, repo: str, sha: str, chunks: List[CodeChunk]) -> None:
        if not chunks:
            return

        col_name = self._collection_name(owner, repo, sha)
        self._fallback_store[col_name] = chunks

        if self.chroma_client:
            try:
                # Delete existing collection if present
                try:
                    self.chroma_client.delete_collection(col_name)
                except Exception:
                    pass

                col = self.chroma_client.create_collection(
                    name=col_name,
                    metadata={"hnsw:space": "cosine"},
                )

                # Batch add chunks
                batch_size = 100
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i : i + batch_size]
                    col.add(
                        ids=[c.chunk_id for c in batch],
                        documents=[c.content for c in batch],
                        metadatas=[{"file_path": c.file_path, "start_line": c.start_line, "end_line": c.end_line} for c in batch],
                    )
            except Exception as e:
                logger.warning(f"Failed to index chunks in ChromaDB: {e}")

    async def search(self, owner: str, repo: str, sha: str, query: str, top_k: int = 4) -> List[CodeChunk]:
        col_name = self._collection_name(owner, repo, sha)

        # Try ChromaDB query
        if self.chroma_client:
            try:
                col = self.chroma_client.get_collection(col_name)
                results = col.query(query_texts=[query], n_results=top_k)
                if results and results.get("ids") and results["ids"][0]:
                    matched_chunks: List[CodeChunk] = []
                    for chunk_id, doc, meta in zip(
                        results["ids"][0], results["documents"][0], results["metadatas"][0]
                    ):
                        matched_chunks.append(
                            CodeChunk(
                                chunk_id=chunk_id,
                                file_path=meta["file_path"],
                                start_line=meta["start_line"],
                                end_line=meta["end_line"],
                                content=doc,
                            )
                        )
                    return matched_chunks
            except Exception as e:
                logger.debug(f"ChromaDB search query failed: {e}")

        # In-memory keyword matching fallback
        cached_chunks = self._fallback_store.get(col_name, [])
        query_words = set(re.findall(r"\w+", query.lower()))
        scored: List[tuple[int, CodeChunk]] = []

        for chunk in cached_chunks:
            chunk_words = set(re.findall(r"\w+", chunk.content.lower()))
            overlap = len(query_words.intersection(chunk_words))
            if overlap > 0:
                scored.append((overlap, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]
