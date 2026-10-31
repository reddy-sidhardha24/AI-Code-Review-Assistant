import React from "react";
import { useNavigate } from "react-router-dom";

const HowToUse: React.FC = () => {
  const navigate = useNavigate();

  return (
    <main className="how-to-use-container">
      <div style={{ textAlign: "center", marginBottom: "40px" }}>
        <div className="eyebrow">Documentation & User Manual</div>
        <h1 style={{ fontSize: "36px", fontWeight: 800, marginTop: "10px", marginBottom: "12px", color: "var(--text-primary)" }}>
          How to Use AI Code Review Assistant
        </h1>
        <p style={{ fontSize: "17px", color: "var(--text-secondary)", maxWidth: "700px", margin: "0 auto 24px" }}>
          A complete step-by-step walkthrough for configuring AI models, uploading codebases, running deep audits, downloading verified reports, and opening automatic GitHub Pull Requests.
        </p>

        <div style={{ display: "flex", justifyContent: "center", gap: "12px" }}>
          <button className="btn-primary" onClick={() => navigate("/review")}>
            Start a Review Now →
          </button>
          <button className="btn-secondary" onClick={() => navigate("/configuration")}>
            Open Configuration ⚙️
          </button>
        </div>
      </div>

      {/* STEP 1 */}
      <div className="guide-step-card">
        <div className="guide-step-header">
          <div className="guide-step-num">1</div>
          <h2 className="guide-step-title">Configure Your Preferred AI Models</h2>
        </div>
        <div className="guide-step-content">
          <p>
            The assistant supports unlimited model configurations across both high-speed cloud APIs and 100% private local models:
          </p>
          <ul>
            <li><strong>Cloud APIs:</strong> Connect Groq (ultra-fast Llama models), OpenAI (GPT-4o), Google Gemini (Gemini 2.5), or Anthropic Claude (Claude 3.5 Sonnet).</li>
            <li><strong>Local Models (Ollama):</strong> Run private audits locally on your computer with <strong>Ollama</strong>. The Configuration page features an <em>Auto-Detect</em> button that automatically fetches installed models from your local Ollama instance (default <code>http://localhost:11434</code>).</li>
            <li><strong>Seamless Switching:</strong> Add as many models as you need, test connectivity with the <em>Test Connection</em> button, and activate your chosen model with one click.</li>
          </ul>
        </div>
      </div>

      {/* STEP 2 */}
      <div className="guide-step-card">
        <div className="guide-step-header">
          <div className="guide-step-num">2</div>
          <h2 className="guide-step-title">Upload or Connect Source Code</h2>
        </div>
        <div className="guide-step-content">
          <p>Select any of the 4 supported ingestion methods on the Home or Upload tab:</p>
          <ul>
            <li><strong>ZIP Archive:</strong> Upload an entire project archive (up to 50MB). The backend safely extracts files, strips binaries and cache directories, and constructs a semantic vector index using RAG.</li>
            <li><strong>Multiple Files:</strong> Select and upload specific source files for batch analysis.</li>
            <li><strong>Paste Code:</strong> Paste raw code snippets with a filename for immediate instant evaluation.</li>
            <li><strong>GitHub Repository:</strong> Pull public repositories by URL, or link your GitHub account using the GitHub App integration to select repositories and branches directly from a dropdown.</li>
          </ul>
        </div>
      </div>

      {/* STEP 3 */}
      <div className="guide-step-card">
        <div className="guide-step-header">
          <div className="guide-step-num">3</div>
          <h2 className="guide-step-title">Select Review Category & Mode</h2>
        </div>
        <div className="guide-step-content">
          <p>Choose an audit category to direct the AI's analytical focus:</p>
          <ul>
            <li><strong>Full Project Review:</strong> Holistic audit evaluating bugs, security, performance, and architecture.</li>
            <li><strong>Bugs & Runtime Errors:</strong> Pinpoints null dereferences, syntax errors, logic flaws, and unhandled exceptions.</li>
            <li><strong>Security Vulnerabilities:</strong> Detects OWASP Top 10 vulnerabilities, SQL injection, XSS, and hardcoded secrets.</li>
            <li><strong>Performance Optimization:</strong> Flags slow algorithmic complexity, memory leaks, and redundant operations.</li>
            <li><strong>Code Quality:</strong> Highlights SOLID principles, maintainability, code smell, and refactoring opportunities.</li>
          </ul>
          <p style={{ marginTop: "14px" }}>
            <strong>Single Agent vs Multi-Agent Mode:</strong> In Configuration, choose between <em>Single Agent</em> (fast, single-pass review) or <em>Multi-Agent Mode</em> (runs 4 specialized parallel reviewers simultaneously: Bug Detective, AppSec Auditor, Performance Architect, and Clean Code Inspector, then synthesizes a unified consensus report).
          </p>
        </div>
      </div>

      {/* STEP 4 */}
      <div className="guide-step-card">
        <div className="guide-step-header">
          <div className="guide-step-num">4</div>
          <h2 className="guide-step-title">Inspect Verified 8-Point Solutions & Scores</h2>
        </div>
        <div className="guide-step-content">
          <p>
            Every detected issue is verified by the backend Grounding Validator to ensure the cited lines and evidence exist in your actual code (eliminating hallucinations). Each finding delivers an 8-point solution breakdown:
          </p>
          <ul>
            <li><strong>1. Problem Title:</strong> Concise definition of the defect.</li>
            <li><strong>2. Exact Location:</strong> File name and verified line number.</li>
            <li><strong>3. Severity Level:</strong> Critical, High, Medium, or Low badge.</li>
            <li><strong>4. Technical Explanation:</strong> Root cause and risk analysis.</li>
            <li><strong>5. Actionable Recommendation:</strong> Step-by-step fix instruction.</li>
            <li><strong>6. Original Code Snippet:</strong> Contextual snippet before correction.</li>
            <li><strong>7. Corrected Code Snippet:</strong> Refactored, production-ready replacement code.</li>
            <li><strong>8. Correction Rationale:</strong> Architectural reasoning for why the fix is superior.</li>
          </ul>
        </div>
      </div>

      {/* STEP 5 */}
      <div className="guide-step-card">
        <div className="guide-step-header">
          <div className="guide-step-num">5</div>
          <h2 className="guide-step-title">Download Reports & Corrected Project ZIPs</h2>
        </div>
        <div className="guide-step-content">
          <p>Export your audit results in multiple industry-standard formats:</p>
          <ul>
            <li><strong>📄 Download PDF Report:</strong> High-resolution, printable executive audit report with health score.</li>
            <li><strong>📝 Download Markdown Report:</strong> Clean Markdown documentation ready for repo commits or wikis.</li>
            <li><strong>🌐 Download Standalone HTML:</strong> Offline interactive HTML report with formatted comparison diffs.</li>
            <li><strong>📦 Full Corrected Project ZIP:</strong> Downloads the entire project codebase with all AI corrections applied to their respective files!</li>
            <li><strong>📁 Corrected Files Only ZIP:</strong> Downloads an archive containing strictly the files and scripts that were modified.</li>
          </ul>
        </div>
      </div>

      {/* STEP 6 */}
      <div className="guide-step-card">
        <div className="guide-step-header">
          <div className="guide-step-num">6</div>
          <h2 className="guide-step-title">Push Fixes & Open GitHub Pull Requests</h2>
        </div>
        <div className="guide-step-content">
          <p>
            When reviewing a GitHub repository, you don't need to manually copy code changes back into your editor:
          </p>
          <ul>
            <li>Click the <strong>🚀 Create Branch & Pull Request</strong> button in the Review workspace.</li>
            <li>The assistant automatically creates an isolated branch (e.g. <code>ai-review/fix-20261007</code>), commits every corrected file, and opens a new Pull Request against your base branch.</li>
            <li>Your primary code branch remains protected and untampered with.</li>
          </ul>
        </div>
      </div>

      {/* STEP 7 */}
      <div className="guide-step-card">
        <div className="guide-step-header">
          <div className="guide-step-num">7</div>
          <h2 className="guide-step-title">Frequently Asked Questions (FAQ)</h2>
        </div>
        <div className="guide-step-content">
          <p><strong>Q: Does the app work without internet?</strong><br />
          A: Yes! When using a local Ollama model, code analysis, vector embedding, and report downloads run 100% locally on your machine with zero external data transmission.</p>

          <p style={{ marginTop: "10px" }}><strong>Q: Where are my reviews saved?</strong><br />
          A: All reviews and uploaded file metadata are safely stored in your local SQLite database (<code>data/code_review.db</code>) and viewable in the Dashboard and History tabs.</p>

          <p style={{ marginTop: "10px" }}><strong>Q: How does email delivery work?</strong><br />
          A: Reports and corrected code can be sent directly to client inboxes using our hosted cloud delivery API, with local outbox archiving as a backup.</p>
        </div>
      </div>
    </main>
  );
};

export default HowToUse;
