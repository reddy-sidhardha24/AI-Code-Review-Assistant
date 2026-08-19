# backend/rag/retriever.py

from typing import Dict, List, Optional, Set

from .vector_store import VectorStore
from .embedder import CodeEmbedder


class Retriever:
    """
    Advanced Retriever for the AI Code Review Assistant.

    Supports:

    • Intent Detection
    • Semantic Retrieval
    • Context Expansion
    • Duplicate Removal
    • Similarity Filtering
    • Project-wide Retrieval

    IMPORTANT:
    The Retriever can receive an existing VectorStore.

    This prevents the Retriever from accidentally loading
    an older project's vector database from disk.
    """

    # ============================================================
    # Retrieval Configuration
    # ============================================================

    MAX_DISTANCE = 2.0

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    DEFAULT_INDEX_PATH = "vector_db/faiss.index"

    DEFAULT_METADATA_PATH = "vector_db/metadata.pkl"

    # ============================================================
    # Constructor
    # ============================================================

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        vector_store: Optional[VectorStore] = None,
        index_path: str = DEFAULT_INDEX_PATH,
        metadata_path: str = DEFAULT_METADATA_PATH,
    ):
        """
        Initialize the Retriever.

        If vector_store is supplied:

            Use the supplied VectorStore.

        If vector_store is NOT supplied:

            Load the persisted vector database.

        This distinction is critical for project isolation.
        """

        print(
            "\nInitializing Retriever..."
        )

        # --------------------------------------------------------
        # Embedding model
        # --------------------------------------------------------

        print(
            "Loading embedding model..."
        )

        self.embedder = CodeEmbedder(
            model_name
        )

        # --------------------------------------------------------
        # Vector store
        # --------------------------------------------------------

        if vector_store is not None:

            # ====================================================
            # IMPORTANT
            # ====================================================
            # Use the VectorStore already created by RAGPipeline.
            #
            # DO NOT load vector_db/metadata.pkl again.
            # ====================================================

            print(
                "Using supplied VectorStore."
            )

            self.vector_store = vector_store

        else:

            # ----------------------------------------------------
            # Standalone / server restart mode
            # ----------------------------------------------------

            print(
                "No VectorStore supplied."
            )

            print(
                "Loading vector database from disk..."
            )

            self.vector_store = VectorStore()

            self.vector_store.load(
                index_path=index_path,
                metadata_path=metadata_path,
            )

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        print(
            f"Retriever Ready. "
            f"{self.vector_store.size()} chunks indexed."
        )

        print(
            f"Indexed Files: "
            f"{self.vector_store.file_count()}"
        )

    # ============================================================
    # Retrieval Statistics
    # ============================================================

    def get_retrieval_statistics(
        self
    ) -> Dict:

        indexed_files = set()

        for chunk in (
            self.vector_store.metadata
        ):

            file_path = (
                chunk.get("relative_path")
                or chunk.get("path")
                or chunk.get("file")
                or chunk.get("name")
                or ""
            )

            if file_path:

                indexed_files.add(
                    file_path
                )

        return {
            "total_indexed_files": len(
                indexed_files
            ),

            "total_chunks": len(
                self.vector_store.metadata
            ),
        }

    # ============================================================
    # Intent Detection
    # ============================================================

    def detect_query_type(
        self,
        query: str
    ) -> str:
        """
        Detect the primary intent of a review question.
        """

        q = query.lower().strip()

        # --------------------------------------------------------
        # Performance
        # --------------------------------------------------------

        performance_keywords = [
            "performance",
            "complexity",
            "slow",
            "optimize",
            "optimization",
            "memory",
            "space complexity",
            "time complexity",
            "efficiency",
            "inefficient",
        ]

        # --------------------------------------------------------
        # Security
        # --------------------------------------------------------

        security_keywords = [
            "security",
            "vulnerability",
            "sql injection",
            "xss",
            "csrf",
            "authentication",
            "authorization",
            "password",
            "api key",
            "secret",
            "credential",
            "command injection",
        ]

        # --------------------------------------------------------
        # Bugs
        # --------------------------------------------------------

        bug_keywords = [
            "bug",
            "bugs",
            "error",
            "errors",
            "issue",
            "issues",
            "exception",
            "runtime",
            "fix",
            "crash",
            "incorrect",
            "wrong",
            "failure",
        ]

        # --------------------------------------------------------
        # Explanation
        # --------------------------------------------------------

        explanation_keywords = [
            "explain",
            "what",
            "how",
            "purpose",
            "working",
            "flow",
            "algorithm",
            "describe",
        ]

        # --------------------------------------------------------
        # Architecture
        # --------------------------------------------------------

        architecture_keywords = [
            "architecture",
            "design",
            "structure",
            "project",
            "overview",
            "workflow",
            "modules",
            "components",
        ]

        # --------------------------------------------------------
        # Priority
        # --------------------------------------------------------

        if any(
            keyword in q
            for keyword in performance_keywords
        ):

            return "performance"

        if any(
            keyword in q
            for keyword in security_keywords
        ):

            return "security"

        if any(
            keyword in q
            for keyword in architecture_keywords
        ):

            return "architecture"

        if any(
            keyword in q
            for keyword in bug_keywords
        ):

            return "bug"

        if any(
            keyword in q
            for keyword in explanation_keywords
        ):

            return "explanation"

        return "general"

    # ============================================================
    # Similarity Filter
    # ============================================================

    def filter_by_similarity(
        self,
        chunks: List[Dict],
        threshold: float = MAX_DISTANCE,
    ) -> List[Dict]:
        """
        Remove chunks whose FAISS distance is too large.
        """

        filtered = []

        for chunk in chunks:

            distance = chunk.get(
                "distance",
                999.0
            )

            if distance <= threshold:

                filtered.append(
                    chunk
                )

        return filtered

    # ============================================================
    # Remove Duplicate Chunks
    # ============================================================

    def remove_duplicates(
        self,
        chunks: List[Dict]
    ) -> List[Dict]:
        """
        Remove duplicate chunks safely.
        """

        unique = []

        seen: Set[str] = set()

        for index, chunk in enumerate(
            chunks
        ):

            chunk_id = chunk.get(
                "chunk_id"
            )

            # ----------------------------------------------------
            # Some chunks may not have a chunk_id.
            # Create a fallback identifier.
            # ----------------------------------------------------

            if chunk_id is None:

                chunk_id = (
                    f"{chunk.get('relative_path', '')}"
                    f":{chunk.get('start_line', '')}"
                    f":{chunk.get('end_line', '')}"
                    f":{index}"
                )

            chunk_key = str(
                chunk_id
            )

            if chunk_key in seen:

                continue

            seen.add(
                chunk_key
            )

            unique.append(
                chunk
            )

        return unique

    # ============================================================
    # Find Adjacent Chunk
    # ============================================================

    def get_adjacent_chunk(
        self,
        current_chunk: Dict,
        offset: int,
    ) -> Optional[Dict]:
        """
        Find the previous or next chunk belonging to
        the same source file.
        """

        current_file = (
            current_chunk.get(
                "relative_path"
            )
            or current_chunk.get(
                "path"
            )
        )

        current_index = (
            current_chunk.get(
                "file_chunk_index"
            )
        )

        if current_file is None:

            return None

        if current_index is None:

            return None

        target_index = (
            current_index + offset
        )

        for chunk in (
            self.vector_store.metadata
        ):

            chunk_file = (
                chunk.get(
                    "relative_path"
                )
                or chunk.get(
                    "path"
                )
            )

            chunk_index = (
                chunk.get(
                    "file_chunk_index"
                )
            )

            if (
                chunk_file == current_file
                and
                chunk_index == target_index
            ):

                return chunk.copy()

        return None

    # ============================================================
    # Context Expansion
    # ============================================================

    def expand_context(
        self,
        retrieved_chunks: List[Dict]
    ) -> List[Dict]:
        """
        Add neighbouring chunks from the same file.
        """

        expanded = []

        for chunk in retrieved_chunks:

            previous_chunk = (
                self.get_adjacent_chunk(
                    chunk,
                    -1
                )
            )

            if previous_chunk:

                expanded.append(
                    previous_chunk
                )

            expanded.append(
                chunk
            )

            next_chunk = (
                self.get_adjacent_chunk(
                    chunk,
                    1
                )
            )

            if next_chunk:

                expanded.append(
                    next_chunk
                )

        expanded = (
            self.remove_duplicates(
                expanded
            )
        )

        expanded.sort(
            key=lambda item: (
                item.get(
                    "relative_path",
                    item.get(
                        "path",
                        ""
                    )
                ),
                item.get(
                    "start_line",
                    0
                ),
            )
        )

        return expanded

    # ============================================================
    # Semantic Retrieval
    # ============================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Advanced semantic retrieval.

        Pipeline:

            Query
              ↓
            Intent Detection
              ↓
            Embedding
              ↓
            FAISS Search
              ↓
            Similarity Filtering
              ↓
            Context Expansion
              ↓
            Duplicate Removal
              ↓
            Ranking
              ↓
            Final Results
        """

        if not query or not query.strip():

            raise ValueError(
                "Retrieval query cannot be empty."
            )

        total_chunks = (
            self.vector_store.size()
        )

        if total_chunks == 0:

            print(
                "Vector store is empty."
            )

            return []

        # --------------------------------------------------------
        # Query type
        # --------------------------------------------------------

        query_type = (
            self.detect_query_type(
                query
            )
        )

        print(
            f"\nQuery Type: {query_type}"
        )

        # --------------------------------------------------------
        # Query embedding
        # --------------------------------------------------------

        query_embedding = (
            self.embedder.model.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
        )

        # --------------------------------------------------------
        # Search more candidates than required
        # --------------------------------------------------------

        search_size = min(
            max(
                top_k * 3,
                10
            ),
            total_chunks
        )

        print(
            "Using semantic retrieval..."
        )

        retrieved = (
            self.vector_store.search(
                query_embedding,
                top_k=search_size
            )
        )

        # --------------------------------------------------------
        # Similarity filter
        # --------------------------------------------------------

        retrieved = (
            self.filter_by_similarity(
                retrieved
            )
        )

        if not retrieved:

            print(
                "No chunks passed similarity filter."
            )

            return []

        # --------------------------------------------------------
        # Context expansion
        # --------------------------------------------------------

        print(
            "Expanding neighbouring chunks..."
        )

        expanded = (
            self.expand_context(
                retrieved
            )
        )

        # --------------------------------------------------------
        # Remove duplicates
        # --------------------------------------------------------

        expanded = (
            self.remove_duplicates(
                expanded
            )
        )

        # --------------------------------------------------------
        # Ranking
        # --------------------------------------------------------

        if query_type in (
            "bug",
            "security",
            "performance",
        ):

            expanded.sort(
                key=lambda chunk: (
                    chunk.get(
                        "distance",
                        999
                    ),
                    chunk.get(
                        "start_line",
                        0
                    ),
                )
            )

        else:

            expanded.sort(
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
                    ),
                )
            )

        # --------------------------------------------------------
        # Final limit
        # --------------------------------------------------------

        final_chunks = expanded[
            :top_k
        ]

        print(
            f"\nRetrieved "
            f"{len(final_chunks)} chunks."
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
                f"File: "
                f"{chunk.get('name', 'Unknown')}"
            )

            print(
                f"Lines: "
                f"{chunk.get('start_line', '?')} - "
                f"{chunk.get('end_line', '?')}"
            )

            print(
                f"Distance: "
                f"{chunk.get('distance', 'Expanded')}"
            )

        return final_chunks

    # ============================================================
    # Project-Wide Retrieval
    # ============================================================

    def retrieve_project_wide(
        self,
        query: str = "",
        max_chunks: int = 20,
        chunks_per_file: int = 2,
    ) -> List[Dict]:
        """
        Retrieve representative chunks from EVERY indexed file.

        This is intentionally NOT semantic filtering.

        For a complete project review, every file should have
        an opportunity to reach the LLM.
        """

        total_chunks = (
            self.vector_store.size()
        )

        if total_chunks == 0:

            print(
                "Vector store is empty."
            )

            return []

        # --------------------------------------------------------
        # Group by file
        # --------------------------------------------------------

        chunks_by_file: Dict[
            str,
            List[Dict]
        ] = {}

        for chunk in (
            self.vector_store.metadata
        ):

            file_path = (
                chunk.get(
                    "relative_path"
                )
                or chunk.get(
                    "path"
                )
                or chunk.get(
                    "name"
                )
                or ""
            )

            if file_path not in (
                chunks_by_file
            ):

                chunks_by_file[
                    file_path
                ] = []

            chunks_by_file[
                file_path
            ].append(
                chunk
            )

        # --------------------------------------------------------
        # Sort chunks in each file
        # --------------------------------------------------------

        for file_path in (
            chunks_by_file
        ):

            chunks_by_file[
                file_path
            ].sort(
                key=lambda chunk: (
                    chunk.get(
                        "start_line",
                        0
                    ),
                    chunk.get(
                        "end_line",
                        0
                    ),
                )
            )

        # --------------------------------------------------------
        # Select chunks
        # --------------------------------------------------------

        selected_chunks = []

        sorted_files = sorted(
            chunks_by_file.keys()
        )

        for file_path in sorted_files:

            file_chunks = (
                chunks_by_file[
                    file_path
                ]
            )

            selected_chunks.extend(
                file_chunks[
                    :chunks_per_file
                ]
            )

            if len(
                selected_chunks
            ) >= max_chunks:

                break

        # --------------------------------------------------------
        # Remove duplicates
        # --------------------------------------------------------

        selected_chunks = (
            self.remove_duplicates(
                selected_chunks
            )
        )

        # --------------------------------------------------------
        # Final limit
        # --------------------------------------------------------

        final_chunks = (
            selected_chunks[
                :max_chunks
            ]
        )

        # --------------------------------------------------------
        # Sort final result
        # --------------------------------------------------------

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
                ),
            )
        )

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        represented_files = set()

        for chunk in final_chunks:

            file_path = (
                chunk.get(
                    "relative_path"
                )
                or chunk.get(
                    "path"
                )
                or chunk.get(
                    "name"
                )
                or ""
            )

            represented_files.add(
                file_path
            )

        print(
            f"\nProject-wide retrieval: "
            f"{len(final_chunks)} chunks."
        )

        print(
            "Files represented:",
            len(represented_files)
        )

        # --------------------------------------------------------
        # Debug output
        # --------------------------------------------------------

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
                "Language:",
                chunk.get(
                    "language",
                    "Unknown"
                )
            )

            print(
                "Lines:",
                f"{chunk.get('start_line', '?')} - "
                f"{chunk.get('end_line', '?')}"
            )

        return final_chunks