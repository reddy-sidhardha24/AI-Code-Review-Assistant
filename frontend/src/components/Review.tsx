import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
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

interface CorrectedCodeItem {
  file_name: string;
  code: string;
}

interface CommonFinding {
  title: string;
  category?: string;
  type?: string;
  severity?: string;
  file?: string;
  line?: number | null;
  line_range?: string | null;
  evidence?: string;
  description?: string;
  explanation?: string;
  impact?: string;
  fix?: string;
  suggestion?: string;
  suggested_solution?: string;
  before_code?: string;
  after_code?: string;
  corrected_code?: string;
  reason_for_correction?: string;
  confidence?: number;
}

interface PerformanceInfo {
  time_complexity: string;
  space_complexity: string;
  issues: CommonFinding[];
}

interface SecurityInfo {
  issues_found: number;
  issues: CommonFinding[];
}

interface CodeQualityInfo {
  observations: CommonFinding[];
  suggestions: CommonFinding[];
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
  bugs: CommonFinding[];
  errors: CommonFinding[];
  performance?: PerformanceInfo | null;
  security?: SecurityInfo | null;
  code_quality?: CodeQualityInfo | null;
  detected_issues?: CommonFinding[];
  corrected_code?: CorrectedCodeItem[];
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
   ISSUE SOLUTION & CODE CORRECTION CARD COMPONENT
   ============================================================ */

function IssueSolutionCard({
  issue,
  categoryBadge
}: {
  issue: CommonFinding;
  categoryBadge: string;
}) {
  const [copied, setCopied] = useState(false);
  const severity = (issue.severity || "medium").toLowerCase();
  const title = issue.title || "Detected Issue";
  const explanation = issue.explanation || issue.description || "No specific explanation provided.";
  const solution =
    issue.suggested_solution ||
    issue.fix ||
    issue.suggestion ||
    "Follow recommended architectural and security practices to resolve this issue.";
  const beforeCode = issue.before_code || issue.evidence;
  const afterCode =
    issue.after_code ||
    issue.corrected_code ||
    (issue.fix && issue.fix.includes("\n") ? issue.fix : null);
  const reason = issue.reason_for_correction;

  const handleCopy = (codeText: string) => {
    navigator.clipboard.writeText(codeText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <article className="finding-card issue-solution-card">
      {/* 1. Problem Identification & 4. Severity */}
      <div className="finding-top">
        <div className="issue-title-group">
          <span className="issue-category-tag">{categoryBadge}</span>
          <h4 className="issue-title-text">{title}</h4>
        </div>

        <span className={`severity-badge ${getSeverityClass(severity)}`}>
          {severity.toUpperCase()}
        </span>
      </div>

      {/* 2. File & Line Number */}
      <div className="finding-meta" style={{ marginTop: "8px", display: "flex", flexWrap: "wrap", gap: "10px", alignItems: "center" }}>
        <span style={{ fontWeight: 600 }}>📍 Location:</span>
        <span>📄 {issue.file || "source code"}</span>
        {issue.line != null && <span style={{ background: "rgba(255,255,255,0.06)", padding: "2px 8px", borderRadius: "4px" }}>Line {issue.line}</span>}
        {issue.line_range && <span style={{ background: "rgba(255,255,255,0.06)", padding: "2px 8px", borderRadius: "4px" }}>Lines {issue.line_range}</span>}
        {issue.confidence && <span style={{ color: "var(--success)" }}>✓ {issue.confidence}% confidence</span>}
      </div>

      {/* 3. Explanation */}
      <div className="issue-explanation-block">
        <strong className="block-label">📖 Problem & Explanation</strong>
        <p className="finding-description">{explanation}</p>
      </div>

      {/* 5. Suggested Solution */}
      {solution && (
        <div className="issue-solution-block">
          <strong className="block-label">💡 Suggested Solution</strong>
          <p>{solution}</p>
        </div>
      )}

      {/* 6 & 7. Before and After Code Comparison */}
      {(beforeCode || afterCode) && (
        <div style={{ marginTop: "16px" }}>
          <strong className="block-label" style={{ marginBottom: "8px" }}>🔄 Before & After Code Comparison</strong>
          <div className="code-comparison-container">
            {beforeCode && (
              <div className="code-compare-col before-col">
                <div className="code-compare-header">
                  <span className="compare-tag tag-before">❌ Before (Problematic Code)</span>
                </div>
                <pre className="compare-pre before-pre">
                  <code>{beforeCode}</code>
                </pre>
              </div>
            )}

            {afterCode && (
              <div className="code-compare-col after-col">
                <div className="code-compare-header">
                  <span className="compare-tag tag-after">✅ After (Corrected Code)</span>
                  <button
                    type="button"
                    className="btn-copy-code"
                    onClick={() => handleCopy(afterCode)}
                  >
                    {copied ? "✓ Copied!" : "📋 Copy Code"}
                  </button>
                </div>
                <pre className="compare-pre after-pre">
                  <code>{afterCode}</code>
                </pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 8. Reason for Correction */}
      {reason && (
        <div className="reason-callout-box">
          <div className="reason-callout-title">
            <span>🛡️ Reason for Correction</span>
          </div>
          <p className="reason-callout-text">{reason}</p>
        </div>
      )}

      {issue.impact && (
        <div className="finding-text" style={{ marginTop: "0.75rem", fontSize: "12px", color: "var(--text-muted)" }}>
          <strong>Impact:</strong> {issue.impact}
        </div>
      )}
    </article>
  );
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

  const [inputType, setInputType] =
    useState<"zip" | "source_file" | "pasted_code">(() => {
      const saved = localStorage.getItem("project_input_type");
      if (saved === "pasted_code" || saved === "source_file" || saved === "zip") {
        return saved;
      }
      return "zip";
    });

  useEffect(() => {
    API.get("/project-info")
      .then((res) => {
        const bType = res.data?.input_type || res.data?.project?.input_type;
        if (bType === "pasted_code" || bType === "source_file" || bType === "zip") {
          setInputType(bType);
        }
      })
      .catch(() => {});
  }, []);

  const getDownloadButtonLabel = () => {
    switch (inputType) {
      case "zip":
        return "Download ZIP File";
      case "source_file":
        return "Download Source File";
      case "pasted_code":
        return "Download Code";
      default:
        return "Download ZIP File";
    }
  };

  const handleDownloadItem = (item: CorrectedCodeItem) => {
    if (inputType === "zip") {
      // For ZIP project, download complete analyzed project from backend
      API.get("/api/download/project", { responseType: "blob" })
        .then((res) => {
          const blob = new Blob([res.data], { type: "application/zip" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = localStorage.getItem("project_filename") || "project.zip";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        })
        .catch(() => {
          // Fallback: download the refactored code file
          const blob = new Blob([item.code], { type: "text/plain;charset=utf-8" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = item.file_name || "refactored_code.py";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        });
    } else {
      // For source file or pasted code, download the actual file with original filename
      const blob = new Blob([item.code], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = item.file_name || (inputType === "pasted_code" ? "code.py" : "source_file.py");
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

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
          trimmedQuestion,
          response.data?.id
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
                  {review.bugs.map((bug, index) => (
                    <IssueSolutionCard
                      key={`${bug.title}-${index}`}
                      issue={bug}
                      categoryBadge="Bug"
                    />
                  ))}
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
                  {review.errors.map((item, index) => (
                    <IssueSolutionCard
                      key={`${item.title}-${index}`}
                      issue={item}
                      categoryBadge="Error"
                    />
                  ))}
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
                    {review.security.issues.map((issue, index) => (
                      <IssueSolutionCard
                        key={`${issue.title}-${index}`}
                        issue={issue}
                        categoryBadge="Security"
                      />
                    ))}
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
                    {review.performance.issues.map((issue, index) => (
                      <IssueSolutionCard
                        key={`${issue.title}-${index}`}
                        issue={issue}
                        categoryBadge="Performance"
                      />
                    ))}
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


                <div className="review-findings">
                  {review.code_quality.observations?.map((item, index) => (
                    <IssueSolutionCard
                      key={`obs-${index}`}
                      issue={item}
                      categoryBadge="Quality Observation"
                    />
                  ))}
                  {review.code_quality.suggestions?.map((item, index) => (
                    <IssueSolutionCard
                      key={`sug-${index}`}
                      issue={item}
                      categoryBadge="Quality Suggestion"
                    />
                  ))}
                </div>

              </section>

            )}

            {/* ================================================
                COMPLETE CORRECTED CODE
                ================================================ */}

            {review.corrected_code && review.corrected_code.length > 0 && (

              <section className="review-detail-section">

                <div className="review-detail-heading">

                  <div>

                    <span className="detail-icon success">
                      ✓
                    </span>

                    <div>

                      <h3>
                        Complete Refactored Code
                      </h3>

                      <p>
                        Full production-ready files with all corrections applied.
                      </p>

                    </div>

                  </div>

                  <strong>
                    {review.corrected_code.length} File{review.corrected_code.length !== 1 ? "s" : ""}
                  </strong>

                </div>

                <div className="corrected-code-list">
                  {review.corrected_code.map((item, idx) => (
                    <div key={idx} className="code-diff-card" style={{ marginBottom: "1.5rem" }}>
                      <div className="code-diff-header">
                        <span>📄 {item.file_name || "Refactored Code"}</span>
                        <div className="code-header-actions">
                          <button
                            type="button"
                            className="btn-copy-code"
                            onClick={() => {
                              navigator.clipboard.writeText(item.code);
                              alert("Copied complete refactored file to clipboard!");
                            }}
                          >
                            📋 Copy Full File
                          </button>
                          <button
                            type="button"
                            className="btn-download-action"
                            onClick={() => handleDownloadItem(item)}
                            title={`Click to ${getDownloadButtonLabel()}`}
                          >
                            ⬇️ {getDownloadButtonLabel()}
                          </button>
                          <Link to="/final-output" className="btn-view-final-output">
                            🚀 Final Output →
                          </Link>
                        </div>
                      </div>
                      <pre className="code-pre">
                        <code>{item.code}</code>
                      </pre>
                    </div>
                  ))}
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
                PROCEED TO FINAL OUTPUT BANNER
                ================================================ */}
            <section className="review-final-output-banner">
              <div className="final-output-banner-content">
                <h3>🚀 Review Finished — Proceed to Final Output</h3>
                <p>
                  Download the complete analyzed project, inspected source files, or verified refactored code matching your input type.
                </p>
              </div>
              <Link to="/final-output" className="btn-dynamic-main-download" style={{ textDecoration: "none" }}>
                <span>📦</span>
                <span>Open Final Output Page →</span>
              </Link>
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