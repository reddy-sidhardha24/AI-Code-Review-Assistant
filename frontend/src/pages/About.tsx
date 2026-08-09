import { useNavigate } from "react-router-dom";

function About() {
  const navigate = useNavigate();

  return (
    <main className="about-page-modern">

      <div className="container">

        {/* ==================================================
            HERO
            ================================================== */}

        <section className="about-hero">

          <div className="section-label">
            ABOUT THE PROJECT
          </div>

          <h1>
            AI-powered
            <span> code review.</span>
          </h1>

          <p>
            CodeReview AI analyzes your source code using
            Retrieval-Augmented Generation to provide
            contextual feedback on bugs, security,
            performance, and code quality.
          </p>

          <div className="about-hero-actions">

            <button
              className="about-primary-button"
              onClick={() =>
                navigate("/review")
              }
            >
              Start a Review
              <span>→</span>
            </button>

            <button
              className="about-secondary-button"
              onClick={() =>
                navigate("/dashboard")
              }
            >
              View Dashboard
            </button>

          </div>

        </section>


        {/* ==================================================
            WHAT IT DOES
            ================================================== */}

        <section className="about-section">

          <div className="about-section-heading">

            <div className="section-label">
              WHAT IT DOES
            </div>

            <h2>
              From source code to
              <span> actionable insights.</span>
            </h2>

            <p>
              The system combines code retrieval,
              embeddings, vector search, and generative AI
              to understand the relevant parts of a project
              before producing a review.
            </p>

          </div>


          <div className="about-feature-grid">

            <article className="about-feature-card">

              <div className="about-feature-number">
                01
              </div>

              <div className="about-feature-icon">
                ↑
              </div>

              <h3>
                Index
              </h3>

              <p>
                Source files are loaded, processed into
                meaningful chunks, embedded, and stored in
                the vector database.
              </p>

            </article>


            <article className="about-feature-card">

              <div className="about-feature-number">
                02
              </div>

              <div className="about-feature-icon">
                ⌕
              </div>

              <h3>
                Retrieve
              </h3>

              <p>
                The system identifies code relevant to the
                user's question instead of blindly sending
                the entire project to the AI model.
              </p>

            </article>


            <article className="about-feature-card">

              <div className="about-feature-number">
                03
              </div>

              <div className="about-feature-icon">
                ✦
              </div>

              <h3>
                Analyze
              </h3>

              <p>
                The retrieved context is passed to the AI
                review pipeline to identify issues and
                generate structured findings.
              </p>

            </article>


            <article className="about-feature-card">

              <div className="about-feature-number">
                04
              </div>

              <div className="about-feature-icon">
                ✓
              </div>

              <h3>
                Improve
              </h3>

              <p>
                Findings are presented with evidence,
                impact, severity, and recommended fixes
                that developers can act on.
              </p>

            </article>

          </div>

        </section>


        {/* ==================================================
            RAG ARCHITECTURE
            ================================================== */}

        <section className="about-architecture">

          <div className="about-section-heading">

            <div className="section-label">
              RAG PIPELINE
            </div>

            <h2>
              How the analysis
              <span> works.</span>
            </h2>

          </div>


          <div className="about-pipeline">

            <div className="pipeline-step">

              <span className="pipeline-index">
                01
              </span>

              <strong>
                Project
              </strong>

              <small>
                ZIP / source files
              </small>

            </div>


            <span className="pipeline-arrow">
              →
            </span>


            <div className="pipeline-step">

              <span className="pipeline-index">
                02
              </span>

              <strong>
                Chunking
              </strong>

              <small>
                Meaningful code sections
              </small>

            </div>


            <span className="pipeline-arrow">
              →
            </span>


            <div className="pipeline-step">

              <span className="pipeline-index">
                03
              </span>

              <strong>
                Embeddings
              </strong>

              <small>
                Semantic representations
              </small>

            </div>


            <span className="pipeline-arrow">
              →
            </span>


            <div className="pipeline-step">

              <span className="pipeline-index">
                04
              </span>

              <strong>
                Vector Search
              </strong>

              <small>
                Relevant code retrieval
              </small>

            </div>


            <span className="pipeline-arrow">
              →
            </span>


            <div className="pipeline-step">

              <span className="pipeline-index">
                05
              </span>

              <strong>
                AI Review
              </strong>

              <small>
                Structured analysis
              </small>

            </div>

          </div>

        </section>


        {/* ==================================================
            REVIEW AREAS
            ================================================== */}

        <section className="about-section">

          <div className="about-section-heading">

            <div className="section-label">
              ANALYSIS AREAS
            </div>

            <h2>
              What the reviewer
              <span> checks.</span>
            </h2>

          </div>


          <div className="about-analysis-grid">

            <div className="about-analysis-item">

              <span className="analysis-icon danger">
                !
              </span>

              <div>

                <h3>
                  Bugs
                </h3>

                <p>
                  Detect runtime errors, logic problems,
                  and potentially failing code paths.
                </p>

              </div>

            </div>


            <div className="about-analysis-item">

              <span className="analysis-icon warning">
                !
              </span>

              <div>

                <h3>
                  Security
                </h3>

                <p>
                  Identify security risks such as
                  hardcoded credentials and unsafe patterns.
                </p>

              </div>

            </div>


            <div className="about-analysis-item">

              <span className="analysis-icon info">
                ↗
              </span>

              <div>

                <h3>
                  Performance
                </h3>

                <p>
                  Analyze algorithmic complexity and
                  potential performance bottlenecks.
                </p>

              </div>

            </div>


            <div className="about-analysis-item">

              <span className="analysis-icon purple">
                ✦
              </span>

              <div>

                <h3>
                  Code Quality
                </h3>

                <p>
                  Review readability, maintainability,
                  structure, and improvement opportunities.
                </p>

              </div>

            </div>

          </div>

        </section>


        {/* ==================================================
            TECHNOLOGY STACK
            ================================================== */}

        <section className="about-stack">

          <div className="about-section-heading">

            <div className="section-label">
              TECHNOLOGY
            </div>

            <h2>
              Built with a modern
              <span> AI stack.</span>
            </h2>

          </div>


          <div className="about-stack-grid">

            <div className="stack-card">

              <span>
                FRONTEND
              </span>

              <strong>
                React + TypeScript
              </strong>

              <p>
                Responsive interface for project upload,
                reviews, dashboard, and history.
              </p>

            </div>


            <div className="stack-card">

              <span>
                BACKEND
              </span>

              <strong>
                FastAPI + Python
              </strong>

              <p>
                Handles project processing, RAG retrieval,
                review requests, and API responses.
              </p>

            </div>


            <div className="stack-card">

              <span>
                EMBEDDINGS
              </span>

              <strong>
                Sentence Transformers
              </strong>

              <p>
                Converts code chunks into semantic vector
                representations for retrieval.
              </p>

            </div>


            <div className="stack-card">

              <span>
                VECTOR DATABASE
              </span>

              <strong>
                FAISS
              </strong>

              <p>
                Performs similarity search over indexed
                project code.
              </p>

            </div>


            <div className="stack-card">

              <span>
                GENERATIVE AI
              </span>

              <strong>
                Groq / LLM
              </strong>

              <p>
                Generates the contextual code review using
                retrieved project information.
              </p>

            </div>


            <div className="stack-card">

              <span>
                ARCHITECTURE
              </span>

              <strong>
                Retrieval-Augmented Generation
              </strong>

              <p>
                Combines retrieval with generation so the
                model reviews relevant project context.
              </p>

            </div>

          </div>

        </section>


        {/* ==================================================
            DEMO CTA
            ================================================== */}

        <section className="about-cta">

          <div>

            <div className="section-label">
              READY TO TEST?
            </div>

            <h2>
              Analyze your project.
            </h2>

            <p>
              Upload your code, ask a question, and see
              the AI-generated review.
            </p>

          </div>


          <button
            onClick={() =>
              navigate("/review")
            }
          >
            Open Code Review
            <span>→</span>
          </button>

        </section>

      </div>

    </main>
  );
}

export default About;