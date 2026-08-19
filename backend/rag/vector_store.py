# backend/rag/vector_store.py

import os
import pickle
from typing import Dict, List

import faiss
import numpy as np


class VectorStore:
    """
    FAISS-based vector store for the AI Code Review Assistant.

    Important behavior:
    --------------------
    Every new project REPLACES the previous in-memory index.

    It does NOT append chunks from different projects.

    The store maintains:

        FAISS index
            ↓
        metadata records

    Each vector has exactly one corresponding metadata record.
    """

    def __init__(
        self,
        embedding_dimension: int = 384
    ):
        self.embedding_dimension = (
            embedding_dimension
        )

        self.index = faiss.IndexFlatL2(
            self.embedding_dimension
        )

        self.metadata: List[Dict] = []

    # ============================================================
    # RESET
    # ============================================================

    def reset(self):
        """
        Completely clear the current vector store.

        This removes all in-memory vectors and metadata.

        A new project should call this behavior through
        add_chunks(), which automatically replaces the
        existing index.
        """

        self.index = faiss.IndexFlatL2(
            self.embedding_dimension
        )

        self.metadata = []

        print(
            "Vector store reset successfully."
        )

    # ============================================================
    # ADD CHUNKS
    # ============================================================

    def add_chunks(
        self,
        embedded_chunks: List[Dict]
    ):
        """
        Replace the current vector database with a new project.

        IMPORTANT:
        This is intentionally a REPLACE operation, not APPEND.

        Therefore:

            Project A
                ↓
            add_chunks()
                ↓
            Project A indexed

            Project B
                ↓
            add_chunks()
                ↓
            Project A removed
            Project B indexed
        """

        if not embedded_chunks:

            raise ValueError(
                "No embedded chunks were provided."
            )

        # ========================================================
        # COMPLETE RESET
        # ========================================================

        self.reset()

        vectors = []

        new_metadata = []

        # ========================================================
        # PROCESS CHUNKS
        # ========================================================

        for chunk in embedded_chunks:

            embedding = chunk.get(
                "embedding"
            )

            # ----------------------------------------------------
            # Missing embedding
            # ----------------------------------------------------

            if embedding is None:

                print(
                    f"Skipping chunk "
                    f"{chunk.get('chunk_id', 'Unknown')} "
                    f"because embedding is missing."
                )

                continue

            vectors.append(
                embedding
            )

            # ----------------------------------------------------
            # Metadata
            # ----------------------------------------------------

            metadata = {

                # ================================================
                # Chunk Information
                # ================================================

                "chunk_id": chunk.get(
                    "chunk_id"
                ),

                "file_chunk_index": chunk.get(
                    "file_chunk_index",
                    0
                ),

                # ================================================
                # File Information
                # ================================================

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

                # ================================================
                # Source Location
                # ================================================

                "start_line": chunk.get(
                    "start_line"
                ),

                "end_line": chunk.get(
                    "end_line"
                ),

                # ================================================
                # Code
                # ================================================

                "content": chunk.get(
                    "content",
                    ""
                ),

                "numbered_content": chunk.get(
                    "numbered_content",
                    ""
                ),
            }

            new_metadata.append(
                metadata
            )

        # ========================================================
        # VALIDATE EMBEDDINGS
        # ========================================================

        if not vectors:

            self.reset()

            raise ValueError(
                "No valid embeddings were available "
                "to create the FAISS index."
            )

        vectors = np.asarray(
            vectors,
            dtype="float32"
        )

        # ========================================================
        # DIMENSION VALIDATION
        # ========================================================

        if vectors.ndim != 2:

            self.reset()

            raise ValueError(
                "Embeddings must be a "
                "2-dimensional array."
            )

        if (
            vectors.shape[1]
            != self.embedding_dimension
        ):

            self.reset()

            raise ValueError(
                f"Embedding dimension mismatch. "
                f"Expected "
                f"{self.embedding_dimension}, "
                f"received "
                f"{vectors.shape[1]}."
            )

        # ========================================================
        # BUILD NEW FAISS INDEX
        # ========================================================

        self.index = faiss.IndexFlatL2(
            self.embedding_dimension
        )

        self.index.add(
            vectors
        )

        # ========================================================
        # REPLACE METADATA
        # ========================================================

        self.metadata = new_metadata

        # ========================================================
        # CONSISTENCY CHECK
        # ========================================================

        if (
            self.index.ntotal
            != len(self.metadata)
        ):

            self.reset()

            raise ValueError(
                "Vector database became inconsistent. "
                f"FAISS contains "
                f"{self.index.ntotal} vectors "
                f"but metadata contains "
                f"{len(self.metadata)} records."
            )

        # ========================================================
        # STATISTICS
        # ========================================================

        unique_files = set()

        for item in self.metadata:

            path = item.get(
                "path"
            )

            if path:

                unique_files.add(
                    path
                )

        print()
        print(
            "=========================================="
        )
        print(
            "VECTOR STORE UPDATED"
        )
        print(
            "=========================================="
        )

        print(
            f"Indexed Chunks : "
            f"{self.index.ntotal}"
        )

        print(
            f"Indexed Files  : "
            f"{len(unique_files)}"
        )

        print(
            "Previous project data replaced."
        )

        print(
            "=========================================="
        )
        print()

    # ============================================================
    # SEARCH
    # ============================================================

    def search(
        self,
        query_embedding,
        top_k: int = 5
    ):
        """
        Search the current project's FAISS index.

        Results are returned together with their metadata
        and similarity distance.
        """

        # ========================================================
        # EMPTY STORE
        # ========================================================

        if self.index.ntotal == 0:

            return []

        # ========================================================
        # QUERY VECTOR
        # ========================================================

        query_embedding = np.asarray(
            [query_embedding],
            dtype="float32"
        )

        # ========================================================
        # DIMENSION CHECK
        # ========================================================

        if query_embedding.ndim != 2:

            raise ValueError(
                "Query embedding must be "
                "a 2-dimensional array."
            )

        if (
            query_embedding.shape[1]
            != self.embedding_dimension
        ):

            raise ValueError(
                f"Query embedding dimension mismatch. "
                f"Expected "
                f"{self.embedding_dimension}, "
                f"received "
                f"{query_embedding.shape[1]}."
            )

        # ========================================================
        # TOP K
        # ========================================================

        actual_top_k = min(
            top_k,
            self.index.ntotal
        )

        # ========================================================
        # FAISS SEARCH
        # ========================================================

        distances, indices = (
            self.index.search(
                query_embedding,
                actual_top_k
            )
        )

        results = []

        # ========================================================
        # BUILD RESULTS
        # ========================================================

        for idx, distance in zip(
            indices[0],
            distances[0]
        ):

            # ----------------------------------------------------
            # Invalid FAISS index
            # ----------------------------------------------------

            if idx < 0:

                continue

            # ----------------------------------------------------
            # Metadata safety check
            # ----------------------------------------------------

            if idx >= len(
                self.metadata
            ):

                continue

            result = (
                self.metadata[idx].copy()
            )

            result["distance"] = float(
                distance
            )

            results.append(
                result
            )

        return results

    # ============================================================
    # SAVE
    # ============================================================

    def save(
        self,
        index_path="vector_db/faiss.index",
        metadata_path="vector_db/metadata.pkl"
    ):
        """
        Persist the current FAISS index and metadata.

        The files are completely overwritten.
        """

        # ========================================================
        # VALIDATE STATE
        # ========================================================

        if (
            self.index.ntotal
            != len(self.metadata)
        ):

            raise ValueError(
                "Cannot save inconsistent vector database. "
                f"FAISS contains "
                f"{self.index.ntotal} vectors "
                f"but metadata contains "
                f"{len(self.metadata)} records."
            )

        # ========================================================
        # DIRECTORIES
        # ========================================================

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

        # ========================================================
        # SAVE FAISS
        # ========================================================

        faiss.write_index(
            self.index,
            index_path
        )

        # ========================================================
        # SAVE METADATA
        # ========================================================

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
            f"Saved chunks: "
            f"{len(self.metadata)}"
        )

    # ============================================================
    # LOAD
    # ============================================================

    def load(
        self,
        index_path="vector_db/faiss.index",
        metadata_path="vector_db/metadata.pkl"
    ):
        """
        Load a previously saved FAISS index and metadata.

        This should only be used when intentionally restoring
        the current project's persisted vector database.
        """

        # ========================================================
        # FILE CHECK
        # ========================================================

        if not os.path.exists(
            index_path
        ):

            raise FileNotFoundError(
                f"FAISS index not found: "
                f"{index_path}"
            )

        if not os.path.exists(
            metadata_path
        ):

            raise FileNotFoundError(
                f"Metadata file not found: "
                f"{metadata_path}"
            )

        # ========================================================
        # LOAD FAISS
        # ========================================================

        loaded_index = faiss.read_index(
            index_path
        )

        # ========================================================
        # LOAD METADATA
        # ========================================================

        with open(
            metadata_path,
            "rb"
        ) as file:

            loaded_metadata = pickle.load(
                file
            )

        # ========================================================
        # VALIDATE INDEX DIMENSION
        # ========================================================

        if (
            loaded_index.d
            != self.embedding_dimension
        ):

            raise ValueError(
                f"Loaded FAISS index dimension mismatch. "
                f"Expected "
                f"{self.embedding_dimension}, "
                f"received "
                f"{loaded_index.d}."
            )

        # ========================================================
        # VALIDATE METADATA
        # ========================================================

        if not isinstance(
            loaded_metadata,
            list
        ):

            raise ValueError(
                "Loaded metadata must be a list."
            )

        # ========================================================
        # CONSISTENCY CHECK
        # ========================================================

        if (
            loaded_index.ntotal
            != len(loaded_metadata)
        ):

            raise ValueError(
                "Vector database is inconsistent. "
                f"FAISS contains "
                f"{loaded_index.ntotal} vectors "
                f"but metadata contains "
                f"{len(loaded_metadata)} records."
            )

        # ========================================================
        # REPLACE CURRENT STATE
        # ========================================================

        self.index = loaded_index

        self.metadata = (
            loaded_metadata
        )

        # ========================================================
        # STATISTICS
        # ========================================================

        unique_files = set()

        for item in self.metadata:

            if isinstance(
                item,
                dict
            ):

                path = item.get(
                    "path"
                )

                if path:

                    unique_files.add(
                        path
                    )

        print()
        print(
            "=========================================="
        )
        print(
            "VECTOR DATABASE LOADED"
        )
        print(
            "=========================================="
        )

        print(
            f"Loaded Chunks : "
            f"{self.index.ntotal}"
        )

        print(
            f"Loaded Files  : "
            f"{len(unique_files)}"
        )

        print(
            "=========================================="
        )
        print()

    # ============================================================
    # SIZE
    # ============================================================

    def size(self) -> int:
        """
        Return the number of indexed chunks.
        """

        return self.index.ntotal

    # ============================================================
    # FILE COUNT
    # ============================================================

    def file_count(self) -> int:
        """
        Return the number of unique files currently indexed.
        """

        files = set()

        for item in self.metadata:

            if not isinstance(
                item,
                dict
            ):

                continue

            path = item.get(
                "path"
            )

            if path:

                files.add(
                    path
                )

        return len(files)

    # ============================================================
    # CURRENT FILES
    # ============================================================

    def get_indexed_files(self) -> List[str]:
        """
        Return unique paths of files currently indexed.
        """

        files = set()

        for item in self.metadata:

            if not isinstance(
                item,
                dict
            ):

                continue

            path = item.get(
                "path"
            )

            if path:

                files.add(
                    path
                )

        return sorted(
            files
        )

    # ============================================================
    # METADATA
    # ============================================================

    def get_metadata(self) -> List[Dict]:
        """
        Return a copy of the current metadata.
        """

        return [
            item.copy()
            for item in self.metadata
        ]