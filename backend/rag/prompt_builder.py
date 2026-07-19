# backend/rag/prompt_builder.py

from typing import List, Dict


class PromptBuilder:
    """
    Builds a structured prompt for the LLM using:
    - User question
    - Retrieved code chunks
    """

    def __init__(self):
        pass

    def build_prompt(self, query: str, retrieved_chunks: List[Dict]) -> str:

        context = ""

        for i, chunk in enumerate(retrieved_chunks, start=1):

            context += (
                f"\n{'=' * 80}\n"
                f"Chunk {i}\n"
                f"File: {chunk['path']}\n"
                f"Lines: {chunk['start_line']} - {chunk['end_line']}\n"
                f"{'=' * 80}\n"
                f"{chunk['content']}\n"
            )

        prompt = f"""
You are an Expert Senior Software Engineer and Professional Code Reviewer.

You are reviewing a software project using Retrieval-Augmented Generation (RAG).

Use ONLY the project context provided below to answer the user's question.
If the answer cannot be determined from the provided context, clearly state that the information is not available in the retrieved code.

==========================
PROJECT CONTEXT
==========================

{context}

==========================
USER QUESTION
==========================

{query}

==========================
REVIEW GUIDELINES
==========================

Analyze the retrieved code and provide:

1. Project Summary
   - Explain what the retrieved code does.

2. Architecture
   - Describe the design and flow if possible.

3. Bugs
   - Logical errors
   - Runtime exceptions
   - Edge cases

4. Security Issues
   - SQL Injection
   - XSS
   - Authentication
   - Authorization
   - Hardcoded secrets
   - Unsafe file handling

5. Performance Issues
   - Inefficient loops
   - Duplicate operations
   - Memory usage
   - Expensive computations

6. Code Quality
   - Clean Code
   - SOLID Principles
   - Naming conventions
   - Maintainability
   - Readability

7. Suggestions
   - Recommend improvements.
   - Mention refactoring opportunities.

8. Overall Rating
   - Rate the code out of 10.

Format the response using Markdown with headings and bullet points.
"""

        return prompt


if __name__ == "__main__":

    sample_chunks = [
        {
            "path": "backend/auth.py",
            "start_line": 10,
            "end_line": 45,
            "content": """
def login():
    username = request.form['username']
    password = request.form['password']
"""
        }
    ]

    builder = PromptBuilder()

    prompt = builder.build_prompt(
        "Review login authentication",
        sample_chunks
    )

    print(prompt)