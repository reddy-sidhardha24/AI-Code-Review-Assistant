from collections import defaultdict
from typing import Dict, List, Optional, Set

from .vector_store import VectorStore
from .embedder import CodeEmbedder



class Retriever:
    """
    Advanced Retriever

    Supports:

    • Intent Detection
    • Semantic Retrieval
    • Context Expansion
    • Duplicate Removal
    • Similarity Filtering
    • Project-wide Retrieval
    """

    # ---------------------------------------------
    # Retrieval thresholds
    # ---------------------------------------------

    MAX_DISTANCE = 2.0

    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
        index_path="vector_db/faiss.index",
        metadata_path="vector_db/metadata.pkl",
    ):

        print("Loading embedding model...")

        self.embedder = CodeEmbedder(model_name)

        print("Loading vector database...")

        self.vector_store = VectorStore()

        self.vector_store.load(
            index_path=index_path,
            metadata_path=metadata_path,
        )

        print(
            f"Retriever Ready. "
            f"{len(self.vector_store.metadata)} chunks indexed."
        )
        # =====================================================
    # Retrieval Statistics
    # =====================================================

    def get_retrieval_statistics(self):

        indexed_files = set()

        for chunk in self.vector_store.metadata:

            file_path = (
                chunk.get("relative_path")
                or chunk.get("path")
                or chunk.get("file")
                or ""
            )

            if file_path:
                indexed_files.add(file_path)

        return {
            "total_indexed_files": len(indexed_files),
            "total_chunks": len(
                self.vector_store.metadata
            )
        }
    # =====================================================
    # Intent Detection
    # =====================================================

    def detect_query_type(
        self,
        query: str
    ) -> str:

        q = query.lower()

        performance_keywords = [
            "performance",
            "complexity",
            "slow",
            "optimize",
            "optimization",
            "memory",
            "space complexity",
            "time complexity",
        ]

        security_keywords = [
            "security",
            "vulnerability",
            "sql injection",
            "xss",
            "csrf",
            "authentication",
            "authorization",
        ]

        bug_keywords = [
            "bug",
            "error",
            "issue",
            "exception",
            "runtime",
            "fix",
            "crash",
        ]

        explanation_keywords = [
            "explain",
            "what",
            "how",
            "purpose",
            "working",
            "flow",
            "algorithm",
        ]

        architecture_keywords = [
            "architecture",
            "design",
            "structure",
            "project",
            "overview",
            "workflow",
        ]

        if any(k in q for k in performance_keywords):
            return "performance"

        if any(k in q for k in security_keywords):
            return "security"

        if any(k in q for k in architecture_keywords):
            return "architecture"

        if any(k in q for k in bug_keywords):
            return "bug"

        if any(k in q for k in explanation_keywords):
            return "explanation"

        return "general"

    # =====================================================
    # Similarity Filter
    # =====================================================

    def filter_by_similarity(
        self,
        chunks: List[Dict],
        threshold: float = MAX_DISTANCE,
    ) -> List[Dict]:

        filtered = []

        for chunk in chunks:

            distance = chunk.get(
                "distance",
                999.0,
            )

            if distance <= threshold:

                filtered.append(chunk)

        return filtered

    # =====================================================
    # Remove Duplicate Chunks
    # =====================================================

    def remove_duplicates(
        self,
        chunks: List[Dict]
    ) -> List[Dict]:

        unique = []

        seen: Set[int] = set()

        for chunk in chunks:

            chunk_id = chunk.get(
                "chunk_id"
            )

            if chunk_id in seen:
                continue

            seen.add(chunk_id)

            unique.append(chunk)

        return unique

    # =====================================================
    # Find Adjacent Chunk
    # =====================================================

    def get_adjacent_chunk(
        self,
        current_chunk: Dict,
        offset: int,
    ) -> Optional[Dict]:

        current_file = current_chunk.get(
            "relative_path"
        )

        current_index = current_chunk.get(
            "file_chunk_index"
        )

        if current_index is None:
            return None

        target_index = current_index + offset

        for chunk in self.vector_store.metadata:

            if (
                chunk.get("relative_path")
                == current_file
                and
                chunk.get("file_chunk_index")
                == target_index
            ):
                return chunk.copy()

        return None

    # =====================================================
    # Context Expansion
    # =====================================================

    def expand_context(
        self,
        retrieved_chunks: List[Dict]
    ) -> List[Dict]:

        expanded = []

        for chunk in retrieved_chunks:

            previous_chunk = self.get_adjacent_chunk(
                chunk,
                -1,
            )

            if previous_chunk:
                expanded.append(
                    previous_chunk
                )

            expanded.append(chunk)

            next_chunk = self.get_adjacent_chunk(
                chunk,
                1,
            )

            if next_chunk:
                expanded.append(
                    next_chunk
                )

        expanded = self.remove_duplicates(
            expanded
        )

        expanded.sort(
            key=lambda c: (
                c.get(
                    "relative_path",
                    ""
                ),
                c.get(
                    "start_line",
                    0,
                ),
            )
        )

        return expanded

    # =====================================================
    # Advanced Retrieval
    # =====================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Advanced Retrieval Pipeline

        1. Detect query intent
        2. Semantic search
        3. Similarity filtering
        4. Context expansion
        5. Remove duplicates
        6. Ranking
        """

        if not query.strip():

            raise ValueError(
                "Retrieval query cannot be empty."
            )

        total_chunks = len(
            self.vector_store.metadata
        )

        if total_chunks == 0:
            return []

        # -------------------------------------------------
        # Detect Query Type
        # -------------------------------------------------

        query_type = self.detect_query_type(
            query
        )

        print(
            f"\nQuery Type: {query_type}"
        )

        # -------------------------------------------------
        # Encode Query
        # -------------------------------------------------

        query_embedding = (
            self.embedder.model.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        )

        # -------------------------------------------------
        # Broad search before filtering
        # -------------------------------------------------

        search_size = min(
            max(
                top_k * 3,
                10
            ),
            total_chunks,
        )

        print(
            "Using semantic retrieval..."
        )

        retrieved = (
            self.vector_store.search(
                query_embedding,
                top_k=search_size,
            )
        )

        # -------------------------------------------------
        # Similarity Filtering
        # -------------------------------------------------

        retrieved = self.filter_by_similarity(
            retrieved
        )

        if not retrieved:

            print(
                "No chunks passed similarity filter."
            )

            return []

        # -------------------------------------------------
        # Context Expansion
        # -------------------------------------------------

        print(
            "Expanding neighbouring chunks..."
        )

        expanded = self.expand_context(
            retrieved
        )

        # -------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------

        expanded = self.remove_duplicates(
            expanded
        )

        # -------------------------------------------------
        # Ranking
        # -------------------------------------------------

        if query_type in [
            "bug",
            "security",
            "performance",
        ]:

            expanded.sort(
                key=lambda chunk: (
                    chunk.get(
                        "distance",
                        999
                    ),
                    chunk.get(
                        "start_line",
                        0
                    )
                )
            )

        else:

            expanded.sort(
                key=lambda chunk: (
                    chunk.get(
                        "relative_path",
                        ""
                    ),
                    chunk.get(
                        "start_line",
                        0
                    )
                )
            )

        # -------------------------------------------------
        # Final Limit
        # -------------------------------------------------

        final_chunks = expanded[:top_k]

        print(
            f"\nRetrieved {len(final_chunks)} chunks."
        )

        for i, chunk in enumerate(
            final_chunks,
            start=1
        ):

            print()

            print(
                f"Retrieved Chunk {i}"
            )

            print(
                f"File: {chunk.get('name')}"
            )

            print(
                f"Lines: "
                f"{chunk.get('start_line')} - "
                f"{chunk.get('end_line')}"
            )

            print(
                f"Distance: "
                f"{chunk.get('distance', 'Expanded')}"
            )

        return final_chunks
       
    # =====================================================
    # Project-Wide Retrieval
    # =====================================================

    def retrieve_project_wide(
        self,
        query: str = "",
        max_chunks: int = 20,
        chunks_per_file: int = 2,
    ) -> List[Dict]:
        """
        Project-wide retrieval.

        Retrieves representative chunks from across
        the indexed project.

        Parameters
        ----------
        query:
            Review question. Accepted for compatibility
            with the RAG pipeline.

        max_chunks:
            Maximum total chunks to return.

        chunks_per_file:
            Maximum number of chunks selected from
            each file.
        """

        total_chunks = len(
            self.vector_store.metadata
        )

        if total_chunks == 0:
            return []

        # -------------------------------------------------
        # Group chunks by file
        # -------------------------------------------------

        chunks_by_file = {}

        for chunk in self.vector_store.metadata:

            file_path = chunk.get(
                "relative_path",
                chunk.get(
                    "path",
                    chunk.get(
                        "name",
                        ""
                    )
                )
            )

            if file_path not in chunks_by_file:

                chunks_by_file[file_path] = []

            chunks_by_file[file_path].append(
                chunk
            )

        # -------------------------------------------------
        # Sort chunks inside each file
        # -------------------------------------------------

        for file_path in chunks_by_file:

            chunks_by_file[file_path].sort(
                key=lambda chunk: (
                    chunk.get(
                        "start_line",
                        0
                    ),
                    chunk.get(
                        "end_line",
                        0
                    )
                )
            )

        # -------------------------------------------------
        # Select chunks from every file
        # -------------------------------------------------

        selected_chunks = []

        for file_path in sorted(
            chunks_by_file.keys()
        ):

            file_chunks = chunks_by_file[
                file_path
            ]

            selected_chunks.extend(
                file_chunks[
                    :chunks_per_file
                ]
            )

            if len(selected_chunks) >= max_chunks:

                break

        # -------------------------------------------------
        # Remove duplicates
        # -------------------------------------------------

        selected_chunks = (
            self.remove_duplicates(
                selected_chunks
            )
        )

        # -------------------------------------------------
        # Final limit
        # -------------------------------------------------

        final_chunks = selected_chunks[
            :max_chunks
        ]

        # -------------------------------------------------
        # Sort final chunks
        # -------------------------------------------------

        final_chunks.sort(
            key=lambda chunk: (
                chunk.get(
                    "relative_path",
                    chunk.get(
                        "path",
                        ""
                    )
                ),
                chunk.get(
                    "start_line",
                    0
                )
            )
        )

        # -------------------------------------------------
        # Debug information
        # -------------------------------------------------

        print(
            f"\nProject-wide retrieval: "
            f"{len(final_chunks)} chunks."
        )

        # Calculate represented files separately.
        # This avoids complicated nested f-strings.

        represented_files = set()

        for chunk in final_chunks:

            file_path = chunk.get(
                "relative_path",
                chunk.get(
                    "path",
                    chunk.get(
                        "name",
                        ""
                    )
                )
            )

            represented_files.add(
                file_path
            )

        print(
            "Files represented:",
            len(represented_files)
        )

        # -------------------------------------------------
        # Print retrieved chunks
        # -------------------------------------------------

        for i, chunk in enumerate(
            final_chunks,
            start=1
        ):

            print()

            print(
                f"Project Chunk {i}"
            )

            print(
                "File:",
                chunk.get(
                    "name",
                    "Unknown"
                )
            )

            print(
                "Path:",
                chunk.get(
                    "path",
                    chunk.get(
                        "relative_path",
                        "Unknown"
                    )
                )
            )

            print(
                "Lines:",
                f"{chunk.get('start_line', '?')} - "
                f"{chunk.get('end_line', '?')}"
            )

        return final_chunks