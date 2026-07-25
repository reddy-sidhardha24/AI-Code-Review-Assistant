# backend/rag/pipeline.py

import os
import json

from .loader import ProjectLoader
from .chunker import CodeChunker
from .embedder import CodeEmbedder
from .vector_store import VectorStore
from .retriever import Retriever
from .prompt_builder import PromptBuilder


class RAGPipeline:
    """
    Complete RAG Pipeline

    Project Loader
            ↓
    Project Metadata
            ↓
    Chunker
            ↓
    Embedder
            ↓
    Vector Store (FAISS)
            ↓
    Retriever
            ↓
    Prompt Builder
    """

    def __init__(self):

        print("\nInitializing RAG Pipeline...\n")

        self.loader = None

        self.chunker = CodeChunker()

        self.embedder = CodeEmbedder()

        self.vector_store = VectorStore()

        self.prompt_builder = PromptBuilder()

        # Store project-wide metadata
        self.project_metadata = None

        # Retriever will be initialized only if
        # an existing vector database is available.
        self.retriever = None

        if self.vector_database_exists():

            print("Existing vector database found.")

            try:
                self.retriever = Retriever()

                print("Retriever loaded successfully.")

            except Exception as e:

                print(
                    f"Could not initialize retriever: {e}"
                )

        # Load existing project metadata if available
        self.load_project_metadata()

        print("\nRAG Pipeline Ready.\n")

    # ==================================================
    # Build Vector Database
    # ==================================================

    def build_vector_database(self, project_path):

        print("\nLoading project...")

        # ----------------------------------------------
        # Load project
        # ----------------------------------------------

        self.loader = ProjectLoader(project_path)

        documents = self.loader.load()

        if not documents:

            raise ValueError(
                "No supported source-code files were found "
                "inside the uploaded project."
            )

        print(
            f"Loaded {len(documents)} files."
        )

        # ----------------------------------------------
        # Get project metadata
        # ----------------------------------------------

        self.project_metadata = (
            self.loader.get_metadata()
        )

        print("\nProject Metadata:")

        print(
            f"Project Name : "
            f"{self.project_metadata['project_name']}"
        )

        print(
            f"Total Files  : "
            f"{self.project_metadata['total_files']}"
        )

        print(
            f"Total Lines  : "
            f"{self.project_metadata['total_lines']}"
        )

        print(
            f"Languages    : "
            f"{list(self.project_metadata['languages'].keys())}"
        )

        # Save metadata separately
        self.save_project_metadata()

        # ----------------------------------------------
        # Chunk project
        # ----------------------------------------------

        print("\nChunking...")

        chunks = self.chunker.chunk_documents(
            documents
        )

        if not chunks:

            raise ValueError(
                "No code chunks were generated."
            )

        print(
            f"Generated {len(chunks)} chunks."
        )

        # ----------------------------------------------
        # Generate embeddings
        # ----------------------------------------------

        print("\nGenerating embeddings...")

        embedded_chunks = (
            self.embedder.embed_chunks(chunks)
        )

        # ----------------------------------------------
        # IMPORTANT:
        # Create a NEW vector store for every project.
        #
        # Otherwise uploading project B after project A
        # could leave project A vectors in memory.
        # ----------------------------------------------

        print("\nCreating FAISS index...")

        self.vector_store = VectorStore()

        self.vector_store.add_chunks(
            embedded_chunks
        )

        self.vector_store.save()

        print(
            "\nVector database created successfully."
        )

        # ----------------------------------------------
        # IMPORTANT:
        # Reload retriever after rebuilding FAISS.
        #
        # The old Retriever may still contain the
        # previous project's index in memory.
        # ----------------------------------------------

        print(
            "\nReloading retriever with new project..."
        )

        self.retriever = Retriever()

        print(
            "Retriever updated successfully."
        )

        return self.project_metadata

    # ==================================================
    # Generate RAG Prompt
    # ==================================================

    def generate_prompt(
        self,
        query,
        top_k=5
    ):

        if not query or not query.strip():

            raise ValueError(
                "Question cannot be empty."
            )

        # ----------------------------------------------
        # Make sure vector database exists
        # ----------------------------------------------

        if not self.vector_database_exists():

            raise ValueError(
                "No vector database found. "
                "Please upload a project first."
            )

        # ----------------------------------------------
        # Initialize retriever if necessary
        # ----------------------------------------------

        if self.retriever is None:

            print(
                "\nInitializing retriever..."
            )

            self.retriever = Retriever()

        # ----------------------------------------------
        # Retrieve relevant code
        # ----------------------------------------------

        print(
            "\nRetrieving relevant code...\n"
        )

        retrieved_chunks = (
            self.retriever.retrieve(
                query=query,
                top_k=top_k
            )
        )

        print(
            f"Retrieved "
            f"{len(retrieved_chunks)} chunks."
        )

        # ----------------------------------------------
        # Debug retrieved chunks
        # ----------------------------------------------

        for i, chunk in enumerate(
            retrieved_chunks,
            start=1
        ):

            print(
                f"\nRetrieved Chunk {i}:"
            )

            print(
                f"File: "
                f"{chunk.get('name', 'Unknown')}"
            )

            print(
                f"Path: "
                f"{chunk.get('path', 'Unknown')}"
            )

            print(
                f"Lines: "
                f"{chunk.get('start_line', '?')} - "
                f"{chunk.get('end_line', '?')}"
            )

            print(
                f"Distance: "
                f"{chunk.get('distance', '?')}"
            )

        # ----------------------------------------------
        # Load metadata if necessary
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

        return prompt

    # ==================================================
    # Save Project Metadata
    # ==================================================

    def save_project_metadata(
        self,
        metadata_path="vector_db/project_metadata.json"
    ):

        if self.project_metadata is None:
            return

        os.makedirs(
            os.path.dirname(metadata_path),
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
        metadata_path="vector_db/project_metadata.json"
    ):

        if not os.path.exists(metadata_path):

            self.project_metadata = None

            return None

        try:

            with open(
                metadata_path,
                "r",
                encoding="utf-8"
            ) as file:

                self.project_metadata = (
                    json.load(file)
                )

            print(
                "Project metadata loaded."
            )

            return self.project_metadata

        except Exception as e:

            print(
                f"Could not load project metadata: {e}"
            )

            self.project_metadata = None

            return None

    # ==================================================
    # Check Vector Database
    # ==================================================

    def vector_database_exists(self):

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

    def get_project_metadata(self):

        if self.project_metadata is None:

            self.load_project_metadata()

        return self.project_metadata


# ======================================================
# Test Pipeline
# ======================================================

if __name__ == "__main__":

    rag = RAGPipeline()

    if not rag.vector_database_exists():

        print(
            "No vector database found."
        )

        print(
            "Building vector database..."
        )

        rag.build_vector_database("../")

    else:

        print(
            "Vector database already exists."
        )

        metadata = (
            rag.get_project_metadata()
        )

        if metadata:

            print("\nProject Information:")

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
                metadata.get(
                    "languages"
                )
            )

    while True:

        question = input(
            "\nAsk Question "
            "(type 'exit' to quit): "
        )

        if question.lower() == "exit":
            break

        prompt = rag.generate_prompt(
            question
        )

        print(
            "\n" + "=" * 80
        )

        print(prompt)

        print(
            "=" * 80
        )