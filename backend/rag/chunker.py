# backend/rag/chunker.py

from typing import List, Dict


class CodeChunker:

    def __init__(
        self,
        chunk_size: int = 100,
        overlap: int = 20
    ):
        """
        chunk_size:
            Maximum number of lines in each chunk.

        overlap:
            Number of lines shared between consecutive chunks.
        """

        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than 0."
            )

        if overlap < 0:
            raise ValueError(
                "overlap cannot be negative."
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    # =====================================================
    # Add Source Line Numbers
    # =====================================================

    def _add_line_numbers(
        self,
        lines: List[str],
        start_line: int
    ) -> str:
        """
        Adds original source line numbers.
        """

        numbered_lines = []

        for offset, line in enumerate(lines):

            actual_line_number = start_line + offset

            numbered_lines.append(
                f"{actual_line_number:>5} | {line}"
            )

        return "\n".join(numbered_lines)

    # =====================================================
    # Chunk Documents
    # =====================================================

    def chunk_documents(
        self,
        documents: List[Dict]
    ) -> List[Dict]:

        chunks = []

        chunk_id = 1

        for doc in documents:

            # ------------------------------------------
            # Track chunk order within this file
            # ------------------------------------------

            file_chunk_index = 0

            content = doc.get(
                "content",
                ""
            )

            lines = content.splitlines()

            if not lines:
                continue

            start = 0

            while start < len(lines):

                end = min(
                    start + self.chunk_size,
                    len(lines)
                )

                chunk_lines = lines[start:end]

                start_line = start + 1
                end_line = end

                # ------------------------------------------
                # Plain content
                # ------------------------------------------

                chunk_text = "\n".join(
                    chunk_lines
                )

                # ------------------------------------------
                # Numbered content
                # ------------------------------------------

                numbered_text = (
                    self._add_line_numbers(
                        chunk_lines,
                        start_line
                    )
                )

                # ------------------------------------------
                # Create Chunk
                # ------------------------------------------

                chunk = {

                    # Global chunk id
                    "chunk_id": chunk_id,

                    # Position inside this file
                    "file_chunk_index": file_chunk_index,

                    "path": doc.get(
                        "path",
                        "Unknown"
                    ),

                    "relative_path": doc.get(
                        "relative_path",
                        doc.get(
                            "path",
                            "Unknown"
                        )
                    ),

                    "name": doc.get(
                        "name",
                        "Unknown"
                    ),

                    "extension": doc.get(
                        "extension",
                        ""
                    ),

                    "language": doc.get(
                        "language",
                        "Unknown"
                    ),

                    "start_line": start_line,

                    "end_line": end_line,

                    # Plain code (used for embeddings)
                    "content": chunk_text,

                    # Line-numbered code (used by LLM)
                    "numbered_content": numbered_text,
                }

                chunks.append(chunk)

                chunk_id += 1
                file_chunk_index += 1

                # Last chunk reached
                if end >= len(lines):
                    break

                # Move forward with overlap
                start += (
                    self.chunk_size -
                    self.overlap
                )

        return chunks


# ============================================================
# Local Test
# ============================================================

if __name__ == "__main__":

    sample_documents = [
        {
            "path": "src/Main.java",
            "relative_path": "src/Main.java",
            "name": "Main.java",
            "extension": ".java",
            "language": "Java",
            "content": """public class Main {

    public static void main(String[] args) {

        int[] arr = {10, 20, 30};

        for (int i = 0; i < arr.length; i++) {
            System.out.println(arr[i]);
        }
    }
}"""
        }
    ]

    chunker = CodeChunker(
        chunk_size=5,
        overlap=1
    )

    chunks = chunker.chunk_documents(
        sample_documents
    )

    print(f"\nTotal Chunks: {len(chunks)}\n")

    for chunk in chunks:

        print("=" * 80)

        print(
            f"Chunk ID         : {chunk['chunk_id']}"
        )

        print(
            f"File Chunk Index : {chunk['file_chunk_index']}"
        )

        print(
            f"File             : {chunk['name']}"
        )

        print(
            f"Language         : {chunk['language']}"
        )

        print(
            f"Lines            : {chunk['start_line']} - {chunk['end_line']}"
        )

        print("\nPlain Content:\n")

        print(chunk["content"])

        print("\nNumbered Content:\n")

        print(chunk["numbered_content"])

        print()