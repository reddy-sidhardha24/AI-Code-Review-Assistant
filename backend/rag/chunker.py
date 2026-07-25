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
        Converts:

        public class Main {
            int x = 10;
        }

        into numbered source code such as:

        1 | public class Main {
        2 |     int x = 10;
        3 | }

        start_line represents the real line number
        in the original source file.
        """

        numbered_lines = []

        for offset, line in enumerate(lines):

            actual_line_number = (
                start_line + offset
            )

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

            content = doc.get(
                "content",
                ""
            )

            # Keep blank lines because they are real
            # source-code lines.
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

                # -----------------------------------------
                # Real source line numbers
                # -----------------------------------------

                start_line = start + 1
                end_line = end

                # -----------------------------------------
                # Plain content
                #
                # Used for embeddings / semantic search.
                # -----------------------------------------

                chunk_text = "\n".join(
                    chunk_lines
                )

                # -----------------------------------------
                # Numbered content
                #
                # Used later by the LLM so it can identify
                # exact source-code locations.
                # -----------------------------------------

                numbered_text = (
                    self._add_line_numbers(
                        chunk_lines,
                        start_line
                    )
                )

                # -----------------------------------------
                # Create Chunk
                # -----------------------------------------

                chunk = {
                    "chunk_id": chunk_id,

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

                    # Plain source code
                    "content": chunk_text,

                    # Source code with exact line numbers
                    "numbered_content": numbered_text,
                }

                chunks.append(chunk)

                chunk_id += 1

                # Last chunk
                if end >= len(lines):
                    break

                # Move forward while preserving overlap
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

    print(
        f"\nTotal Chunks: {len(chunks)}\n"
    )

    for chunk in chunks:

        print("=" * 80)

        print(
            f"Chunk ID : "
            f"{chunk['chunk_id']}"
        )

        print(
            f"File     : "
            f"{chunk['name']}"
        )

        print(
            f"Language : "
            f"{chunk['language']}"
        )

        print(
            f"Lines    : "
            f"{chunk['start_line']} - "
            f"{chunk['end_line']}"
        )

        print("\nPlain Content:\n")

        print(
            chunk["content"]
        )

        print("\nNumbered Content:\n")

        print(
            chunk["numbered_content"]
        )

        print()