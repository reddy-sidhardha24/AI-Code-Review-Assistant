import { useNavigate } from "react-router-dom";

function About() {
  const navigate = useNavigate();

  return (
    <main className="about-container">
      <div className="about-card">
        <div className="about-header">
          <div className="section-label">SYSTEM ARCHITECTURE</div>
          <h1>About AI Code Review Assistant</h1>
          <p>
            An intelligent, privacy-first software auditing platform combining Retrieval-Augmented Generation (RAG), strict evidence verification, multi-provider LLMs, and automated GitHub remediation.
          </p>

          <div style={{ display: "flex", justifyContent: "center", gap: "12px", marginTop: "20px" }}>
            <button className="btn-primary" onClick={() => navigate("/review")}>
              Run Code Review →
            </button>
            <button className="btn-secondary" onClick={() => navigate("/how-to-use")}>
              Read User Guide
            </button>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "28px", marginTop: "32px" }}>
          <div>
            <h3 style={{ fontSize: "18px", color: "var(--text-primary)", marginBottom: "8px" }}>
              1. Retrieval-Augmented Code Indexing (RAG)
            </h3>
            <p style={{ fontSize: "15px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
              Rather than blindly sending your entire project to an LLM where context limits truncate files and hallucination rates surge, our RAG pipeline systematically decomposes source code using language-aware chunking. High-dimensional vector embeddings are generated locally via Sentence Transformers and indexed using FAISS.
            </p>
          </div>

          <div>
            <h3 style={{ fontSize: "18px", color: "var(--text-primary)", marginBottom: "8px" }}>
              2. Anti-Hallucination Evidence Verification
            </h3>
            <p style={{ fontSize: "15px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
              Our backend employs an automated Grounding Validator. Every finding proposed by the AI must prove that the referenced line numbers, problematic syntax, and file names exist in the indexed source code. Any unsupported finding is immediately filtered out before the user sees it.
            </p>
          </div>

          <div>
            <h3 style={{ fontSize: "18px", color: "var(--text-primary)", marginBottom: "8px" }}>
              3. Flexible Provider Ecosystem (Cloud & Local)
            </h3>
            <p style={{ fontSize: "15px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
              Engineers have complete autonomy over their model execution. You can leverage cloud providers (Groq, OpenAI, Google Gemini, Anthropic Claude) for peak intelligence, or connect a local Ollama instance for 100% offline, privacy-compliant code reviews.
            </p>
          </div>

          <div>
            <h3 style={{ fontSize: "18px", color: "var(--text-primary)", marginBottom: "8px" }}>
              4. Complete Automated Remediation
            </h3>
            <p style={{ fontSize: "15px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
              Identifying bugs is only half the battle. Our system synthesizes tested replacement code, packages complete corrected project archives (ZIP), and integrates directly with the GitHub App ecosystem to create isolated feature branches and open automated Pull Requests.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}

export default About;