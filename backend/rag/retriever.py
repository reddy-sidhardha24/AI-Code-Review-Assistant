from sentence_transformers import SentenceTransformer

from .vector_store import VectorStore
from .embedder import CodeEmbedder


class Retriever:

    def __init__(
        self,
        model_name="all-MiniLM-L6-v2",
        index_path="vector_db/faiss.index",
        metadata_path="vector_db/metadata.pkl"
    ):
        """
        Initializes:
        1. Embedding model
        2. Loads FAISS vector database
        """

        print("Loading embedding model...")
        self.embedder = CodeEmbedder(model_name)

        print("Loading vector database...")
        self.vector_store = VectorStore()
        self.vector_store.load(index_path, metadata_path)

        print("Retriever Ready.")

    def retrieve(self, query: str, top_k: int = 5):
        """
        Retrieve the most relevant code chunks.
        """

        query_embedding = self.embedder.model.encode(
            query,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        results = self.vector_store.search(
            query_embedding,
            top_k=top_k
        )

        return results


if __name__ == "__main__":

    retriever = Retriever()

    question = input("Ask a question: ")

    results = retriever.retrieve(question)

    print("\nRetrieved Chunks\n")

    for i, chunk in enumerate(results, start=1):

        print("=" * 80)

        print(f"Rank        : {i}")
        print(f"File        : {chunk['path']}")
        print(f"Lines       : {chunk['start_line']} - {chunk['end_line']}")
        print(f"Distance    : {chunk['distance']:.4f}")

        print("\nCode Preview\n")

        print(chunk["content"][:500])

        print("\n")