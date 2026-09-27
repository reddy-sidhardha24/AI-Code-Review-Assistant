import React, { useState } from "react";

interface ReviewModalProps {
  reviewData: any;
  onClose: () => void;
}

const ModalIssueCard = ({ issue, defaultCategory }: { issue: any; defaultCategory: string }) => {
  const [copied, setCopied] = useState(false);
  const severity = (issue.severity || (defaultCategory === "security" ? "high" : "medium")).toLowerCase();
  const title = issue.title || `Issue in ${issue.file || "code"}`;
  const explanation = issue.explanation || issue.description || "";
  const solution = issue.suggested_solution || issue.fix || issue.suggestion || "";
  const beforeCode = issue.before_code || issue.evidence;
  const afterCode = issue.after_code || issue.corrected_code || (issue.fix && typeof issue.fix === "string" && issue.fix.includes("\n") ? issue.fix : null);
  const reason = issue.reason_for_correction;

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="finding-card danger-card issue-solution-modal-card" style={{ marginBottom: "1rem" }}>
      <div className="finding-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <span className="finding-type-badge danger">
            {defaultCategory.toUpperCase()}
          </span>
          <span className={`severity-badge severity-${severity}`}>
            {severity.toUpperCase()}
          </span>
        </div>
        <span className="finding-file">📄 {issue.file || "source code"} {issue.line ? `: Line ${issue.line}` : ""}</span>
      </div>

      <h4 className="finding-title" style={{ fontSize: "1.05rem", margin: "0.5rem 0" }}>{title}</h4>

      {explanation && (
        <div style={{ margin: "0.5rem 0" }}>
          <strong style={{ fontSize: "0.82rem", color: "#94a3b8" }}>Problem & Explanation:</strong>
          <p className="finding-desc" style={{ marginTop: "0.25rem" }}>{explanation}</p>
        </div>
      )}

      {solution && (
        <div className="finding-fix-box" style={{ margin: "0.5rem 0" }}>
          <strong style={{ color: "#38bdf8" }}>Suggested Solution:</strong>
          <p style={{ marginTop: "0.25rem" }}>{solution}</p>
        </div>
      )}

      {(beforeCode || afterCode) && (
        <div className="code-comparison-container" style={{ margin: "0.75rem 0" }}>
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
                  {copied ? "✓ Copied!" : "📋 Copy"}
                </button>
              </div>
              <pre className="compare-pre after-pre">
                <code>{afterCode}</code>
              </pre>
            </div>
          )}
        </div>
      )}

      {reason && (
        <div className="reason-callout-box" style={{ marginTop: "0.5rem" }}>
          <div className="reason-callout-title">
            <span>💡 Reason for Correction:</span>
          </div>
          <p className="reason-callout-text">{reason}</p>
        </div>
      )}
    </div>
  );
};

const ReviewModal: React.FC<ReviewModalProps> = ({ reviewData, onClose }) => {
  const [activeTab, setActiveTab] = useState<"summary" | "bugs" | "security" | "performance" | "quality" | "code">("summary");

  if (!reviewData) return null;

  const review = reviewData.review || {};
  const bugs = Array.isArray(review.bugs) ? review.bugs : [];
  const errors = Array.isArray(review.errors) ? review.errors : [];
  const allBugs = [...bugs, ...errors];

  const security = review.security?.issues || [];
  const performance = review.performance?.issues || [];
  const observations = review.code_quality?.observations || [];
  const suggestions = review.code_quality?.suggestions || [];
  const correctedCode = Array.isArray(review.corrected_code) ? review.corrected_code : [];

  const score = reviewData.score ?? review.score ?? null;
  const confidence = reviewData.confidence ?? review.confidence ?? 90;

  return (
    <div className="review-modal-backdrop" onClick={onClose}>
      <div className="review-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="review-modal-header">
          <div className="modal-title-group">
            <span className="modal-badge">Past Review Reopened</span>
            <h2 className="modal-title">{reviewData.projectName || reviewData.project_name || "Code Review Details"}</h2>
            <div className="modal-meta">
              <span>📅 {new Date(reviewData.createdAt || reviewData.created_at || Date.now()).toLocaleString()}</span>
              <span>•</span>
              <span>💻 {reviewData.language || "Multi-language"}</span>
              <span>•</span>
              <span>Confidence: {confidence}%</span>
            </div>
          </div>

          <div className="modal-header-actions">
            {score !== null && (
              <div className={`score-badge ${score >= 80 ? "score-high" : score >= 60 ? "score-mid" : "score-low"}`}>
                <span className="score-val">{score}</span>
                <span className="score-max">/100</span>
              </div>
            )}
            <button className="modal-close-btn" onClick={onClose}>✕</button>
          </div>
        </div>

        {/* Question prompt */}
        <div className="modal-question-box">
          <span className="question-label">Review Question:</span>
          <span className="question-text">"{reviewData.question}"</span>
        </div>

        {/* Modal Navigation Tabs */}
        <div className="modal-tabs">
          <button
            className={`modal-tab ${activeTab === "summary" ? "active" : ""}`}
            onClick={() => setActiveTab("summary")}
          >
            Overview
          </button>
          <button
            className={`modal-tab ${activeTab === "bugs" ? "active" : ""}`}
            onClick={() => setActiveTab("bugs")}
          >
            Bugs & Errors ({allBugs.length})
          </button>
          <button
            className={`modal-tab ${activeTab === "security" ? "active" : ""}`}
            onClick={() => setActiveTab("security")}
          >
            Security ({security.length})
          </button>
          <button
            className={`modal-tab ${activeTab === "performance" ? "active" : ""}`}
            onClick={() => setActiveTab("performance")}
          >
            Performance ({performance.length})
          </button>
          <button
            className={`modal-tab ${activeTab === "quality" ? "active" : ""}`}
            onClick={() => setActiveTab("quality")}
          >
            Quality ({observations.length + suggestions.length})
          </button>
          {correctedCode.length > 0 && (
            <button
              className={`modal-tab ${activeTab === "code" ? "active" : ""}`}
              onClick={() => setActiveTab("code")}
            >
              Corrected Code ({correctedCode.length})
            </button>
          )}
        </div>

        {/* Modal Body */}
        <div className="modal-body-content">
          {activeTab === "summary" && (
            <div className="tab-pane">
              <div className="summary-block">
                <h4>Executive Summary</h4>
                <p>{review.answer_summary || "No executive summary provided."}</p>
              </div>

              {review.final_verdict && (
                <div className="verdict-block">
                  <h4>Final Verdict</h4>
                  <p>{review.final_verdict}</p>
                </div>
              )}

              <div className="stats-mini-grid">
                <div className="stat-mini-card">
                  <span className="stat-num red">{allBugs.length}</span>
                  <span className="stat-lbl">Bugs / Errors</span>
                </div>
                <div className="stat-mini-card">
                  <span className="stat-num amber">{security.length}</span>
                  <span className="stat-lbl">Security Alerts</span>
                </div>
                <div className="stat-mini-card">
                  <span className="stat-num blue">{performance.length}</span>
                  <span className="stat-lbl">Performance Bottlenecks</span>
                </div>
                <div className="stat-mini-card">
                  <span className="stat-num green">{observations.length + suggestions.length}</span>
                  <span className="stat-lbl">Quality Insights</span>
                </div>
              </div>

              {review.files_analyzed && review.files_analyzed.length > 0 && (
                <div className="analyzed-files-list">
                  <h4>Files Analyzed ({review.files_analyzed.length})</h4>
                  <div className="files-pill-container">
                    {review.files_analyzed.map((f: any, idx: number) => (
                      <span key={idx} className="file-pill">
                        📄 {f.file_name || f.path || f}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === "bugs" && (
            <div className="tab-pane">
              {allBugs.length === 0 ? (
                <div className="empty-findings">🎉 No bugs or syntax errors detected in this review!</div>
              ) : (
                <div className="findings-list">
                  {allBugs.map((bug: any, idx: number) => (
                    <ModalIssueCard key={idx} issue={bug} defaultCategory="Bug" />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "security" && (
            <div className="tab-pane">
              {security.length === 0 ? (
                <div className="empty-findings">🛡️ Zero security vulnerabilities found in scanned modules!</div>
              ) : (
                <div className="findings-list">
                  {security.map((sec: any, idx: number) => (
                    <ModalIssueCard key={idx} issue={sec} defaultCategory="Security" />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "performance" && (
            <div className="tab-pane">
              {review.performance?.time_complexity && (
                <div className="complexity-banner">
                  <span>⏱️ Time: <strong>{review.performance.time_complexity}</strong></span>
                  <span>📦 Space: <strong>{review.performance.space_complexity || "O(1)"}</strong></span>
                </div>
              )}

              {performance.length === 0 ? (
                <div className="empty-findings">⚡ No major performance bottlenecks detected!</div>
              ) : (
                <div className="findings-list">
                  {performance.map((perf: any, idx: number) => (
                    <ModalIssueCard key={idx} issue={perf} defaultCategory="Performance" />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "quality" && (
            <div className="tab-pane">
              {observations.length === 0 && suggestions.length === 0 ? (
                <div className="empty-findings">✨ High code quality standards maintained throughout.</div>
              ) : (
                <div className="findings-list">
                  {observations.map((item: any, idx: number) => (
                    <ModalIssueCard key={`obs-${idx}`} issue={item} defaultCategory="Quality Observation" />
                  ))}
                  {suggestions.map((item: any, idx: number) => (
                    <ModalIssueCard key={`sug-${idx}`} issue={item} defaultCategory="Quality Suggestion" />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "code" && (
            <div className="tab-pane">
              <div className="findings-list">
                {correctedCode.map((item: any, idx: number) => (
                  <div key={idx} className="code-diff-card">
                    <div className="code-diff-header">
                      <span>📄 {item.file_name || "Refactored Code"}</span>
                    </div>
                    <pre className="code-pre">
                      <code>{item.code}</code>
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="review-modal-footer">
          <button className="btn-secondary" onClick={onClose}>Close Window</button>
        </div>
      </div>
    </div>
  );
};

export default ReviewModal;
