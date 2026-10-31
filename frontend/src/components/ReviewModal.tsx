import React, { useState } from "react";
import API from "../api";
import CodeDiffPreview from "./CodeDiffPreview";

const getDownloadErrorMessage = async (error: any, fallback: string): Promise<string> => {
  const responseData = error?.response?.data;
  if (responseData instanceof Blob) {
    try {
      const parsed = JSON.parse(await responseData.text());
      if (parsed?.detail) return String(parsed.detail);
    } catch {
      // Keep the generic message when the server response is not JSON.
    }
  }
  return responseData?.detail || fallback;
};

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
  const [activeTab, setActiveTab] = useState<"summary" | "bugs" | "security" | "performance" | "quality" | "code" | "fixes">("summary");
  const [isFullscreen, setIsFullscreen] = useState(false);

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
  const codeFixIssues = [
    ...allBugs,
    ...security,
    ...performance,
    ...observations,
    ...(Array.isArray(review.detected_issues) ? review.detected_issues : [])
  ];
  const hasProposedFixes = correctedCode.some((item: any) =>
    typeof (item?.code || item?.content) === "string" && (item.code || item.content).trim()
  ) || codeFixIssues.some((issue: any) =>
    [issue?.after_code, issue?.corrected_code, issue?.suggested_solution].some(
      (value) => typeof value === "string" && value.trim()
    )
  );
  const reviewWithProject = {
    ...review,
    project: {
      ...(review.project || {}),
      name: review.project?.name || review.project_name || reviewData.projectName || ""
    }
  };

  const score = reviewData.score ?? review.score ?? null;
  const confidence = reviewData.confidence ?? review.confidence ?? 90;

  const [downloading, setDownloading] = useState<string | null>(null);

  const downloadReport = async (fmt: "pdf" | "markdown" | "html") => {
    setDownloading(fmt);
    try {
      const res = await API.post("/api/download-report", {
        format: fmt,
        category: "full_review",
        review_data: review
      }, { responseType: "blob" });
      const ext = fmt === "pdf" ? "pdf" : fmt === "html" ? "html" : "md";
      const blob = new Blob([res.data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${reviewData.projectName || "Code_Review"}_Audit_Report.${ext}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Report download error:", e);
      if (fmt === "markdown") {
        const md = `# Review Report — ${reviewData.projectName || "Code Review"}\n\n**Date:** ${new Date(reviewData.createdAt || Date.now()).toLocaleString()}\n**Score:** ${score !== null ? `${score}/100` : "N/A"}\n\n## Executive Summary\n${review.answer_summary || "Review completed."}\n\n## Final Verdict\n${review.final_verdict || "No verdict."}`;
        const blob = new Blob([md], { type: "text/markdown" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Review_Report_${reviewData.id || "export"}.md`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        alert(`Failed to generate ${fmt.toUpperCase()} report download.`);
      }
    } finally {
      setDownloading(null);
    }
  };

  const downloadFullProjectZip = async () => {
    setDownloading("full-zip");
    try {
      const res = await API.post("/api/download-corrected-project", {
        project_name: reviewData.projectName || reviewData.project_name || (review.project && review.project.name),
        review_data: review
      }, { responseType: "blob" });
      const blob = new Blob([res.data], { type: "application/zip" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${reviewData.projectName || "Project"}_Corrected_Full.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Full ZIP download error:", e);
      alert(await getDownloadErrorMessage(e, "Failed to package full project archive."));
    } finally {
      setDownloading(null);
    }
  };

  const downloadPatchedFilesZip = async () => {
    setDownloading("patch-zip");
    try {
      const res = await API.post("/api/download-corrected-files", {
        project_name: reviewData.projectName || reviewData.project_name || (review.project && review.project.name),
        review_data: review
      }, { responseType: "blob" });
      const blob = new Blob([res.data], { type: "application/zip" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${reviewData.projectName || "Project"}_Corrected_Files_Only.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Patched ZIP download error:", e);
      alert("Failed to package patched files archive.");
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="review-modal-backdrop" onClick={onClose}>
      <div
        className={`review-modal-container ${isFullscreen ? "fullscreen-modal" : ""}`}
        style={isFullscreen ? { width: "96vw", maxWidth: "96vw", height: "94vh", maxHeight: "94vh" } : undefined}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="review-modal-header">
          <div className="modal-title-group">
            <span className="modal-badge">Past Review Audit</span>
            <h2 className="modal-title">{reviewData.projectName || reviewData.project_name || "Code Review Details"}</h2>
            <div className="modal-meta">
              <span>📅 {new Date(reviewData.createdAt || reviewData.created_at || Date.now()).toLocaleString()}</span>
              <span>•</span>
              <span>💻 {reviewData.language || "Multi-language"}</span>
              <span>•</span>
              <span>Confidence: {confidence}%</span>
              <span>•</span>
              <span className={`modal-agent-badge ${(review.agent_mode || reviewData.agent_mode) === "multi" ? "multi" : "single"}`}>
                {(review.agent_mode || reviewData.agent_mode) === "multi" ? "🤖 Multi-Agent Ensemble" : "⚡ Single-Agent"}
              </span>
              {(review.audited_by?.name || reviewData.audited_by?.name) && (
                <>
                  <span>•</span>
                  <span className="modal-auditor-badge">👤 {review.audited_by?.name || reviewData.audited_by?.name}</span>
                </>
              )}
            </div>
          </div>

          <div className="modal-header-actions">
            <button
              type="button"
              className="btn-modal-fullscreen"
              onClick={() => setIsFullscreen(!isFullscreen)}
              title={isFullscreen ? "Restore standard size" : "Expand report to fullscreen"}
              style={{
                background: "var(--bg-subtle, rgba(255,255,255,0.06))",
                border: "1px solid var(--border, rgba(255,255,255,0.15))",
                color: "var(--text-main, #e2e8f0)",
                borderRadius: "8px",
                padding: "6px 14px",
                fontSize: "0.85rem",
                fontWeight: 500,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px"
              }}
            >
              {isFullscreen ? "🗗 Standard View" : "⛶ Fullscreen"}
            </button>
            {score !== null && (
              <div className={`score-badge ${score >= 80 ? "score-high" : score >= 60 ? "score-mid" : "score-low"}`}>
                <span className="score-val">{score}</span>
                <span className="score-max">/100</span>
              </div>
            )}
            <button
              className="modal-close-btn"
              onClick={onClose}
              aria-label="Close modal"
              style={{
                borderRadius: "50%",
                width: "34px",
                height: "34px",
                minWidth: "34px",
                minHeight: "34px",
                maxWidth: "34px",
                maxHeight: "34px",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                padding: 0,
                lineHeight: 1
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Question prompt */}
        {reviewData.question && (
          <div className="modal-question-box">
            <span className="question-label">Review Prompt:</span>
            <span className="question-text">"{reviewData.question}"</span>
          </div>
        )}

        {/* Modal Navigation Tabs */}
        <div className="modal-tabs">
          <button
            type="button"
            className={`modal-tab ${activeTab === "summary" ? "active" : ""}`}
            onClick={() => setActiveTab("summary")}
          >
            <span className="modal-tab-icon">📊</span>
            <span className="modal-tab-label">Overview</span>
          </button>
          <button
            type="button"
            className={`modal-tab ${activeTab === "bugs" ? "active" : ""}`}
            onClick={() => setActiveTab("bugs")}
          >
            <span className="modal-tab-icon">🐛</span>
            <span className="modal-tab-label">Bugs & Errors</span>
            <span className="modal-tab-count">{allBugs.length}</span>
          </button>
          <button
            type="button"
            className={`modal-tab ${activeTab === "security" ? "active" : ""}`}
            onClick={() => setActiveTab("security")}
          >
            <span className="modal-tab-icon">🛡️</span>
            <span className="modal-tab-label">Security</span>
            <span className="modal-tab-count">{security.length}</span>
          </button>
          <button
            type="button"
            className={`modal-tab ${activeTab === "performance" ? "active" : ""}`}
            onClick={() => setActiveTab("performance")}
          >
            <span className="modal-tab-icon">⚡</span>
            <span className="modal-tab-label">Performance</span>
            <span className="modal-tab-count">{performance.length}</span>
          </button>
          <button
            type="button"
            className={`modal-tab ${activeTab === "quality" ? "active" : ""}`}
            onClick={() => setActiveTab("quality")}
          >
            <span className="modal-tab-icon">✨</span>
            <span className="modal-tab-label">Quality</span>
            <span className="modal-tab-count">{observations.length + suggestions.length}</span>
          </button>
          {correctedCode.length > 0 && (
            <button
              type="button"
              className={`modal-tab ${activeTab === "code" ? "active" : ""}`}
              onClick={() => setActiveTab("code")}
            >
              <span className="modal-tab-icon">💻</span>
              <span className="modal-tab-label">Corrected Code</span>
              <span className="modal-tab-count">{correctedCode.length}</span>
            </button>
          )}
          <button
            type="button"
            className={`modal-tab ${activeTab === "fixes" ? "active" : ""}`}
            onClick={() => setActiveTab("fixes")}
          >
            <span className="modal-tab-icon">🛠️</span>
            <span className="modal-tab-label">Fixes & Pull Request</span>
          </button>
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
                <div className="stat-mini-card bug-stat">
                  <span className="stat-icon">🐛</span>
                  <div className="stat-meta">
                    <span className="stat-num red">{allBugs.length}</span>
                    <span className="stat-lbl">Bugs & Errors</span>
                  </div>
                </div>
                <div className="stat-mini-card security-stat">
                  <span className="stat-icon">🛡️</span>
                  <div className="stat-meta">
                    <span className="stat-num amber">{security.length}</span>
                    <span className="stat-lbl">Security Alerts</span>
                  </div>
                </div>
                <div className="stat-mini-card perf-stat">
                  <span className="stat-icon">⚡</span>
                  <div className="stat-meta">
                    <span className="stat-num blue">{performance.length}</span>
                    <span className="stat-lbl">Performance Bottlenecks</span>
                  </div>
                </div>
                <div className="stat-mini-card quality-stat">
                  <span className="stat-icon">✨</span>
                  <div className="stat-meta">
                    <span className="stat-num green">{observations.length + suggestions.length}</span>
                    <span className="stat-lbl">Quality Insights</span>
                  </div>
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

              {/* DEDICATED DOWNLOAD & EXPORT SECTION */}
              <div className="modal-export-card">
                <h4 className="modal-export-title">
                  📥 Download Reports & Remediation Archives
                </h4>
                <p className="modal-export-description">
                  Export this audit in your preferred industry format or download corrected code archives:
                </p>
                <div className="modal-export-actions">
                  <button
                    type="button"
                    onClick={() => downloadReport("pdf")}
                    disabled={downloading !== null}
                    className="btn-toolbar modal-export-button"
                  >
                    {downloading === "pdf" ? "⏳ Generating..." : "📄 PDF Report"}
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadReport("markdown")}
                    disabled={downloading !== null}
                    className="btn-toolbar modal-export-button"
                  >
                    {downloading === "markdown" ? "⏳ Generating..." : "📝 Markdown (.md)"}
                  </button>
                  <button
                    type="button"
                    onClick={() => downloadReport("html")}
                    disabled={downloading !== null}
                    className="btn-toolbar modal-export-button"
                  >
                    {downloading === "html" ? "⏳ Generating..." : "🌐 Standalone HTML"}
                  </button>
                  <button
                    type="button"
                    onClick={downloadFullProjectZip}
                    disabled={downloading !== null}
                    className="btn-toolbar modal-export-button"
                  >
                    {downloading === "full-zip" ? "⏳ Packaging..." : "📦 Full Corrected Project ZIP"}
                  </button>
                  <button
                    type="button"
                    onClick={downloadPatchedFilesZip}
                    disabled={downloading !== null}
                    className="btn-toolbar modal-export-button"
                  >
                    {downloading === "patch-zip" ? "⏳ Packaging..." : "📁 Corrected Files Only ZIP"}
                  </button>
                </div>
              </div>
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

          {activeTab === "fixes" && (
            <div className="tab-pane history-fixes-pane">
              {hasProposedFixes ? (
                <CodeDiffPreview review={reviewWithProject} />
              ) : (
                <div className="empty-findings">
                  No proposed code fixes were saved with this review.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="review-modal-footer">
          <div className="modal-quick-downloads">
            <span className="quick-downloads-label">
              Quick Downloads:
            </span>
            <button
              type="button"
              className="btn-toolbar"
              onClick={() => downloadReport("pdf")}
              disabled={downloading !== null}
              title="Download high-resolution printable PDF report"
            >
              {downloading === "pdf" ? "⏳ Generating..." : "📄 PDF"}
            </button>
            <button
              type="button"
              className="btn-toolbar"
              onClick={() => downloadReport("markdown")}
              disabled={downloading !== null}
              title="Download Markdown report"
            >
              {downloading === "markdown" ? "⏳ Generating..." : "📝 Markdown"}
            </button>
            <button
              type="button"
              className="btn-toolbar"
              onClick={() => downloadReport("html")}
              disabled={downloading !== null}
              title="Download standalone HTML report"
            >
              {downloading === "html" ? "⏳ Generating..." : "🌐 HTML"}
            </button>
            <button
              type="button"
              className="btn-toolbar"
              onClick={downloadFullProjectZip}
              disabled={downloading !== null}
              title="Download entire project codebase with fixes applied"
            >
              {downloading === "full-zip" ? "⏳ Packaging..." : "📦 Full ZIP"}
            </button>
            <button
              type="button"
              className="btn-toolbar"
              onClick={downloadPatchedFilesZip}
              disabled={downloading !== null}
              title="Download modified and corrected files only"
            >
              {downloading === "patch-zip" ? "⏳ Packaging..." : "📁 Patched ZIP"}
            </button>
          </div>
          <button className="btn-secondary" onClick={onClose}>Close Window</button>
        </div>
      </div>
    </div>
  );
};

export default ReviewModal;
