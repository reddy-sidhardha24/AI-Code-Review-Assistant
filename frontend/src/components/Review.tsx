import { useState } from "react";
import API from "../api";
import { saveReviewToHistory } from "../utils/reviewHistory";

/* ============================================================
   TYPES
   ============================================================ */

interface FileAnalyzed {
  file_name: string;
  path: string;
  language: string;
}

interface BugFinding {
  title: string;
  type: string;
  severity: string;
  file: string;
  line?: number | null;
  line_range?: string | null;
  evidence: string;
  description: string;
  impact: string;
  fix: string;
  confidence: number;
}

interface ErrorFinding {
  type: string;
  title: string;
  file: string;
  line?: number | null;
  line_range?: string | null;
  evidence: string;
  description: string;
  impact: string;
  fix: string;
  confidence: number;
}

interface PerformanceIssue {
  title: string;
  description: string;
  file?: string;
  line?: number | null;
  line_range?: string | null;
  evidence?: string;
  impact?: string;
  suggestion?: string;
  confidence?: number;
}

interface PerformanceInfo {
  time_complexity: string;
  space_complexity: string;
  issues: PerformanceIssue[];
}

interface SecurityIssue {
  title: string;
  description: string;
}

interface SecurityInfo {
  issues_found: number;
  issues: SecurityIssue[];
}

interface CodeQualityFinding {
  type?: string;
  title?: string;
  description: string;
}

interface CodeQualityInfo {
  observations: CodeQualityFinding[];
  suggestions: CodeQualityFinding[];
}

interface ProjectInfo {
  name?: string | null;
  languages: string[];
  total_files: number;
  total_lines: number;
}

interface ReviewData {
  project: ProjectInfo;

  question: string;

  review_types: string[];

  answer_summary: string;

  files_analyzed: FileAnalyzed[];

  bugs: BugFinding[];

  errors: ErrorFinding[];

  performance?: PerformanceInfo | null;

  security?: SecurityInfo | null;

  code_quality?: CodeQualityInfo | null;

  key_methods: string[];

  key_classes: string[];

  libraries: string[];

  expected_output?: string | null;

  score?: number | null;

  confidence: number;

  final_verdict: string;
}

/* ============================================================
   HELPERS
   ============================================================ */

function getSeverityClass(
  severity: string
): string {
  const value = severity.toLowerCase();

  if (value === "critical") {
    return "severity-critical";
  }

  if (value === "high") {
    return "severity-high";
  }

  if (value === "medium") {
    return "severity-medium";
  }

  return "severity-low";
}

function formatReviewType(
  value: string
): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase()
    );
}

function getLanguageLabel(
  languages: string[]
): string {
  if (!languages || languages.length === 0) {
    return "Unknown";
  }

  return languages.join(", ");
}

function safeCount(
  value?: unknown
): number {
  return Array.isArray(value)
    ? value.length
    : 0;
}

/* ============================================================
   REVIEW COMPONENT
   ============================================================ */

function Review() {
  const [question, setQuestion] =
    useState("");

  const [review, setReview] =
    useState<ReviewData | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  /* ==========================================================
     ASK QUESTION
     ========================================================== */

  const askQuestion = async () => {
    const trimmedQuestion =
      question.trim();

    if (!trimmedQuestion) {
      setError(
        "Please enter a review question."
      );
      return;
    }

    setLoading(true);
    setReview(null);
    setError("");

    try {
      const response = await API.post(
        "/review",
        {
          question:
            trimmedQuestion,
        }
      );

      if (
        response.data?.success &&
        response.data?.review
      ) {
        const reviewData =
          response.data.review as ReviewData;

        setReview(reviewData);

        saveReviewToHistory(
          reviewData,
          trimmedQuestion
        );
      } else {
        setError(
          "The backend did not return a valid review."
        );
      }
    } catch (err: any) {
      console.error(
        "Review request failed:",
        err
      );

      const backendError =
        err.response?.data?.detail;

      if (backendError) {
        setError(
          typeof backendError === "string"
            ? backendError
            : "The review request failed."
        );
      } else if (
        err.response?.status === 502
      ) {
        setError(
          "The AI review response could not be validated by the backend."
        );
      } else {
        setError(
          "Unable to connect to the backend."
        );
      }
    } finally {
      setLoading(false);
    }
  };

  /* ==========================================================
     KEYBOARD
     ========================================================== */

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (
      event.key === "Enter" &&
      event.ctrlKey
    ) {
      event.preventDefault();
      askQuestion();
    }
  };

  /* ==========================================================
     CLEAR REVIEW
     ========================================================== */

  const clearReview = () => {
    setReview(null);
    setError("");
    setQuestion("");
  };

  /* ==========================================================
     RENDER
     ========================================================== */

  return (
    <main className="review-modern-page">

      <div className="container">

        {/* ==================================================
            PAGE HEADER
            ================================================== */}

        <section className="review-modern-header">

          <div>

            <div className="section-label">
              AI CODE ANALYSIS
            </div>

            <h1>
              Review your code
              <span>.</span>
            </h1>

            <p>
              Ask questions about your indexed
              project and get contextual analysis
              powered by RAG and AI.
            </p>

          </div>

        </section>


        {/* ==================================================
            QUESTION PANEL
            ================================================== */}

        <section className="review-input-card">

          <div className="review-input-header">

            <div>

              <span className="review-input-label">
                WHAT WOULD YOU LIKE TO ANALYZE?
              </span>

              <h2>
                Ask your code reviewer
              </h2>

            </div>

            <div className="review-ai-badge">
              <span className="status-dot" />
              AI Ready
            </div>

          </div>


          <textarea
            className="review-question-input"
            rows={7}
            maxLength={2000}
            placeholder={
              "Example: Perform a complete project-wide review covering bugs, security, performance, and code quality."
            }
            value={question}
            disabled={loading}
            onChange={(event) =>
              setQuestion(
                event.target.value
              )
            }
            onKeyDown={handleKeyDown}
          />


          <div className="review-input-footer">

            <span className="review-character-count">
              {question.length} / 2000
            </span>

            <button
              type="button"
              className="review-analyze-button"
              onClick={askQuestion}
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="review-spinner" />
                  Analyzing...
                </>
              ) : (
                <>
                  Analyze Project
                  <span>→</span>
                </>
              )}
            </button>

          </div>


          {/* ==================================================
              QUICK PROMPTS
              ================================================== */}

          <div className="review-quick-prompts">

            <span>
              Try a review:
            </span>

            <button
              type="button"
              onClick={() =>
                setQuestion(
                  "Perform a complete project-wide review covering bugs, security, performance, and code quality."
                )
              }
              disabled={loading}
            >
              Full Project Review
            </button>

            <button
              type="button"
              onClick={() =>
                setQuestion(
                  "Find all bugs and runtime errors in the project."
                )
              }
              disabled={loading}
            >
              Find Bugs
            </button>

            <button
              type="button"
              onClick={() =>
                setQuestion(
                  "Perform a security review and identify security vulnerabilities."
                )
              }
              disabled={loading}
            >
              Security
            </button>

            <button
              type="button"
              onClick={() =>
                setQuestion(
                  "Analyze the project's performance and identify performance bottlenecks."
                )
              }
              disabled={loading}
            >
              Performance
            </button>

            <button
              type="button"
              onClick={() =>
                setQuestion(
                  "Review the code quality, readability, maintainability, and architecture."
                )
              }
              disabled={loading}
            >
              Code Quality
            </button>

          </div>

        </section>


        {/* ==================================================
            ERROR
            ================================================== */}

        {error && (

          <section className="review-error-card">

            <div className="review-error-icon">
              !
            </div>

            <div>

              <h3>
                Review failed
              </h3>

              <p>
                {error}
              </p>

            </div>

          </section>

        )}


        {/* ==================================================
            LOADING
            ================================================== */}

        {loading && (

          <section className="review-loading-card">

            <div className="review-loading-animation">

              <span />
              <span />
              <span />

            </div>

            <h3>
              Analyzing your project
            </h3>

            <p>
              Retrieving relevant code,
              evaluating findings, and
              generating the structured review.
            </p>

            <div className="review-loading-steps">

              <span>
                ✓ Retrieving code
              </span>

              <span>
                • AI analysis
              </span>

              <span>
                • Structuring results
              </span>

            </div>

          </section>

        )}


        {/* ==================================================
            REVIEW RESULT
            ================================================== */}

        {review && !loading && (

          <section className="review-result-section">

            {/* ================================================
                RESULT HEADER
                ================================================ */}

            <div className="review-result-header">

              <div>

                <div className="section-label">
                  ANALYSIS COMPLETE
                </div>

                <h2>
                  {review.project?.name ||
                    "Project Review"}
                </h2>

                <p>
                  {getLanguageLabel(
                    review.project?.languages || []
                  )}
                  {" • "}
                  {review.project?.total_files || 0}{" "}
                  files
                  {" • "}
                  {review.project?.total_lines || 0}{" "}
                  lines
                </p>

              </div>

              <button
                type="button"
                className="review-clear-button"
                onClick={clearReview}
              >
                New Review
              </button>

            </div>


            {/* ================================================
                REVIEW TYPES
                ================================================ */}

            {review.review_types?.length > 0 && (

              <div className="review-type-list">

                {review.review_types.map(
                  (type) => (
                    <span
                      key={type}
                      className="review-type-badge"
                    >
                      {formatReviewType(type)}
                    </span>
                  )
                )}

              </div>

            )}


            {/* ================================================
                SUMMARY
                ================================================ */}

            <section className="review-summary-card">

              <div className="review-summary-icon">
                ✦
              </div>

              <div>

                <span>
                  AI SUMMARY
                </span>

                <p>
                  {review.answer_summary ||
                    "The review completed successfully. See the findings below for the detailed analysis."}
                </p>

              </div>

            </section>


            {/* ================================================
                STATISTICS
                ================================================ */}

            <section className="review-stat-grid">

              <div className="review-stat-card">

                <span className="review-stat-label">
                  BUGS
                </span>

                <strong className="stat-red">
                  {safeCount(review.bugs)}
                </strong>

                <small>
                  detected
                </small>

              </div>


              <div className="review-stat-card">

                <span className="review-stat-label">
                  SECURITY
                </span>

                <strong className="stat-yellow">
                  {review.security?.issues_found || 0}
                </strong>

                <small>
                  issues
                </small>

              </div>


              <div className="review-stat-card">

                <span className="review-stat-label">
                  PERFORMANCE
                </span>

                <strong className="stat-blue">
                  {safeCount(
                    review.performance?.issues
                  )}
                </strong>

                <small>
                  concerns
                </small>

              </div>


              <div className="review-stat-card">

                <span className="review-stat-label">
                  CODE QUALITY
                </span>

                <strong className="stat-purple">
                  {safeCount(
                    review.code_quality?.observations
                  ) +
                    safeCount(
                      review.code_quality?.suggestions
                    )}
                </strong>

                <small>
                  findings
                </small>

              </div>


              <div className="review-stat-card">

                <span className="review-stat-label">
                  CONFIDENCE
                </span>

                <strong className="stat-green">
                  {review.confidence || 0}%
                </strong>

                <small>
                  AI confidence
                </small>

              </div>

            </section>


            {/* ================================================
                FINAL VERDICT
                ================================================ */}

            <section className="review-verdict-card">

              <div className="review-verdict-heading">

                <span>
                  FINAL VERDICT
                </span>

                <div className="review-confidence">
                  {review.confidence || 0}%
                  confidence
                </div>

              </div>

              <p>
                {review.final_verdict ||
                  "The project review completed successfully. Review the findings above and address the highest-severity issues first."}
              </p>

            </section>


            {/* ================================================
                BUGS
                ================================================ */}

            {review.bugs?.length > 0 && (

              <section className="review-detail-section">

                <div className="review-detail-heading">

                  <div>

                    <span className="detail-icon danger">
                      !
                    </span>

                    <div>

                      <h3>
                        Bugs & Runtime Issues
                      </h3>

                      <p>
                        Confirmed and potential
                        problems detected in the
                        project.
                      </p>

                    </div>

                  </div>

                  <strong>
                    {review.bugs.length}
                  </strong>

                </div>


                <div className="review-findings">

                  {review.bugs.map(
                    (bug, index) => (

                      <article
                        className="finding-card"
                        key={`${bug.title}-${index}`}
                      >

                        <div className="finding-top">

                          <h4>
                            {bug.title}
                          </h4>

                          <span
                            className={`severity-badge ${getSeverityClass(
                              bug.severity
                            )}`}
                          >
                            {bug.severity}
                          </span>

                        </div>


                        <div className="finding-meta">

                          <span>
                            {bug.file}
                          </span>

                          {bug.line != null && (
                            <span>
                              Line {bug.line}
                            </span>
                          )}

                          {bug.line_range && (
                            <span>
                              Lines {bug.line_range}
                            </span>
                          )}

                          <span>
                            {bug.type}
                          </span>

                        </div>


                        <p className="finding-description">
                          {bug.description}
                        </p>


                        {bug.evidence && (

                          <div className="finding-block">

                            <span>
                              EVIDENCE
                            </span>

                            <code>
                              {bug.evidence}
                            </code>

                          </div>

                        )}


                        {bug.impact && (

                          <div className="finding-text">

                            <strong>
                              Impact
                            </strong>

                            <p>
                              {bug.impact}
                            </p>

                          </div>

                        )}


                        {bug.fix && (

                          <div className="finding-fix">

                            <strong>
                              Recommended Fix
                            </strong>

                            <p>
                              {bug.fix}
                            </p>

                          </div>

                        )}

                      </article>

                    )
                  )}

                </div>

              </section>

            )}


            {/* ================================================
                ERRORS
                ================================================ */}

            {review.errors?.length > 0 && (

              <section className="review-detail-section">

                <div className="review-detail-heading">

                  <div>

                    <span className="detail-icon danger">
                      !
                    </span>

                    <div>

                      <h3>
                        Errors
                      </h3>

                      <p>
                        Errors identified during
                        the analysis.
                      </p>

                    </div>

                  </div>

                  <strong>
                    {review.errors.length}
                  </strong>

                </div>


                <div className="review-findings">

                  {review.errors.map(
                    (item, index) => (

                      <article
                        className="finding-card"
                        key={`${item.title}-${index}`}
                      >

                        <div className="finding-top">

                          <h4>
                            {item.title}
                          </h4>

                          <span className="finding-type">
                            {item.type}
                          </span>

                        </div>


                        <div className="finding-meta">

                          <span>
                            {item.file}
                          </span>

                          {item.line != null && (
                            <span>
                              Line {item.line}
                            </span>
                          )}

                          {item.line_range && (
                            <span>
                              Lines {item.line_range}
                            </span>
                          )}

                        </div>


                        <p className="finding-description">
                          {item.description}
                        </p>


                        {item.evidence && (

                          <div className="finding-block">

                            <span>
                              EVIDENCE
                            </span>

                            <code>
                              {item.evidence}
                            </code>

                          </div>

                        )}


                        {item.impact && (

                          <div className="finding-text">

                            <strong>
                              Impact
                            </strong>

                            <p>
                              {item.impact}
                            </p>

                          </div>

                        )}


                        {item.fix && (

                          <div className="finding-fix">

                            <strong>
                              Recommended Fix
                            </strong>

                            <p>
                              {item.fix}
                            </p>

                          </div>

                        )}

                      </article>

                    )
                  )}

                </div>

              </section>

            )}


            {/* ================================================
                SECURITY
                ================================================ */}

            {review.security &&
              review.security.issues_found > 0 && (

                <section className="review-detail-section">

                  <div className="review-detail-heading">

                    <div>

                      <span className="detail-icon warning">
                        !
                      </span>

                      <div>

                        <h3>
                          Security
                        </h3>

                        <p>
                          Potential security risks
                          identified by the AI reviewer.
                        </p>

                      </div>

                    </div>

                    <strong>
                      {review.security.issues_found}
                    </strong>

                  </div>


                  <div className="review-findings">

                    {review.security.issues.map(
                      (issue, index) => (

                        <article
                          className="finding-card"
                          key={`${issue.title}-${index}`}
                        >

                          <div className="finding-top">

                            <h4>
                              {issue.title}
                            </h4>

                            <span className="finding-type">
                              Security
                            </span>

                          </div>


                          <p className="finding-description">
                            {issue.description}
                          </p>

                        </article>

                      )
                    )}

                  </div>

                </section>

              )}


            {/* ================================================
                PERFORMANCE
                ================================================ */}

            {review.performance && (

              <section className="review-detail-section">

                <div className="review-detail-heading">

                  <div>

                    <span className="detail-icon info">
                      ↗
                    </span>

                    <div>

                      <h3>
                        Performance
                      </h3>

                      <p>
                        Complexity and performance
                        concerns found in the project.
                      </p>

                    </div>

                  </div>

                  <strong>
                    {
                      review.performance.issues?.length || 0
                    }
                  </strong>

                </div>


                <div className="complexity-grid">

                  <div>

                    <span>
                      TIME COMPLEXITY
                    </span>

                    <strong>
                      {review.performance.time_complexity ||
                        "Not determined"}
                    </strong>

                  </div>


                  <div>

                    <span>
                      SPACE COMPLEXITY
                    </span>

                    <strong>
                      {review.performance.space_complexity ||
                        "Not determined"}
                    </strong>

                  </div>

                </div>


                {review.performance.issues?.length > 0 && (

                  <div className="review-findings">

                    {review.performance.issues.map(
                      (issue, index) => (

                        <article
                          className="finding-card"
                          key={`${issue.title}-${index}`}
                        >

                          <div className="finding-top">

                            <h4>
                              {issue.title}
                            </h4>

                            {issue.confidence !==
                              undefined && (

                              <span className="finding-type">
                                {issue.confidence}%
                              </span>

                            )}

                          </div>


                          <p className="finding-description">
                            {issue.description}
                          </p>


                          {issue.file && (

                            <div className="finding-meta">

                              <span>
                                {issue.file}
                              </span>

                              {issue.line != null && (
                                <span>
                                  Line {issue.line}
                                </span>
                              )}

                              {issue.line_range && (
                                <span>
                                  Lines {issue.line_range}
                                </span>
                              )}

                            </div>

                          )}


                          {issue.evidence && (

                            <div className="finding-block">

                              <span>
                                EVIDENCE
                              </span>

                              <code>
                                {issue.evidence}
                              </code>

                            </div>

                          )}


                          {issue.impact && (

                            <div className="finding-text">

                              <strong>
                                Impact
                              </strong>

                              <p>
                                {issue.impact}
                              </p>

                            </div>

                          )}


                          {issue.suggestion && (

                            <div className="finding-fix">

                              <strong>
                                Recommendation
                              </strong>

                              <p>
                                {issue.suggestion}
                              </p>

                            </div>

                          )}

                        </article>

                      )
                    )}

                  </div>

                )}

              </section>

            )}


            {/* ================================================
                CODE QUALITY
                ================================================ */}

            {review.code_quality && (

              <section className="review-detail-section">

                <div className="review-detail-heading">

                  <div>

                    <span className="detail-icon purple">
                      ✦
                    </span>

                    <div>

                      <h3>
                        Code Quality
                      </h3>

                      <p>
                        Readability, maintainability,
                        and structural observations.
                      </p>

                    </div>

                  </div>

                  <strong>
                    {(review.code_quality.observations?.length || 0) +
                      (review.code_quality.suggestions?.length || 0)}
                  </strong>

                </div>


                <div className="quality-grid">

                  <div className="quality-column">

                    <span className="quality-column-title">
                      OBSERVATIONS
                    </span>

                    {review.code_quality.observations?.length > 0 ? (

                      review.code_quality.observations.map(
                        (item, index) => (

                          <div
                            className="quality-item"
                            key={index}
                          >

                            <span>
                              ✓
                            </span>

                            <div>

                              <strong>
                                {item.title ||
                                  item.type ||
                                  "Observation"}
                              </strong>

                              <p>
                                {item.description}
                              </p>

                            </div>

                          </div>

                        )
                      )

                    ) : (

                      <p className="quality-empty">
                        No major observations returned.
                      </p>

                    )}

                  </div>


                  <div className="quality-column">

                    <span className="quality-column-title">
                      SUGGESTIONS
                    </span>

                    {review.code_quality.suggestions?.length > 0 ? (

                      review.code_quality.suggestions.map(
                        (item, index) => (

                          <div
                            className="quality-item"
                            key={index}
                          >

                            <span>
                              →
                            </span>

                            <div>

                              <strong>
                                {item.title ||
                                  item.type ||
                                  "Suggestion"}
                              </strong>

                              <p>
                                {item.description}
                              </p>

                            </div>

                          </div>

                        )
                      )

                    ) : (

                      <p className="quality-empty">
                        No suggestions returned.
                      </p>

                    )}

                  </div>

                </div>

              </section>

            )}


            {/* ================================================
                PROJECT DETAILS
                ================================================ */}

            <section className="review-detail-section">

              <div className="review-detail-heading">

                <div>

                  <span className="detail-icon info">
                    #
                  </span>

                  <div>

                    <h3>
                      Project Details
                    </h3>

                    <p>
                      Code elements identified during
                      the analysis.
                    </p>

                  </div>

                </div>

              </div>


              <div className="project-detail-grid">

                {/* FILES */}

                <div className="project-detail-box">

                  <span>
                    FILES ANALYZED
                  </span>

                  <strong>
                    {safeCount(
                      review.files_analyzed
                    )}
                  </strong>

                  {review.files_analyzed?.map(
                    (file, index) => (

                      <small
                        key={`${file.path}-${index}`}
                        title={file.path}
                      >
                        {file.file_name}
                      </small>

                    )
                  )}

                </div>


                {/* METHODS */}

                <div className="project-detail-box">

                  <span>
                    KEY METHODS
                  </span>

                  <strong>
                    {safeCount(
                      review.key_methods
                    )}
                  </strong>

                  {review.key_methods?.map(
                    (method, index) => (

                      <small
                        key={`${method}-${index}`}
                      >
                        {method}
                      </small>

                    )
                  )}

                </div>


                {/* CLASSES */}

                <div className="project-detail-box">

                  <span>
                    KEY CLASSES
                  </span>

                  <strong>
                    {safeCount(
                      review.key_classes
                    )}
                  </strong>

                  {review.key_classes?.map(
                    (item, index) => (

                      <small
                        key={`${item}-${index}`}
                      >
                        {item}
                      </small>

                    )
                  )}

                </div>


                {/* LIBRARIES */}

                <div className="project-detail-box">

                  <span>
                    LIBRARIES
                  </span>

                  <strong>
                    {safeCount(
                      review.libraries
                    )}
                  </strong>

                  {review.libraries?.map(
                    (library, index) => (

                      <small
                        key={`${library}-${index}`}
                      >
                        {library}
                      </small>

                    )
                  )}

                </div>

              </div>

            </section>


            {/* ================================================
                REVIEW QUESTION
                ================================================ */}

            <section className="review-question-footer">

              <span>
                REVIEW QUESTION
              </span>

              <p>
                {review.question}
              </p>

            </section>

          </section>

        )}

      </div>

    </main>
  );
}

export default Review;