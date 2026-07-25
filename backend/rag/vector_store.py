# backend/rag/vector_store.py

import os
import pickle
from typing import Dict, List

import faiss
import numpy as np


class VectorStore:
    """
    Stores and retrieves code embeddings using FAISS.

    FAISS stores the numerical vectors.
    metadata.pkl stores information associated with each vector.
    """

    def __init__(self, embedding_dimension: int = 384):

        self.embedding_dimension = embedding_dimension

        self.index = faiss.IndexFlatL2(
            embedding_dimension
        )

        self.metadata = []

    # ==================================================
    # Add Chunks
    # ==================================================

    def add_chunks(
        self,
        embedded_chunks: List[Dict]
    ):

        if not embedded_chunks:

            raise ValueError(
                "No embedded chunks were provided."
            )

        vectors = []

        # Important:
        # Reset metadata before building a new index.
        self.metadata = []

        for chunk in embedded_chunks:

            embedding = chunk.get("embedding")

            if embedding is None:

                print(
                    f"Skipping chunk "
                    f"{chunk.get('chunk_id', 'Unknown')} "
                    f"because embedding is missing."
                )

                continue

            vectors.append(embedding)

            # ------------------------------------------
            # Store all information required later
            # during retrieval and prompt generation.
            # ------------------------------------------

            self.metadata.append(
                {
                    "chunk_id": chunk.get(
                        "chunk_id"
                    ),

                    "path": chunk.get(
                        "path",
                        "Unknown"
                    ),

                    "relative_path": chunk.get(
                        "relative_path",
                        chunk.get(
                            "path",
                            "Unknown"
                        )
                    ),

                    "name": chunk.get(
                        "name",
                        "Unknown"
                    ),

                    "extension": chunk.get(
                        "extension",
                        ""
                    ),

                    "language": chunk.get(
                        "language",
                        "Unknown"
                    ),

                    "start_line": chunk.get(
                        "start_line"
                    ),

                    "end_line": chunk.get(
                        "end_line"
                    ),

                    # Plain code used for semantic meaning
                    "content": chunk.get(
                        "content",
                        ""
                    ),

                    # Code containing original source
                    # line numbers for grounded reviews
                    "numbered_content": chunk.get(
                        "numbered_content",
                        ""
                    ),
                }
            )

        if not vectors:

            raise ValueError(
                "No valid embeddings were available "
                "to create the FAISS index."
            )

        # ----------------------------------------------
        # Convert vectors to FAISS-compatible format
        # ----------------------------------------------

        vectors = np.asarray(
            vectors,
            dtype="float32"
        )

        # ----------------------------------------------
        # Validate embedding dimensions
        # ----------------------------------------------

        if vectors.ndim != 2:

            raise ValueError(
                "Embeddings must be a 2-dimensional array."
            )

        if vectors.shape[1] != self.embedding_dimension:

            raise ValueError(
                f"Embedding dimension mismatch. "
                f"Expected {self.embedding_dimension}, "
                f"received {vectors.shape[1]}."
            )

        # ----------------------------------------------
        # Create a fresh FAISS index
        # ----------------------------------------------

        self.index = faiss.IndexFlatL2(
            self.embedding_dimension
        )

        self.index.add(vectors)

        print(
            f"Indexed {len(vectors)} chunks."
        )

    # ==================================================
    # Search
    # ==================================================

    def search(
        self,
        query_embedding,
        top_k: int = 5
    ):

        if self.index.ntotal == 0:

            return []

        query_embedding = np.asarray(
            [query_embedding],
            dtype="float32"
        )

        if query_embedding.shape[1] != self.embedding_dimension:

            raise ValueError(
                f"Query embedding dimension mismatch. "
                f"Expected {self.embedding_dimension}, "
                f"received {query_embedding.shape[1]}."
            )

        # Do not request more results than exist.
        actual_top_k = min(
            top_k,
            self.index.ntotal
        )

        distances, indices = self.index.search(
            query_embedding,
            actual_top_k
        )

        results = []

        for idx, distance in zip(
            indices[0],
            distances[0]
        ):

            if idx < 0:
                continue

            if idx >= len(self.metadata):
                continue

            result = self.metadata[idx].copy()

            result["distance"] = float(
                distance
            )

            results.append(result)

        return results

    # ==================================================
    # Save Vector Database
    # ==================================================

    def save(
        self,
        index_path="vector_db/faiss.index",
        metadata_path="vector_db/metadata.pkl"
    ):

        index_directory = os.path.dirname(
            index_path
        )

        metadata_directory = os.path.dirname(
            metadata_path
        )

        if index_directory:

            os.makedirs(
                index_directory,
                exist_ok=True
            )

        if metadata_directory:

            os.makedirs(
                metadata_directory,
                exist_ok=True
            )

        faiss.write_index(
            self.index,
            index_path
        )

        with open(
            metadata_path,
            "wb"
        ) as file:

            pickle.dump(
                self.metadata,
                file
            )

        print(
            "Vector database saved successfully."
        )

        print(
            f"Saved {len(self.metadata)} metadata records."
        )

    # ==================================================
    # Load Vector Database
    # ==================================================

    def load(
        self,
        index_path="vector_db/faiss.index",
        metadata_path="vector_db/metadata.pkl"
    ):

        if not os.path.exists(index_path):

            raise FileNotFoundError(
                f"FAISS index not found: {index_path}"
            )

        if not os.path.exists(metadata_path):

            raise FileNotFoundError(
                f"Metadata file not found: {metadata_path}"
            )

        # ----------------------------------------------
        # Load FAISS
        # ----------------------------------------------

        self.index = faiss.read_index(
            index_path
        )

        # ----------------------------------------------
        # Load metadata
        # ----------------------------------------------

        with open(
            metadata_path,
            "rb"
        ) as file:

            self.metadata = pickle.load(
                file
            )

        # ----------------------------------------------
        # Validate consistency
        # ----------------------------------------------

        if self.index.ntotal != len(self.metadata):

            raise ValueError(
                "Vector database is inconsistent. "
                f"FAISS contains {self.index.ntotal} vectors "
                f"but metadata contains "
                f"{len(self.metadata)} records."
            )

        print(
            f"Loaded {len(self.metadata)} "
            f"chunks from vector database."
        )

    # ==================================================
    # Information
    # ==================================================

    def size(self) -> int:

        return self.index.ntotal