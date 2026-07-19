# backend/rag/vector_store.py

import os
import pickle
from typing import Dict, List

import faiss
import numpy as np


class VectorStore:
    """
    Stores and retrieves vector embeddings using FAISS.
    """

    def __init__(self, embedding_dimension=384):
        """
        all-MiniLM-L6-v2 produces 384-dimensional embeddings.
        """

        self.embedding_dimension = embedding_dimension
        self.index = faiss.IndexFlatL2(embedding_dimension)
        self.metadata = []

    # --------------------------------------------------
    # Add embeddings to FAISS
    # --------------------------------------------------

    def add_chunks(self, embedded_chunks: List[Dict]):

        vectors = []

        for chunk in embedded_chunks:

            vectors.append(chunk["embedding"])

            self.metadata.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "path": chunk["path"],
                    "name": chunk["name"],
                    "extension": chunk["extension"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "content": chunk["content"],
                }
            )

        vectors = np.array(vectors).astype("float32")

        self.index.add(vectors)

        print(f"Indexed {len(vectors)} chunks.")

    # --------------------------------------------------
    # Search Similar Chunks
    # --------------------------------------------------

    def search(self, query_embedding, top_k=5):

        query_embedding = np.array([query_embedding]).astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)

        results = []

        for idx, distance in zip(indices[0], distances[0]):

            if idx == -1:
                continue

            result = self.metadata[idx].copy()

            result["distance"] = float(distance)

            results.append(result)

        return results

    # --------------------------------------------------
    # Save Vector Database
    # --------------------------------------------------

    def save(
        self,
        index_path="vector_db/faiss.index",
        metadata_path="vector_db/metadata.pkl",
    ):

        os.makedirs(os.path.dirname(index_path), exist_ok=True)

        faiss.write_index(self.index, index_path)

        with open(metadata_path, "wb") as f:
            pickle.dump(self.metadata, f)

        print("Vector database saved successfully.")

    # --------------------------------------------------
    # Load Vector Database
    # --------------------------------------------------

    def load(
        self,
        index_path="vector_db/faiss.index",
        metadata_path="vector_db/metadata.pkl",
    ):

        if not os.path.exists(index_path):
            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(
                f"Metadata file not found: {metadata_path}"
            )

        self.index = faiss.read_index(index_path)

        with open(metadata_path, "rb") as f:
            self.metadata = pickle.load(f)

        print(f"Loaded {len(self.metadata)} chunks from vector database.")