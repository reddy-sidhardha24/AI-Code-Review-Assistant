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
              Analyze an entire codebase or paste a
              single source file. AI retrieves relevant
              code context and identifies bugs, security
              vulnerabilities, performance issues, and
              code-quality problems.
            </p>

            <div className="home-trust">

              <span>
                <span className="trust-dot"></span>
                Local project processing
              </span>

              <span>•</span>

              <span>
                RAG-powered analysis
              </span>

              <span>•</span>

              <span>
                Structured AI review
              </span>

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
                ANALYZE YOUR CODE
              </div>

              <h2>
                Start your analysis
              </h2>

              <p>
                Upload a complete project, select
                individual source files, or paste code
                for a quick review.
              </p>

            </div>

          </div>


          {/* Upload / Paste Component */}

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

                <h3>
                  Bug Detection
                </h3>

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

                <h3>
                  Security Analysis
                </h3>

                <p>
                  Detect hardcoded secrets, unsafe
                  practices, and common vulnerabilities.
                </p>

              </div>

            </div>


            <div className="capability-card">

              <div className="capability-icon">
                ↗
              </div>

              <div>

                <h3>
                  Performance
                </h3>

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

                <h3>
                  Code Quality
                </h3>

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

      <section className="workflow-section rag-pipeline-section">

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
                Provide Code
              </h3>

              <p>
                Upload a project, select source files,
                or paste a single file.
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
                Code is loaded, chunked, and converted
                into semantic embeddings.
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
                RAG retrieves relevant code context
                for the review question.
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
                from the retrieved code.
              </p>

            </div>

          </div>

        </div>

      </section>


      {/* =====================================================
          TECHNICAL ARCHITECTURE
          ===================================================== */}

      <section className="rag-pipeline-section">

        <div className="container">

          <div className="workflow-heading">

            <div className="section-label">
              RAG PIPELINE
            </div>

            <h2>
              Analysis grounded in
              <span> your code.</span>
            </h2>

          </div>


          <div className="workflow-grid">

            <div className="workflow-step">

              <div className="workflow-number">
                01
              </div>

              <h3>
                Chunk
              </h3>

              <p>
                Source code is divided into meaningful
                sections for retrieval.
              </p>

            </div>


            <div className="workflow-line"></div>


            <div className="workflow-step">

              <div className="workflow-number">
                02
              </div>

              <h3>
                Embed
              </h3>

              <p>
                Sentence Transformers convert code
                into semantic vector representations.
              </p>

            </div>


            <div className="workflow-line"></div>


            <div className="workflow-step">

              <div className="workflow-number">
                03
              </div>

              <h3>
                Search
              </h3>

              <p>
                FAISS finds relevant code based on
                the review question.
              </p>

            </div>


            <div className="workflow-line"></div>


            <div className="workflow-step">

              <div className="workflow-number">
                04
              </div>

              <h3>
                Generate
              </h3>

              <p>
                Groq analyzes the retrieved context
                and returns a structured review.
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