# backend/rag/pipeline.py

import os

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

        # Load retriever only once
        self.retriever = Retriever()

        print("\nRAG Pipeline Ready.\n")

    # --------------------------------------------------
    # Build Vector Database
    # --------------------------------------------------

    def build_vector_database(self, project_path):

        print("\nLoading project...")

        self.loader = ProjectLoader(project_path)

        documents = self.loader.load()

        print(f"Loaded {len(documents)} files.")

        print("\nChunking...")

        chunks = self.chunker.chunk_documents(documents)

        print(f"Generated {len(chunks)} chunks.")

        print("\nGenerating embeddings...")

        embedded_chunks = self.embedder.embed_chunks(chunks)

        print("\nCreating FAISS index...")

        self.vector_store.add_chunks(embedded_chunks)

        # Save using the default paths configured in VectorStore
        self.vector_store.save()

        print("\nVector database created successfully.")

    # --------------------------------------------------
    # Generate Prompt using RAG
    # --------------------------------------------------

    def generate_prompt(self, query, top_k=5):

        print("\nRetrieving relevant code...\n")

        retrieved_chunks = self.retriever.retrieve(
            query=query,
            top_k=top_k
        )

        print(f"Retrieved {len(retrieved_chunks)} chunks.")

        prompt = self.prompt_builder.build_prompt(
            query=query,
            retrieved_chunks=retrieved_chunks
        )

        return prompt

    # --------------------------------------------------
    # Check if Vector Database Exists
    # --------------------------------------------------

    def vector_database_exists(self):

        return (
            os.path.exists("vector_db/faiss.index")
            and
            os.path.exists("vector_db/metadata.pkl")
        )


# --------------------------------------------------
# Test Pipeline
# --------------------------------------------------

if __name__ == "__main__":

    rag = RAGPipeline()

    if not rag.vector_database_exists():

        print("No vector database found.")
        print("Building vector database...")

        rag.build_vector_database("../")

    else:
        print("Vector database already exists.")

    while True:

        question = input("\nAsk Question (type 'exit' to quit): ")

        if question.lower() == "exit":
            break

        prompt = rag.generate_prompt(question)

        print("\n" + "=" * 80)
        print(prompt)
        print("=" * 80)