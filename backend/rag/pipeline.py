# backend/rag/pipeline.py

import os
import json
from typing import Dict, List

from .loader import ProjectLoader
from .chunker import CodeChunker
from .embedder import CodeEmbedder
from .vector_store import VectorStore
from .retriever import Retriever
from .prompt_builder import PromptBuilder


class RAGPipeline:
    """
    RAG Pipeline

    Project
        ↓
    Loader
        ↓
    Metadata
        ↓
    Chunker
        ↓
    Embedder
        ↓
    FAISS Vector Store
        ↓
    Query Classification
        ↓
    ┌────────────────┬─────────────────┐
    │ Targeted       │ Project-wide    │
    │ Retrieval      │ Retrieval       │
    └────────────────┴─────────────────┘
        ↓
    Prompt Builder
    """

    # ==================================================
    # Broad-query phrases
    # ==================================================

    PROJECT_WIDE_PHRASES = (
        "complete analysis",
        "complete review",
        "full analysis",
        "full review",
        "entire project",
        "whole project",
        "complete project",
        "entire codebase",
        "whole codebase",
        "all files",
        "every file",
        "all bugs",
        "all errors",
        "find all bugs",
        "find all errors",
        "analyze project",
        "analyse project",
        "analyze the project",
        "analyse the project",
        "review project",
        "review the project",
        "analyze everything",
        "analyse everything",
        "review everything",
    )

    def __init__(self):

        print("\nInitializing RAG Pipeline...\n")

        self.loader = None

        self.chunker = CodeChunker()

        self.embedder = CodeEmbedder()

        self.vector_store = VectorStore()

        self.prompt_builder = PromptBuilder()

        self.project_metadata = None

        self.retriever = None

        # ----------------------------------------------
        # Load existing database if available
        # ----------------------------------------------

        if self.vector_database_exists():

            print(
                "Existing vector database found."
            )

            try:

                self.retriever = Retriever()

                print(
                    "Retriever loaded successfully."
                )

            except Exception as e:

                print(
                    "Could not initialize retriever:",
                    str(e)
                )

        # ----------------------------------------------
        # Load existing metadata
        # ----------------------------------------------

        self.load_project_metadata()

        print("\nRAG Pipeline Ready.\n")

    # ==================================================
    # Build Vector Database
    # ==================================================

    def build_vector_database(
        self,
        project_path: str
    ):

        print("\nLoading project...")

        # ----------------------------------------------
        # Load source files
        # ----------------------------------------------

        self.loader = ProjectLoader(
            project_path
        )

        documents = self.loader.load()

        if not documents:

            raise ValueError(
                "No supported source-code files "
                "were found inside the uploaded project."
            )

        print(
            f"Loaded {len(documents)} files."
        )

        # ----------------------------------------------
        # Project metadata
        # ----------------------------------------------

        self.project_metadata = (
            self.loader.get_metadata()
        )

        print("\nProject Metadata:")

        print(
            "Project Name :",
            self.project_metadata.get(
                "project_name",
                "Unknown"
            )
        )

        print(
            "Total Files  :",
            self.project_metadata.get(
                "total_files",
                0
            )
        )

        print(
            "Total Lines  :",
            self.project_metadata.get(
                "total_lines",
                0
            )
        )

        print(
            "Languages    :",
            list(
                self.project_metadata.get(
                    "languages",
                    {}
                ).keys()
            )
        )

        self.save_project_metadata()

        # ----------------------------------------------
        # Chunk project
        # ----------------------------------------------

        print("\nChunking...")

        chunks = (
            self.chunker.chunk_documents(
                documents
            )
        )

        if not chunks:

            raise ValueError(
                "No source-code chunks were generated."
            )

        print(
            f"Generated {len(chunks)} chunks."
        )

        # ----------------------------------------------
        # Generate embeddings
        # ----------------------------------------------

        print(
            "\nGenerating embeddings..."
        )

        embedded_chunks = (
            self.embedder.embed_chunks(
                chunks
            )
        )

        if not embedded_chunks:

            raise ValueError(
                "No embeddings were generated."
            )

        # ----------------------------------------------
        # Fresh vector store
        # ----------------------------------------------

        print(
            "\nCreating new FAISS index..."
        )

        self.vector_store = VectorStore()

        self.vector_store.add_chunks(
            embedded_chunks
        )

        self.vector_store.save()

        print(
            "\nVector database created successfully."
        )

        # ----------------------------------------------
        # Reload retriever
        # ----------------------------------------------

        print(
            "\nReloading retriever..."
        )

        self.retriever = Retriever()

        print(
            "Retriever updated successfully."
        )

        # ----------------------------------------------
        # Retrieval statistics
        # ----------------------------------------------

        statistics = (
            self.retriever
            .get_retrieval_statistics()
        )

        print("\nRetrieval Statistics:")

        print(
            "Indexed Files :",
            statistics[
                "total_indexed_files"
            ]
        )

        print(
            "Total Chunks  :",
            statistics[
                "total_chunks"
            ]
        )

        return self.project_metadata

    # ==================================================
    # Query Classification
    # ==================================================

    def classify_query(
        self,
        query: str
    ) -> str:
        """
        Decide whether the user is asking about:

        TARGETED
        --------
        A particular function, class, file, bug,
        feature, or behavior.

        PROJECT_WIDE
        ------------
        The complete project/codebase or all
        bugs/errors/files.

        Returns:

        "targeted"
        or
        "project_wide"
        """

        normalized_query = (
            query
            .strip()
            .lower()
        )

        # ----------------------------------------------
        # Explicit broad phrases
        # ----------------------------------------------

        for phrase in (
            self.PROJECT_WIDE_PHRASES
        ):

            if phrase in normalized_query:

                return "project_wide"

        # ----------------------------------------------
        # Multiple broad review categories
        # ----------------------------------------------

        broad_categories = (
            "bugs",
            "errors",
            "security",
            "performance",
            "quality",
            "architecture",
            "methods",
            "classes",
            "libraries",
            "output",
            "improvements",
        )

        category_count = sum(
            1
            for category
            in broad_categories
            if category
            in normalized_query
        )

        # Example:
        #
        # "Give bugs, errors, performance,
        # security and improvements"
        #
        # This strongly suggests broad analysis.

        if category_count >= 4:

            return "project_wide"

        return "targeted"

    # ==================================================
    # Retrieve Context
    # ==================================================

    def retrieve_context(
        self,
        query: str,
        targeted_top_k: int = 3,
        project_max_chunks: int = 8,
        chunks_per_file: int = 2
    ) -> Dict:
        """
        Select retrieval strategy automatically.
        """

        if self.retriever is None:

            self.retriever = Retriever()

        query_type = (
            self.classify_query(
                query
            )
        )

        print(
            f"\nQuery Type: {query_type}"
        )

        # ----------------------------------------------
        # Project-wide retrieval
        # ----------------------------------------------

        if query_type == "project_wide":

            print(
                "Using broad project retrieval..."
            )

            chunks = (
                self.retriever
                .retrieve_project_wide(
                    query=query,
                    max_chunks=project_max_chunks,
                    chunks_per_file=chunks_per_file
                )
            )

        # ----------------------------------------------
        # Targeted semantic retrieval
        # ----------------------------------------------

        else:

            print(
                "Using targeted semantic retrieval..."
            )

            chunks = (
                self.retriever.retrieve(
                    query=query,
                    top_k=targeted_top_k
                )
            )

        return {
            "query_type": query_type,
            "chunks": chunks
        }

    # ==================================================
    # Generate Prompt
    # ==================================================

    def generate_prompt(
        self,
        query: str,
        targeted_top_k: int = 3,
        project_max_chunks: int = 8,
        chunks_per_file: int = 2
    ):

        # ----------------------------------------------
        # Validate query
        # ----------------------------------------------

        if not query or not query.strip():

            raise ValueError(
                "Question cannot be empty."
            )

        query = query.strip()

        # ----------------------------------------------
        # Check database
        # ----------------------------------------------

        if not self.vector_database_exists():

            raise ValueError(
                "No vector database found. "
                "Please upload a project first."
            )

        # ----------------------------------------------
        # Initialize retriever
        # ----------------------------------------------

        if self.retriever is None:

            print(
                "\nInitializing retriever..."
            )

            self.retriever = Retriever()

        # ----------------------------------------------
        # Retrieve context
        # ----------------------------------------------

        print(
            "\nRetrieving relevant code..."
        )

        retrieval = (
            self.retrieve_context(
                query=query,
                targeted_top_k=targeted_top_k,
                project_max_chunks=project_max_chunks,
                chunks_per_file=chunks_per_file
            )
        )

        query_type = (
            retrieval["query_type"]
        )

        retrieved_chunks = (
            retrieval["chunks"]
        )

        print(
            f"\nRetrieved "
            f"{len(retrieved_chunks)} chunks."
        )

        # ----------------------------------------------
        # Debug retrieved chunks
        # ----------------------------------------------

        self.print_retrieved_chunks(
            retrieved_chunks
        )

        # ----------------------------------------------
        # Load project metadata
        # ----------------------------------------------

        if self.project_metadata is None:

            self.load_project_metadata()

        # ----------------------------------------------
        # Build prompt
        # ----------------------------------------------

        prompt = (
            self.prompt_builder.build_prompt(
                query=query,
                retrieved_chunks=retrieved_chunks,
                project_metadata=self.project_metadata
            )
        )

        print(
            f"\nPrompt generated using "
            f"{query_type} retrieval."
        )

        return prompt

    # ==================================================
    # Debug Retrieved Chunks
    # ==================================================

    def print_retrieved_chunks(
        self,
        retrieved_chunks: List[Dict]
    ):

        if not retrieved_chunks:

            print(
                "\nNo chunks retrieved."
            )

            return

        for i, chunk in enumerate(
            retrieved_chunks,
            start=1
        ):

            print(
                f"\nRetrieved Chunk {i}:"
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
                    "Unknown"
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

            # Project-wide retrieval can contain
            # metadata chunks without a distance.

            distance = chunk.get(
                "distance"
            )

            if distance is not None:

                print(
                    "Distance:",
                    distance
                )

    # ==================================================
    # Save Project Metadata
    # ==================================================

    def save_project_metadata(
        self,
        metadata_path=(
            "vector_db/"
            "project_metadata.json"
        )
    ):

        if self.project_metadata is None:

            return

        directory = os.path.dirname(
            metadata_path
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True
            )

        with open(
            metadata_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                self.project_metadata,
                file,
                indent=4
            )

        print(
            "Project metadata saved."
        )

    # ==================================================
    # Load Project Metadata
    # ==================================================

    def load_project_metadata(
        self,
        metadata_path=(
            "vector_db/"
            "project_metadata.json"
        )
    ):

        if not os.path.exists(
            metadata_path
        ):

            self.project_metadata = None

            return None

        try:

            with open(
                metadata_path,
                "r",
                encoding="utf-8"
            ) as file:

                self.project_metadata = (
                    json.load(
                        file
                    )
                )

            print(
                "Project metadata loaded."
            )

            return self.project_metadata

        except (
            OSError,
            json.JSONDecodeError
        ) as e:

            print(
                "Could not load "
                "project metadata:",
                str(e)
            )

            self.project_metadata = None

            return None

    # ==================================================
    # Vector Database Exists
    # ==================================================

    def vector_database_exists(
        self
    ) -> bool:

        return (
            os.path.exists(
                "vector_db/faiss.index"
            )
            and
            os.path.exists(
                "vector_db/metadata.pkl"
            )
        )

    # ==================================================
    # Get Project Metadata
    # ==================================================

    def get_project_metadata(
        self
    ):

        if self.project_metadata is None:

            self.load_project_metadata()

        return self.project_metadata

    
# ============================================================
# Local Test
# ============================================================

if __name__ == "__main__":

    rag = RAGPipeline()

    if not rag.vector_database_exists():

        print(
            "No vector database found."
        )

        print(
            "Build/upload a project first."
        )

    else:

        print(
            "Vector database found."
        )

        metadata = (
            rag.get_project_metadata()
        )

        if metadata:

            print(
                "\nProject Information"
            )

            print(
                "Project:",
                metadata.get(
                    "project_name"
                )
            )

            print(
                "Files:",
                metadata.get(
                    "total_files"
                )
            )

            print(
                "Lines:",
                metadata.get(
                    "total_lines"
                )
            )

            print(
                "Languages:",
                list(
                    metadata.get(
                        "languages",
                        {}
                    ).keys()
                )
            )

        statistics = (
            rag.get_retrieval_statistics()
        )

        print(
            "\nRetrieval Statistics"
        )

        print(
            "Chunks:",
            statistics[
                "total_chunks"
            ]
        )

        print(
            "Indexed Files:",
            statistics[
                "total_indexed_files"
            ]
        )

    # --------------------------------------------------------
    # Interactive testing
    # --------------------------------------------------------

    while rag.vector_database_exists():

        question = input(
            "\nAsk Question "
            "(type 'exit' to quit): "
        )

        if (
            question
            .strip()
            .lower()
            == "exit"
        ):

            break

        try:

            print(
                "\nClassification:",
                rag.classify_query(
                    question
                )
            )

            prompt = (
                rag.generate_prompt(
                    question
                )
            )

            print(
                "\nPrompt generated successfully."
            )

            # Do not print the entire prompt during normal
            # testing because it may be very large.

            print(
                "Prompt characters:",
                len(prompt)
            )

        except Exception as e:

            print(
                "Error:",
                str(e)
            )