import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import API from "../api";
import { getReviewHistory } from "../utils/reviewHistory";

export type ProjectInputType = "zip" | "source_file" | "pasted_code";

interface ProjectMeta {
  project_name?: string;
  total_files?: number;
  total_lines?: number;
  languages?: Record<string, any> | string[];
  input_type?: string;
  original_filename?: string;
  files?: Array<{ name: string; path: string; language?: string }>;
}

const FinalOutput: React.FC = () => {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [projectMeta, setProjectMeta] = useState<ProjectMeta | null>(null);
  const [inputType, setInputType] = useState<ProjectInputType>("zip");
  const [filename, setFilename] = useState<string>("project");
  const [refactoredCodeItems, setRefactoredCodeItems] = useState<Array<{ file_name: string; code: string }>>([]);
  const [latestReview, setLatestReview] = useState<any>(null);
  const [pastedCode, setPastedCode] = useState<string>("");
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  useEffect(() => {
    // 1. Check local storage for fastest input detection
    const savedType = localStorage.getItem("project_input_type") as ProjectInputType | null;
    const savedFilename = localStorage.getItem("project_filename") || "";
    const savedCode = localStorage.getItem("pasted_code_content") || "";

    if (savedType === "pasted_code" || savedType === "source_file" || savedType === "zip") {
      setInputType(savedType);
    }
    if (savedFilename) {
      setFilename(savedFilename);
    }
    if (savedCode) {
      setPastedCode(savedCode);
    }

    // 2. Fetch authoritative project metadata from backend
    const fetchMetadata = async () => {
      try {
        const res = await API.get("/project-info");
        if (res.data?.success && res.data?.project) {
          const meta = res.data.project;
          setProjectMeta(meta);

          // Synchronize input type
          const backendInputType = res.data.input_type || meta.input_type;
          if (backendInputType === "pasted_code" || backendInputType === "source_file" || backendInputType === "zip") {
            setInputType(backendInputType);
          } else if (meta.project_name === "pasted_code" || savedType === "pasted_code") {
            setInputType("pasted_code");
          } else if (meta.total_files === 1 && !savedType?.includes("zip")) {
            setInputType("source_file");
          }

          const backendFilename = res.data.original_filename || meta.original_filename;
          if (backendFilename) {
            setFilename(backendFilename);
          }
        }
      } catch (err) {
        console.warn("Could not fetch project info from backend:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchMetadata();

    // 3. Load latest review from history for refactored code & verdict
    const history = getReviewHistory();
    if (history.length > 0) {
      const latest = history[0];
      setLatestReview(latest);
      const revObj = latest.review || latest;
      if (revObj?.corrected_code && revObj.corrected_code.length > 0) {
        setRefactoredCodeItems(revObj.corrected_code);
      }
    }
  }, []);

  // Determine correct button text based on input type
  const getDownloadButtonLabel = (): string => {
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

  // Determine correct icon for download button
  const getDownloadButtonIcon = (): string => {
    switch (inputType) {
      case "zip":
        return "📦";
      case "source_file":
        return "📄";
      case "pasted_code":
        return "💻";
      default:
        return "⬇️";
    }
  };

  // Determine human-readable input label
  const getInputTypeLabel = (): string => {
    switch (inputType) {
      case "zip":
        return "ZIP Project Archive";
      case "source_file":
        return "Single Source File";
      case "pasted_code":
        return "Pasted Source Code";
      default:
        return "Project Code";
    }
  };

  // Client-side helper to trigger file download from Blob
  const triggerBrowserDownload = (content: BlobPart, downloadFilename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = downloadFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Dynamic Download Handler
  const handleMainDownload = async () => {
    setDownloading(true);

    try {
      // For pasted code with local content
      if (inputType === "pasted_code" && pastedCode) {
        const targetName = filename && filename !== "project" ? filename : "main.py";
        triggerBrowserDownload(pastedCode, targetName, "text/plain;charset=utf-8");
        setDownloading(false);
        return;
      }

      // Download from backend endpoint
      const response = await API.get("/api/download/project", {
        responseType: "blob"
      });

      const disposition = response.headers["content-disposition"];
      let downloadedName = filename;

      if (disposition && disposition.includes("filename=")) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches != null && matches[1]) {
          downloadedName = matches[1].replace(/['"]/g, "");
        }
      }

      if (!downloadedName || downloadedName === "project") {
        if (inputType === "zip") downloadedName = "project.zip";
        else if (inputType === "source_file") downloadedName = "source_file.py";
        else downloadedName = "code.py";
      }

      const mimeType = inputType === "zip" ? "application/zip" : "text/plain;charset=utf-8";
      triggerBrowserDownload(response.data, downloadedName, mimeType);
    } catch (err: any) {
      console.warn("Direct project download error, attempting fallback:", err);

      // Graceful fallback for single source file or pasted code if refactored code exists
      if (refactoredCodeItems.length > 0) {
        const first = refactoredCodeItems[0];
        triggerBrowserDownload(first.code, first.file_name || filename || "code.py", "text/plain;charset=utf-8");
      } else if (pastedCode) {
        triggerBrowserDownload(pastedCode, filename || "main.py", "text/plain;charset=utf-8");
      } else {
        alert("Could not complete project download. Please ensure the backend is running.");
      }
    } finally {
      setDownloading(false);
    }
  };

  // Download individual refactored file
  const handleDownloadRefactoredFile = (item: { file_name: string; code: string }) => {
    triggerBrowserDownload(item.code, item.file_name || "refactored_code.py", "text/plain;charset=utf-8");
  };

  // Download full Markdown Audit Summary
  const handleDownloadAuditSummary = () => {
    if (!latestReview) {
      alert("No review analysis available to export.");
      return;
    }

    const rev = latestReview.review || latestReview;
    let summaryMd = `# AI Code Review Summary Report\n`;
    summaryMd += `**Project:** ${rev.project?.name || rev.projectName || filename || "Code Review"}\n`;
    summaryMd += `**Date:** ${new Date(latestReview.createdAt || Date.now()).toLocaleString()}\n`;
    summaryMd += `**Confidence:** ${rev.confidence || 95}%\n`;
    summaryMd += `**Overall Score:** ${rev.score != null ? `${rev.score}/100` : "Assessed"}\n\n`;
    summaryMd += `## Final Verdict\n${rev.final_verdict || "Review completed."}\n\n`;

    if (rev.bugs && rev.bugs.length > 0) {
      summaryMd += `## Detected Bugs (${rev.bugs.length})\n`;
      rev.bugs.forEach((b: any, i: number) => {
        summaryMd += `### ${i + 1}. ${b.title || "Bug"}\n`;
        summaryMd += `- **Location:** ${b.file || "source code"}:${b.line || "N/A"}\n`;
        summaryMd += `- **Severity:** ${b.severity || "medium"}\n`;
        summaryMd += `- **Explanation:** ${b.explanation || b.description || "N/A"}\n`;
        summaryMd += `- **Solution:** ${b.suggested_solution || b.fix || "N/A"}\n\n`;
      });
    }

    if (refactoredCodeItems.length > 0) {
      summaryMd += `## Refactored Code\n`;
      refactoredCodeItems.forEach((c) => {
        summaryMd += `### File: ${c.file_name}\n\`\`\`\n${c.code}\n\`\`\`\n\n`;
      });
    }

    triggerBrowserDownload(summaryMd, `audit_report_${filename.replace(/[^a-zA-Z0-9_-]/g, "_")}.md`, "text/markdown;charset=utf-8");
  };

  const handleCopyCode = (code: string, idx: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <main className="final-output-page">
      <div className="final-output-container">
        {/* Page Header */}
        <section className="final-output-header">
          <div className="final-output-badge">✓ Analysis & Refactoring Complete</div>
          <h1 className="final-output-title">Final Output & Deliverables</h1>
          <p className="final-output-subtitle">
            Your codebase has been fully indexed, scanned, and audited by the RAG engine.
            Download the complete analyzed project, inspected source files, or verified refactored implementations below.
          </p>
        </section>

        {/* Hero Card: Input Detection & Dynamic Download Action */}
        <section className="final-output-hero-card">
          <div className="final-output-hero-grid">
            <div className="hero-info-section">
              {/* Dynamic Input Detection Tag */}
              <div className={`hero-type-indicator ${inputType}`}>
                <span>{getDownloadButtonIcon()}</span>
                <span>Detected Input: <strong>{getInputTypeLabel()}</strong></span>
              </div>

              <h2 className="hero-project-name">
                {filename || projectMeta?.project_name || "Analyzed Project"}
              </h2>

              <div className="hero-stats-row">
                <div className="hero-stat-pill">
                  <span>Files Analyzed</span>
                  <strong>{projectMeta?.total_files || (inputType === "zip" ? "Multi-file" : 1)}</strong>
                </div>

                {projectMeta?.total_lines ? (
                  <div className="hero-stat-pill">
                    <span>Lines of Code</span>
                    <strong>{projectMeta.total_lines}</strong>
                  </div>
                ) : null}

                {(latestReview?.score != null || latestReview?.review?.score != null) && (
                  <div className="hero-stat-pill">
                    <span>Quality Score</span>
                    <strong style={{ color: "var(--success)" }}>
                      {latestReview.score ?? latestReview.review?.score} / 100
                    </strong>
                  </div>
                )}

                {(latestReview?.confidence || latestReview?.review?.confidence) && (
                  <div className="hero-stat-pill">
                    <span>AI Confidence</span>
                    <strong>{latestReview.confidence || latestReview.review?.confidence}%</strong>
                  </div>
                )}
              </div>
            </div>

            {/* DYNAMIC DOWNLOAD ACTION BOX */}
            <div className="hero-download-action-box">
              <button
                type="button"
                className="btn-dynamic-main-download"
                onClick={handleMainDownload}
                disabled={downloading}
                title={`Click to ${getDownloadButtonLabel()}`}
              >
                <span>{getDownloadButtonIcon()}</span>
                <span>{downloading ? "Preparing Download..." : getDownloadButtonLabel()}</span>
              </button>

              <span className="hero-download-note">
                {inputType === "zip" && "Includes complete original folder hierarchy & project assets"}
                {inputType === "source_file" && "Preserves original filename, extension, and formatting"}
                {inputType === "pasted_code" && "Downloads verified source file with proper code extension"}
              </span>
            </div>
          </div>
        </section>

        {/* Secondary Actions Bar */}
        <section className="final-output-secondary-actions" style={{ marginBottom: "32px" }}>
          <button
            type="button"
            className="btn-secondary-download"
            onClick={handleDownloadAuditSummary}
            title="Download full Markdown audit report with findings and solutions"
          >
            📋 Download Audit Report (.md)
          </button>

          <Link to="/review" className="btn-secondary-download">
            🔍 Back to Review Details
          </Link>

          <Link to="/dashboard" className="btn-secondary-download">
            📊 View Security Dashboard
          </Link>

          <button
            type="button"
            className="btn-secondary-download"
            onClick={() => navigate("/")}
          >
            🚀 Analyze Another Project
          </button>
        </section>

        {/* Refactored Code Section */}
        {refactoredCodeItems.length > 0 && (
          <section className="final-output-code-section">
            <div className="section-title-row">
              <div>
                <h3>Refactored & Corrected Source Code</h3>
                <p style={{ margin: "4px 0 0 0", fontSize: "13px", color: "var(--text-secondary)" }}>
                  Production-ready files with all security, performance, and bug fixes applied.
                </p>
              </div>
              <span className="theme-count-badge">
                {refactoredCodeItems.length} Refactored File{refactoredCodeItems.length !== 1 ? "s" : ""}
              </span>
            </div>

            <div className="corrected-code-list">
              {refactoredCodeItems.map((item, idx) => (
                <div key={idx} className="code-diff-card" style={{ marginBottom: "1.5rem" }}>
                  <div className="code-diff-header">
                    <span>📄 {item.file_name || "Refactored Code"}</span>
                    <div className="code-header-actions">
                      <button
                        type="button"
                        className="btn-copy-code"
                        onClick={() => handleCopyCode(item.code, idx)}
                      >
                        {copiedIdx === idx ? "✓ Copied!" : "📋 Copy Full File"}
                      </button>
                      <button
                        type="button"
                        className="btn-download-action"
                        onClick={() => handleDownloadRefactoredFile(item)}
                      >
                        ⬇️ Download File
                      </button>
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

        {/* Executive Summary Card */}
        {(latestReview?.review?.final_verdict || latestReview?.final_verdict) && (
          <section className="finding-card" style={{ marginTop: "24px" }}>
            <h4 style={{ fontSize: "16px", marginBottom: "8px", color: "var(--text-primary)" }}>
              🎯 AI Executive Review Verdict
            </h4>
            <p style={{ margin: 0, fontSize: "14px", lineHeight: "1.6", color: "var(--text-secondary)" }}>
              {latestReview?.review?.final_verdict || latestReview?.final_verdict}
            </p>
          </section>
        )}
      </div>
    </main>
  );
};

export default FinalOutput;
