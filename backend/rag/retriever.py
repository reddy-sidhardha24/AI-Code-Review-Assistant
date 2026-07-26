# backend/rag/retriever.py

from collections import defaultdict
from typing import Dict, List, Optional

from .vector_store import VectorStore
from .embedder import CodeEmbedder


class Retriever:
    """
    Retrieves source-code chunks from the FAISS vector store.

    Supports:

    1. Semantic retrieval
       - Used for specific questions.
       - Example:
         "Explain the login function."

    2. Project-wide retrieval
       - Used when broader project coverage is required.
       - Attempts to include chunks from multiple files.

    3. File-specific retrieval
       - Used when analysis needs chunks belonging to
         a particular file.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: str = "vector_db/faiss.index",
        metadata_path: str = "vector_db/metadata.pkl"
    ):

        print("Loading embedding model...")

        self.embedder = CodeEmbedder(
            model_name
        )

        print("Loading vector database...")

        self.vector_store = VectorStore()

        self.vector_store.load(
            index_path,
            metadata_path
        )

        print(
            f"Retriever Ready. "
            f"{len(self.vector_store.metadata)} chunks available."
        )

    # =====================================================
    # Semantic Retrieval
    # =====================================================

    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve the most semantically relevant chunks.

        This should be used for targeted questions such as:

        - Explain login()
        - Find the bug in UserService
        - What does payment.py do?
        """

        if not query or not query.strip():

            raise ValueError(
                "Retrieval query cannot be empty."
            )

        if top_k <= 0:

            raise ValueError(
                "top_k must be greater than 0."
            )

        total_chunks = len(
            self.vector_store.metadata
        )

        if total_chunks == 0:

            return []

        # Do not request more results than FAISS contains.
        actual_top_k = min(
            top_k,
            total_chunks
        )

        query_embedding = (
            self.embedder.model.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
        )

        results = (
            self.vector_store.search(
                query_embedding,
                top_k=actual_top_k
            )
        )

        return results

    # =====================================================
    # Get All Stored Chunks
    # =====================================================

    def get_all_chunks(
        self
    ) -> List[Dict]:
        """
        Return all chunks stored in metadata.

        IMPORTANT:

        This method does NOT mean that all chunks should
        automatically be sent to the LLM.

        Large projects must later be analyzed in batches
        because sending everything at once can exceed the
        LLM token limit.
        """

        return [
            chunk.copy()
            for chunk
            in self.vector_store.metadata
        ]

    # =====================================================
    # Get Chunks for One File
    # =====================================================

    def get_file_chunks(
        self,
        file_path: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Return chunks belonging to a particular source file.

        A file can be selected using:

        - path
        - relative_path
        - file name
        """

        if not file_path and not file_name:

            raise ValueError(
                "Either file_path or file_name "
                "must be provided."
            )

        matches = []

        for chunk in self.vector_store.metadata:

            chunk_path = str(
                chunk.get(
                    "path",
                    ""
                )
            )

            chunk_relative_path = str(
                chunk.get(
                    "relative_path",
                    ""
                )
            )

            chunk_name = str(
                chunk.get(
                    "name",
                    ""
                )
            )

            path_match = False
            name_match = False

            if file_path:

                normalized_requested_path = (
                    file_path
                    .replace("\\", "/")
                    .lower()
                )

                normalized_chunk_path = (
                    chunk_path
                    .replace("\\", "/")
                    .lower()
                )

                normalized_relative_path = (
                    chunk_relative_path
                    .replace("\\", "/")
                    .lower()
                )

                path_match = (
                    normalized_chunk_path
                    == normalized_requested_path
                    or
                    normalized_relative_path
                    == normalized_requested_path
                )

            if file_name:

                name_match = (
                    chunk_name.lower()
                    ==
                    file_name.lower()
                )

            if path_match or name_match:

                matches.append(
                    chunk.copy()
                )

        # Keep chunks in source-code order.
        matches.sort(
            key=lambda item: (
                str(
                    item.get(
                        "path",
                        ""
                    )
                ),
                int(
                    item.get(
                        "start_line",
                        0
                    )
                )
            )
        )

        return matches

    # =====================================================
    # Group Chunks by File
    # =====================================================

    def group_chunks_by_file(
        self
    ) -> Dict[str, List[Dict]]:
        """
        Group every stored chunk by source file.

        Useful for project-wide analysis and future
        file-by-file batching.
        """

        grouped = defaultdict(list)

        for chunk in self.vector_store.metadata:

            key = (
                chunk.get("relative_path")
                or
                chunk.get("path")
                or
                chunk.get("name")
                or
                "Unknown"
            )

            grouped[key].append(
                chunk.copy()
            )

        # Sort chunks inside every file.
        for file_path in grouped:

            grouped[file_path].sort(
                key=lambda item: int(
                    item.get(
                        "start_line",
                        0
                    )
                )
            )

        return dict(grouped)

    # =====================================================
    # Broad Project Retrieval
    # =====================================================

    def retrieve_project_wide(
        self,
        query: str,
        max_chunks: int = 12,
        chunks_per_file: int = 2
    ) -> List[Dict]:
        """
        Retrieve broader project context.

        Unlike normal semantic retrieval, this method
        attempts to avoid returning many chunks from only
        one file.

        Strategy:

        1. Perform a larger semantic search.
        2. Group results by file.
        3. Limit how many chunks each file contributes.
        4. Return a diverse set of chunks.

        This improves project coverage while still
        controlling prompt size.

        NOTE:
        This is NOT yet a complete whole-project analysis.
        Large projects will require batching.
        """

        if not query or not query.strip():

            raise ValueError(
                "Retrieval query cannot be empty."
            )

        if max_chunks <= 0:

            raise ValueError(
                "max_chunks must be greater than 0."
            )

        if chunks_per_file <= 0:

            raise ValueError(
                "chunks_per_file must be greater than 0."
            )

        total_chunks = len(
            self.vector_store.metadata
        )

        if total_chunks == 0:

            return []

        # Search more broadly than the final number
        # of chunks we intend to return.
        search_size = min(
            total_chunks,
            max(
                max_chunks * 4,
                max_chunks
            )
        )

        semantic_results = (
            self.retrieve(
                query=query,
                top_k=search_size
            )
        )

        selected = []

        file_counts = defaultdict(int)

        # -------------------------------------------------
        # First pass:
        # Select semantically relevant chunks while
        # preventing one file from dominating retrieval.
        # -------------------------------------------------

        for chunk in semantic_results:

            file_key = (
                chunk.get("relative_path")
                or
                chunk.get("path")
                or
                chunk.get("name")
                or
                "Unknown"
            )

            if (
                file_counts[file_key]
                >= chunks_per_file
            ):
                continue

            selected.append(
                chunk
            )

            file_counts[file_key] += 1

            if len(selected) >= max_chunks:
                break

        # -------------------------------------------------
        # Second pass:
        # If diversity filtering produced fewer chunks
        # than requested, fill remaining slots using the
        # best unused semantic results.
        # -------------------------------------------------

        if len(selected) < max_chunks:

            selected_ids = {
                chunk.get("chunk_id")
                for chunk in selected
            }

            for chunk in semantic_results:

                chunk_id = chunk.get(
                    "chunk_id"
                )

                if chunk_id in selected_ids:
                    continue

                selected.append(
                    chunk
                )

                selected_ids.add(
                    chunk_id
                )

                if len(selected) >= max_chunks:
                    break

        return selected

    # =====================================================
    # Project Statistics
    # =====================================================

    def get_retrieval_statistics(
        self
    ) -> Dict:
        """
        Return basic information about the indexed project.

        Useful for debugging and future batching logic.
        """

        grouped = (
            self.group_chunks_by_file()
        )

        return {
            "total_chunks":
                len(
                    self.vector_store.metadata
                ),

            "total_indexed_files":
                len(grouped),

            "chunks_per_file": {
                file_path: len(chunks)
                for file_path, chunks
                in grouped.items()
            }
        }


# ============================================================
# Local Test
# ============================================================

if __name__ == "__main__":

    retriever = Retriever()

    stats = (
        retriever.get_retrieval_statistics()
    )

    print("\nVector Database Statistics\n")

    print(
        "Total Chunks:",
        stats["total_chunks"]
    )

    print(
        "Total Files:",
        stats["total_indexed_files"]
    )

    print("\nChunks Per File:")

    for file_path, count in (
        stats["chunks_per_file"].items()
    ):

        print(
            f"- {file_path}: {count}"
        )

    question = input(
        "\nAsk a question: "
    )

    print(
        "\nSemantic Retrieval\n"
    )

    results = retriever.retrieve(
        question,
        top_k=5
    )

    for i, chunk in enumerate(
        results,
        start=1
    ):

        print("=" * 80)

        print(
            f"Rank     : {i}"
        )

        print(
            f"File     : "
            f"{chunk.get('name', 'Unknown')}"
        )

        print(
            f"Path     : "
            f"{chunk.get('path', 'Unknown')}"
        )

        print(
            f"Lines    : "
            f"{chunk.get('start_line', '?')} - "
            f"{chunk.get('end_line', '?')}"
        )

        print(
            f"Distance : "
            f"{chunk.get('distance', 0):.4f}"
        )

        print("\nCode Preview\n")

        print(
            chunk.get(
                "content",
                ""
            )[:500]
        )

        print()

    print(
        "\nProject-Wide Retrieval\n"
    )

    broad_results = (
        retriever.retrieve_project_wide(
            query=question,
            max_chunks=10,
            chunks_per_file=2
        )
    )

    for i, chunk in enumerate(
        broad_results,
        start=1
    ):

        print("=" * 80)

        print(
            f"Rank     : {i}"
        )

        print(
            f"File     : "
            f"{chunk.get('name', 'Unknown')}"
        )

        print(
            f"Lines    : "
            f"{chunk.get('start_line', '?')} - "
            f"{chunk.get('end_line', '?')}"
        )

        print()