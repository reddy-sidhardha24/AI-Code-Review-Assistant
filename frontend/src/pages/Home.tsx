import Upload from "../components/Upload";

function Home() {
  return (
    <main className="home-page">

      {/* =====================================================
          HERO
      ===================================================== */}

      <section className="home-hero">
        <div className="container">

          <div className="home-hero-content">

            <div className="eyebrow">
              RAG-powered code intelligence
            </div>

            <h1 className="home-title">
              Find bugs before
              <br />
              they reach
              <span> production.</span>
            </h1>

            <p className="home-description">
              Upload your codebase and let AI analyze bugs, security
              vulnerabilities, performance issues, and code quality
              using retrieval-augmented generation.
            </p>

            <div className="home-trust">
              <span>
                <span className="trust-dot"></span>
                Your code stays local
              </span>

              <span>•</span>

              <span>RAG-powered analysis</span>

              <span>•</span>

              <span>AI-assisted review</span>
            </div>

          </div>

        </div>
      </section>


      {/* =====================================================
          ANALYSIS SECTION
      ===================================================== */}

      <section className="analysis-section">

        <div className="container">

          <div className="analysis-header">

            <div>
              <div className="section-label">
                ANALYZE YOUR CODEBASE
              </div>

              <h2>
                Start with your project
              </h2>

              <p>
                Upload a complete project or select individual
                source files for analysis.
              </p>
            </div>

          </div>


          {/* Upload component */}

          <Upload />


          {/* =================================================
              ANALYSIS CAPABILITIES
              ================================================= */}

          <div className="capabilities">

            <div className="capability-card">

              <div className="capability-icon">
                !
              </div>

              <div>
                <h3>Bug Detection</h3>

                <p>
                  Identify runtime errors, logical bugs,
                  and dangerous code patterns.
                </p>
              </div>

            </div>


            <div className="capability-card">

              <div className="capability-icon">
                ◈
              </div>

              <div>
                <h3>Security Analysis</h3>

                <p>
                  Detect hardcoded secrets, unsafe practices,
                  and common vulnerabilities.
                </p>
              </div>

            </div>


            <div className="capability-card">

              <div className="capability-icon">
                ↗
              </div>

              <div>
                <h3>Performance</h3>

                <p>
                  Find inefficient algorithms, operations,
                  and scalability problems.
                </p>
              </div>

            </div>


            <div className="capability-card">

              <div className="capability-icon">
                ✓
              </div>

              <div>
                <h3>Code Quality</h3>

                <p>
                  Improve readability, maintainability,
                  and overall code structure.
                </p>
              </div>

            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          HOW IT WORKS
          ===================================================== */}

      <section className="workflow-section">

        <div className="container">

          <div className="workflow-heading">

            <div className="section-label">
              HOW IT WORKS
            </div>

            <h2>
              From source code to
              <span> actionable insights.</span>
            </h2>

          </div>


          <div className="workflow-grid">

            <div className="workflow-step">

              <div className="workflow-number">
                01
              </div>

              <h3>
                Upload
              </h3>

              <p>
                Provide your project ZIP or individual
                source files.
              </p>

            </div>


            <div className="workflow-line"></div>


            <div className="workflow-step">

              <div className="workflow-number">
                02
              </div>

              <h3>
                Index
              </h3>

              <p>
                Code is chunked and converted into
                semantic embeddings.
              </p>

            </div>


            <div className="workflow-line"></div>


            <div className="workflow-step">

              <div className="workflow-number">
                03
              </div>

              <h3>
                Retrieve
              </h3>

              <p>
                RAG retrieves the most relevant code
                context for your question.
              </p>

            </div>


            <div className="workflow-line"></div>


            <div className="workflow-step">

              <div className="workflow-number">
                04
              </div>

              <h3>
                Review
              </h3>

              <p>
                AI generates structured findings
                from the retrieved context.
              </p>

            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          FOOTER NOTE
          ===================================================== */}

      <div className="home-footer-note">
        CodeReview AI · RAG + LLM powered code intelligence
      </div>

    </main>
  );
}

export default Home;