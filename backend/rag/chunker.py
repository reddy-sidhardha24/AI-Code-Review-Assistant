#Split code into smaller chunks     # backend/rag/chunker.py

from typing import List, Dict


class CodeChunker:
    def __init__(self, chunk_size: int = 100, overlap: int = 20):
        """
        chunk_size : Number of lines per chunk
        overlap    : Number of overlapping lines between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """
        Input:
            [
                {
                    "path": "...",
                    "name": "...",
                    "extension": ".py",
                    "content": "..."
                }
            ]

        Output:
            [
                {
                    "chunk_id": 1,
                    "path": "...",
                    "name": "...",
                    "extension": ".py",
                    "start_line": 1,
                    "end_line": 100,
                    "content": "..."
                }
            ]
        """

        chunks = []
        chunk_id = 1

        for doc in documents:

            lines = doc["content"].splitlines()

            start = 0

            while start < len(lines):

                end = min(start + self.chunk_size, len(lines))

                chunk_text = "\n".join(lines[start:end])

                chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "path": doc["path"],
                        "name": doc["name"],
                        "extension": doc["extension"],
                        "start_line": start + 1,
                        "end_line": end,
                        "content": chunk_text,
                    }
                )

                chunk_id += 1

                if end == len(lines):
                    break

                start += self.chunk_size - self.overlap

        return chunks


if __name__ == "__main__":

    from loader import ProjectLoader

    loader = ProjectLoader("../")
    documents = loader.load()

    chunker = CodeChunker(
        chunk_size=100,
        overlap=20
    )

    chunks = chunker.chunk_documents(documents)

    print(f"\nTotal Chunks : {len(chunks)}\n")

    for chunk in chunks[:5]:
        print("=" * 80)
        print(f"Chunk ID   : {chunk['chunk_id']}")
        print(f"File       : {chunk['name']}")
        print(f"Lines      : {chunk['start_line']} - {chunk['end_line']}")
        print(chunk["content"][:300]) 