import { useNavigate } from "react-router-dom";

function Home() {
  const navigate = useNavigate();
  return (
    <main className="home-page">
      {/* =====================================================
          HERO
          ===================================================== */}
      <section className="home-hero">
        <div className="container">
          <div className="home-hero-content">
            <div className="eyebrow">
              AI Code Review Assistant
            </div>

            <h1 className="home-title">
              Detect issues & fix bugs
              <br />
              before they reach
              <span> production.</span>
            </h1>

            <p className="home-description">
              Start a guided review by choosing a project archive, source files, pasted code, or a GitHub repository.
              Our RAG-powered engine indexes your code, identifies security vulnerabilities,
              runtime errors, and performance bottlenecks, and generates verified fixes.
            </p>

            <div className="home-trust">
              <span>
                <span className="trust-dot"></span>
                Grounded source verification
              </span>
              <span>•</span>
              <span>RAG vector retrieval</span>
              <span>•</span>
              <span>Multi-model & multi-agent support</span>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          REVIEW ENTRY SECTION
          ===================================================== */}
      <section className="analysis-section">
        <div className="container">
          <div className="analysis-header">
            <div className="section-label">READY TO START?</div>
            <h2>Start a Code Review</h2>
            <p>
              Choose your project source and set up the review in a guided flow.
            </p>
          </div>

          <div style={{ display: "flex", justifyContent: "center", margin: "28px 0 44px" }}>
            <button type="button" className="btn-primary" onClick={() => navigate("/review")}>
              Start Review <span aria-hidden="true">→</span>
            </button>
          </div>

          {/* Capabilities Grid */}
          <div className="capabilities">
            <div className="capability-card">
              <div className="capability-icon">!</div>
              <div>
                <h3>Bug Detection</h3>
                <p>
                  Identify runtime exceptions, null dereferences, logic flaws, and edge cases with exact line numbers.
                </p>
              </div>
            </div>

            <div className="capability-card">
              <div className="capability-icon">🛡️</div>
              <div>
                <h3>Security Analysis</h3>
                <p>
                  Detect OWASP vulnerabilities, SQL injection, hardcoded secrets, and insecure dependencies.
                </p>
              </div>
            </div>

            <div className="capability-card">
              <div className="capability-icon">⚡</div>
              <div>
                <h3>Performance Audits</h3>
                <p>
                  Uncover algorithmic bottlenecks, high memory consumption, unoptimized database queries, and blocking calls.
                </p>
              </div>
            </div>

            <div className="capability-card">
              <div className="capability-icon">✓</div>
              <div>
                <h3>Code Quality</h3>
                <p>
                  Enforce SOLID design principles, clean architecture patterns, cyclomatic complexity reduction, and readability.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          HOW IT WORKS (CLEAN & NON-REPETITIVE)
          ===================================================== */}
      <section className="workflow-section">
        <div className="container">
          <div className="workflow-heading">
            <div className="section-label">HOW IT WORKS</div>
            <h2>From Source Code to <span>Verified Fixes</span></h2>
          </div>

          <div className="workflow-grid">
            <div className="workflow-step">
              <div className="workflow-number">01</div>
              <h3>1. Ingest</h3>
              <p>Upload project ZIPs, source files, or connect your GitHub repository.</p>
            </div>

            <div className="workflow-step">
              <div className="workflow-number">02</div>
              <h3>2. Index & Retrieve</h3>
              <p>RAG pipeline chunks your code and retrieves relevant contexts using semantic vector embeddings.</p>
            </div>

            <div className="workflow-step">
              <div className="workflow-number">03</div>
              <h3>3. Audit & Ground</h3>
              <p>Specialist agents analyze the retrieved code and verify every issue against the actual lines.</p>
            </div>

            <div className="workflow-step">
              <div className="workflow-number">04</div>
              <h3>4. Fix & Export</h3>
              <p>Download audit reports (PDF/MD/HTML), get full corrected ZIPs, or open GitHub Pull Requests.</p>
            </div>
          </div>
        </div>
      </section>

      <div className="home-footer-note">
        AI Code Review Assistant · Grounded code intelligence with multi-provider LLM support
      </div>
    </main>
  );
}

export default Home;
