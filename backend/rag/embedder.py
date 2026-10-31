#Convert chunks into embeddings   # backend/rag/embedder.py

from typing import List, Dict
from threading import Lock


class CodeEmbedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        """Configure the model; load its weights only when embeddings are needed."""
        self.model_name = model_name
        self.model = None
        self._model_lock = Lock()

    def _get_model(self):
        """Load the embedding model once, keeping API startup independent of downloads."""
        if self.model is not None:
            return self.model

        with self._model_lock:
            if self.model is not None:
                return self.model

            print("Loading embedding model...")
            from sentence_transformers import SentenceTransformer

            try:
                self.model = SentenceTransformer(self.model_name, local_files_only=True)
            except Exception:
                # Download only when the first embedding operation actually needs it.
                self.model = SentenceTransformer(self.model_name, local_files_only=False)
            print("Embedding model loaded successfully.")
            return self.model

    def embed_text(self, text: str):
        """Embed a retrieval query with the same model used for indexed chunks."""
        return self._get_model().encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    def embed_chunks(self, chunks: List[Dict], batch_size: int = 512) -> List[Dict]:
        """
        Generate embeddings for each chunk.
        Processes in batches to handle large projects without memory issues.

        Returns the same chunk dictionary with an added 'embedding' key.
        """
        import numpy as np

        texts = [chunk["content"] for chunk in chunks]
        total = len(texts)

        if total == 0:
            return []

        print(f"Embedding {total} chunks in batches of {batch_size}...")
        model = self._get_model()

        all_embeddings = []

        for start in range(0, total, batch_size):
            end = min(start + batch_size, total)
            batch_texts = texts[start:end]

            batch_embeddings = model.encode(
                batch_texts,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            all_embeddings.append(batch_embeddings)
            print(f"  Embedded batch {start // batch_size + 1}/{(total + batch_size - 1) // batch_size} ({end}/{total} chunks)")

        embeddings = np.vstack(all_embeddings)

        embedded_chunks = []

        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding
            embedded_chunks.append(chunk)

        return embedded_chunks


if __name__ == "__main__":

    from loader import ProjectLoader
    from chunker import CodeChunker

    loader = ProjectLoader("../")
    documents = loader.load()

    chunker = CodeChunker()
    chunks = chunker.chunk_documents(documents)

    embedder = CodeEmbedder()

    embedded_chunks = embedder.embed_chunks(chunks)

    print("\nTotal Embedded Chunks:", len(embedded_chunks))

    print("\nExample:\n")

    sample = embedded_chunks[0]

    print("Chunk ID :", sample["chunk_id"])
    print("File     :", sample["name"])
    print("Vector Size :", len(sample["embedding"]))
