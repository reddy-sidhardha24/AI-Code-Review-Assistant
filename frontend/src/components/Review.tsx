import { useState, useEffect, useCallback, useRef } from "react";
import { useLocation } from "react-router-dom";
import API, { pushGitHubFix } from "../api";
import { useAppAuth } from "../context/AuthContext";
import {
  useReview,
  ReviewData,
  ReviewCategory,
  CommonFinding,
  FileAnalyzed,
  CorrectedCodeItem,
  PerformanceInfo,
  SecurityInfo,
  CodeQualityInfo,
  ProjectInfo
} from "../context/ReviewContext";
import { saveReviewToHistory } from "../utils/reviewHistory";
import CodeDiffPreview from "./CodeDiffPreview";
import Upload from "./Upload";

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

const MULTI_AGENT_STAGES = [
  {
    id: "rag",
    icon: "⚡",
    name: "RAG & Code Context Retrieval",
    focus: "Extracting semantic code chunks and project metadata"
  },
  {
    id: "bug",
    icon: "🐞",
    name: "Bug Detective Agent",
    focus: "Auditing logic bugs, runtime crashes & null safety"
  },
  {
    id: "sec",
    icon: "🛡️",
    name: "AppSec Auditor Agent",
    focus: "Scanning OWASP Top 10 vulnerabilities & credentials"
  },
  {
    id: "perf",
    icon: "⚡",
    name: "Perf Architect Agent",
    focus: "Profiling algorithmic complexity & memory efficiency"
  },
  {
    id: "quality",
    icon: "📐",
    name: "Clean Code Specialist Agent",
    focus: "Enforcing SOLID design principles & maintainability"
  },
  {
    id: "merge",
    icon: "🧩",
    name: "Synthesis Merger Agent",
    focus: "Synthesizing consensus findings into structured report"
  }
];

const SINGLE_AGENT_STAGES = [
  {
    id: "s-rag",
    icon: "🔍",
    name: "Semantic Code Context Retrieval",
    focus: "Retrieving relevant code chunks from vector database"
  },
  {
    id: "s-eval",
    icon: "⚡",
    name: "AI Code Analysis & Verification",
    focus: "Evaluating bugs, security, performance and code quality"
  },
  {
    id: "s-struct",
    icon: "📊",
    name: "Structuring Findings & Health Scoring",
    focus: "Validating against JSON schema and computing project health score"
  }
];

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

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function buildMarkdownReport(review: ReviewData, category: string): string {
  const projName = review.project?.name || "Code Review";
  const langs = (review.project?.languages || []).join(", ") || "Source Code";
  const dateStr = new Date().toLocaleString();
  const catTitle = category.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

  let md = `# AI Code Review Report — ${projName}\n`;
  md += `**Generated:** ${dateStr}\n`;
  md += `**Review Mode / Category:** ${catTitle}\n`;
  md += `**Languages:** ${langs}\n`;
  md += `**AI Confidence:** ${review.confidence || 90}%\n`;

  if (review.score !== null && review.score !== undefined) {
    md += `**Overall Project Score:** ${review.score}/100\n`;
  }

  md += `\n---\n\n## 1. Executive Summary\n${review.answer_summary || "Review completed."}\n\n`;

  if (review.final_verdict) {
    md += `## 2. Final Verdict\n${review.final_verdict}\n\n`;
  }

  md += `## 3. Files Analyzed\n`;
  if (review.files_analyzed && review.files_analyzed.length > 0) {
    review.files_analyzed.forEach((f) => {
      md += `- 📄 \`${f.file_name}\` (${f.language})\n`;
    });
  } else {
    md += `- Complete project source\n`;
  }

  md += `\n---\n\n## 4. Identified Issues & Recommended Fixes\n\n`;

  const allFindings: { item: CommonFinding; cat: string }[] = [];
  (review.bugs || []).forEach((b) => allFindings.push({ item: b, cat: "Bug" }));
  (review.errors || []).forEach((e) => allFindings.push({ item: e, cat: "Error" }));
  (review.security?.issues || []).forEach((s) => allFindings.push({ item: s, cat: "Security" }));
  (review.performance?.issues || []).forEach((p) => allFindings.push({ item: p, cat: "Performance" }));
  (review.code_quality?.observations || []).forEach((o) => allFindings.push({ item: o, cat: "Quality Observation" }));
  (review.code_quality?.suggestions || []).forEach((s) => allFindings.push({ item: s, cat: "Quality Suggestion" }));

  if (allFindings.length === 0) {
    md += `🎉 **No issues detected in the analyzed scope!**\n`;
  } else {
    allFindings.forEach(({ item, cat }, idx) => {
      const title = item.title || `Finding #${idx + 1}`;
      const sev = (item.severity || "medium").toUpperCase();
      const loc = item.file ? `\`${item.file}\`${item.line ? ` (Line ${item.line})` : ""}` : "Source code";
      const exp = item.explanation || item.description || "No specific explanation.";
      const sol = item.suggested_solution || item.fix || item.suggestion || "Follow recommended best practices.";

      md += `### ${idx + 1}. [${sev}] ${title}\n`;
      md += `- **Category:** ${cat}\n`;
      md += `- **Location:** ${loc}\n`;
      md += `- **Explanation:** ${exp}\n`;
      md += `- **Suggested Solution:** ${sol}\n`;

      if (item.before_code) {
        md += `\n**Before (Problematic Code):**\n\`\`\`\n${item.before_code.trim()}\n\`\`\`\n`;
      }
      if (item.after_code || item.corrected_code) {
        const code = (item.after_code || item.corrected_code || "").trim();
        md += `\n**After (Corrected Code):**\n\`\`\`\n${code}\n\`\`\`\n`;
      }
      if (item.reason_for_correction) {
        md += `\n🛡️ **Reason for Correction:** ${item.reason_for_correction}\n`;
      }
      md += `\n`;
    });
  }

  return md;
}

function buildCorrectedCodeText(review: ReviewData): string {
  if (review.corrected_code && review.corrected_code.length > 0) {
    return review.corrected_code
      .map(
        (f) =>
          `# ============================================================\n# File: ${f.file_name}\n# ============================================================\n\n${f.code.trim()}\n`
      )
      .join("\n\n");
  }

  const allFindings = [
    ...(review.bugs || []),
    ...(review.errors || []),
    ...(review.security?.issues || []),
    ...(review.performance?.issues || []),
    ...(review.code_quality?.observations || []),
    ...(review.code_quality?.suggestions || []),
    ...(review.detected_issues || [])
  ];

  const snips = allFindings
    .filter((f) => f.after_code || f.corrected_code)
    .map(
      (f) =>
        `# --- Fix for: ${f.title} (${f.file || "source"}) ---\n${(f.after_code || f.corrected_code || "").trim()}`
    );

  if (snips.length > 0) {
    return `# ============================================================\n# Refactored Code with Applied Fixes\n# ============================================================\n\n` + snips.join("\n\n");
  }

  return "# Code analysis passed. No refactoring changes were required.";
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
  const { user } = useAppAuth();
  const location = useLocation();
  const initialFlowHandledRef = useRef(false);

  const {
    review,
    loading,
    question,
    setQuestion,
    activeCategory,
    setActiveCategory,
    currentReviewCategory,
    error,
    agentMode,
    updatingMode,
    modeNotice,
    handleToggleAgentMode,
    runReview,
    cancelReview,
    clearReview,
    loadReviewDirectly
  } = useReview();

  // Email delivery state
  const initialEmail =
    localStorage.getItem("clerk_user_email") ||
    localStorage.getItem("auth_user_email") ||
    "";
  const [email, setEmail] = useState(initialEmail);
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailStatus, setEmailStatus] = useState<{
    success: boolean;
    message: string;
    outboxPath?: string;
    folderName?: string;
  } | null>(null);

  const [downloadingFormat, setDownloadingFormat] = useState<string | null>(null);
  const [downloadingZip, setDownloadingZip] = useState(false);
  const [pushingPR, setPushingPR] = useState(false);
  const [prResult, setPrResult] = useState<{
    html_url: string;
    pr_number: number;
    branch: string;
    files_changed: number;
  } | null>(null);
  const [showPromptCard, setShowPromptCard] = useState<boolean>(false);
  const [workflowStep, setWorkflowStep] = useState<"source" | "prompt">("source");

  // History/dashboard results are an explicit navigation; direct visits start at source selection.
  useEffect(() => {
    if (initialFlowHandledRef.current) return;
    initialFlowHandledRef.current = true;
    const stateObj = location.state as any;
    if (stateObj && stateObj.review) {
      loadReviewDirectly(stateObj.review, stateObj.category, stateObj.question);
      setShowPromptCard(false);
      setWorkflowStep("prompt");
    } else if (!loading) {
      clearReview();
      setWorkflowStep("source");
    }
  }, [location.state, loadReviewDirectly, loading, clearReview]);

  // Active Multi-Agent Execution Progression Tracker
  const [activeStage, setActiveStage] = useState<number>(0);
  const [elapsedSec, setElapsedSec] = useState<number>(0);

  useEffect(() => {
    if (!loading) {
      setActiveStage(0);
      setElapsedSec(0);
      return;
    }

    let start = Date.now();
    try {
      const p = localStorage.getItem("review_in_progress");
      if (p) {
        const parsed = JSON.parse(p);
        if (parsed.startTime) start = parsed.startTime;
      }
    } catch (e) {}

    const computeStage = () => {
      const elapsed = Math.max(0, Math.floor((Date.now() - start) / 1000));
      setElapsedSec(elapsed);
      if (agentMode === "multi") {
        if (elapsed < 3) setActiveStage(0);
        else if (elapsed < 11) setActiveStage(1);
        else if (elapsed < 20) setActiveStage(2);
        else if (elapsed < 29) setActiveStage(3);
        else if (elapsed < 38) setActiveStage(4);
        else setActiveStage(5);
      } else {
        if (elapsed < 3) setActiveStage(0);
        else if (elapsed < 14) setActiveStage(1);
        else setActiveStage(2);
      }
    };

    computeStage();
    const interval = setInterval(computeStage, 1000);
    return () => clearInterval(interval);
  }, [loading, agentMode]);

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const handleDownloadReportFormat = async (format: "pdf" | "markdown" | "html") => {
    if (!review) return;
    setDownloadingFormat(format);
    try {
      const res = await API.post(
        "/api/download-report",
        {
          review_data: review,
          category: currentReviewCategory,
          format
        },
        { responseType: "blob" }
      );
      const ext = format === "pdf" ? "pdf" : format === "html" ? "html" : "md";
      const projName = review.project?.name || "Code_Review";
      downloadBlob(new Blob([res.data]), `${projName}_Audit_Report.${ext}`);
    } catch (e) {
      console.error("Report download failed:", e);
      alert("Failed to generate report download. Please try again.");
    } finally {
      setDownloadingFormat(null);
    }
  };

  const handleDownloadFullZip = async () => {
    if (!review) return;
    setDownloadingZip(true);
    const pName = review?.project?.name || "Project";
    try {
      const res = await API.post(
        "/api/download-corrected-project",
        { project_name: pName, review_data: review },
        { responseType: "blob" }
      );
      downloadBlob(new Blob([res.data]), `${pName}_Corrected_Full_Project.zip`);
    } catch (e) {
      console.error("Project download failed:", e);
      alert(await getDownloadErrorMessage(e, "Failed to package corrected project ZIP."));
    } finally {
      setDownloadingZip(false);
    }
  };

  const handleDownloadCorrectedOnlyZip = async () => {
    if (!review) return;
    setDownloadingZip(true);
    const pName = review?.project?.name || "Project";
    try {
      const res = await API.post(
        "/api/download-corrected-files",
        { project_name: pName, review_data: review },
        { responseType: "blob" }
      );
      downloadBlob(new Blob([res.data]), `${pName}_Corrected_Files_Only.zip`);
    } catch (e) {
      console.error("Files download failed:", e);
      alert("Failed to package corrected files ZIP.");
    } finally {
      setDownloadingZip(false);
    }
  };

  const handlePushGitHubPR = async () => {
    if (!review) return;
    setPushingPR(true);
    try {
      const correctedList: { path: string; code: string }[] = [];
      if (Array.isArray(review.corrected_code) && review.corrected_code.length > 0) {
        review.corrected_code.forEach((c) => {
          correctedList.push({ path: c.file_name, code: c.code });
        });
      } else {
        const issues = (review.bugs || []).concat(review.errors || []).concat(review.detected_issues || []);
        issues.forEach((b) => {
          const after = b.after_code || b.corrected_code;
          if (after && after.trim()) {
            correctedList.push({ path: b.file || "corrected_code.py", code: after.trim() });
          }
        });
      }

      if (correctedList.length === 0) {
        alert("No corrected code files found in this review to commit.");
        setPushingPR(false);
        return;
      }

      const st = await API.get("/api/github/status");
      if (!st.data?.connected) {
        alert("Please connect your GitHub account in Configuration first.");
        return;
      }

      let repoName = review.project?.name || review.project_name || "project";
      if (repoName.includes("/")) {
        repoName = repoName.split("/").pop() || repoName;
      }

      const prRes = await pushGitHubFix({
        owner: st.data.username,
        repo: repoName,
        base_branch: "main",
        corrected_files: correctedList
      });

      if (prRes.data?.html_url) {
        setPrResult({
          html_url: prRes.data.html_url,
          pr_number: prRes.data.pr_number,
          branch: prRes.data.branch,
          files_changed: prRes.data.files_changed ?? correctedList.length
        });
      } else {
        alert(prRes.data?.detail || "GitHub did not return a Pull Request link.");
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || "Could not create Pull Request. Please check GitHub connection.");
    } finally {
      setPushingPR(false);
    }
  };



  const askQuestion = async () => {
    setEmailStatus(null);
    await runReview(activeCategory, question);
  };

  const handleSelectCategory = (cat: ReviewCategory) => {
    setEmailStatus(null);
    setActiveCategory(cat);
    runReview(cat);
  };

  const handleClearReview = () => {
    setEmailStatus(null);
    clearReview();
    setShowPromptCard(false);
    setWorkflowStep("source");
  };

  const handleSendEmail = async () => {
    const targetEmail = email.trim();
    if (!targetEmail || !targetEmail.includes("@") || !targetEmail.includes(".")) {
      setEmailStatus({
        success: false,
        message: "Please enter a valid client email address."
      });
      return;
    }
    if (!review) {
      setEmailStatus({
        success: false,
        message: "No active review available to send."
      });
      return;
    }

    setSendingEmail(true);
    setEmailStatus(null);

    try {
      const reportMd = buildMarkdownReport(review, currentReviewCategory);
      const res = await API.post("/api/send-email", {
        email: targetEmail,
        category: currentReviewCategory,
        review_data: review,
        report_markdown: reportMd
      });

      if (res.data?.success) {
        setEmailStatus({
          success: true,
          message:
            res.data?.message ||
            "Review Report and Corrected Code have been successfully sent to the client's email address.",
          outboxPath: res.data?.outbox_path,
          folderName: res.data?.folder_name
        });
      } else {
        setEmailStatus({
          success: false,
          message: res.data?.message || "Failed to deliver email."
        });
      }
    } catch (err: any) {
      const msg =
        err.response?.data?.detail || err.message || "Failed to deliver email.";
      setEmailStatus({
        success: false,
        message:
          typeof msg === "string" ? msg : "An error occurred while delivering email."
      });
    } finally {
      setSendingEmail(false);
    }
  };

  const handleDownloadReport = () => {
    if (!review) return;
    const md = buildMarkdownReport(review, currentReviewCategory);
    downloadFile(md, `Review_Report_${currentReviewCategory}.md`, "text/markdown");
  };

  const handleDownloadCode = () => {
    if (!review) return;
    const code = buildCorrectedCodeText(review);
    downloadFile(code, `Corrected_Code_${currentReviewCategory}.txt`, "text/plain");
  };

  /* ==========================================================
     KEYBOARD
     ========================================================== */

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (event.key === "Enter" && event.ctrlKey) {
      event.preventDefault();
      askQuestion();
    }
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


        {!loading && workflowStep === "source" && !(location.state as any)?.review ? (
          <section className="review-source-step">
            <div className="section-label">STEP 1 OF 2 · CHOOSE A SOURCE</div>
            <h2>Where should we review?</h2>
            <p>Choose a ZIP, source files, pasted code, or a GitHub repository. We’ll index it before the review.</p>
            <Upload onComplete={() => setWorkflowStep("prompt")} />
          </section>
        ) : (
        <>

        {/* ==================================================
            AUDITOR IDENTITY & EXECUTION ARCHITECTURE BAR
            ================================================== */}
        <section className="audit-context-bar">
          <div className="audit-context-user">
            <div className="audit-user-avatar">
              {user?.imageUrl ? (
                <img src={user.imageUrl} alt={user.fullName || "User"} />
              ) : (
                <span>{(user?.fullName || user?.email || "U")[0].toUpperCase()}</span>
              )}
            </div>
            <div className="audit-user-info">
              <span className="audit-user-title">ACTIVE AUDITOR</span>
              <span className="audit-user-name">
                {user?.fullName || user?.email || "Developer"}
              </span>
              {user?.email && user.fullName && (
                <span className="audit-user-email">({user.email})</span>
              )}
            </div>
            <span className="audit-db-synced-pill" title="Audits & preferences synchronized with SQLite database">
              <span className="status-dot green" /> DB Synced
            </span>
          </div>

          <div className="audit-context-mode">
            <div className="audit-mode-details">
              <span className="audit-mode-title">EXECUTION ARCHITECTURE</span>
              <div className="audit-mode-status">
                {agentMode === "multi" ? (
                  <span className="mode-badge multi" title="Multi-Agent Collaborative Review with 4 domain specialist agents">
                    <span className="mode-badge-icon">🤖✨</span> Multi-Agent Collaborative Mode
                  </span>
                ) : (
                  <span className="mode-badge single" title="Fast single-pass model evaluation">
                    <span className="mode-badge-icon">⚡</span> Fast Single-Agent Mode
                  </span>
                )}
              </div>
            </div>

            <div className="audit-mode-actions">
              {agentMode === "multi" ? (
                <button
                  type="button"
                  className="audit-mode-switch-btn"
                  disabled={updatingMode || loading}
                  onClick={() => handleToggleAgentMode("single")}
                  title="Switch to Single-Agent mode for faster execution"
                >
                  {updatingMode ? "Switching..." : "⚡ Switch to Single-Agent"}
                </button>
              ) : (
                <button
                  type="button"
                  className="audit-mode-switch-btn active-callout"
                  disabled={updatingMode || loading}
                  onClick={() => handleToggleAgentMode("multi")}
                  title="Enable Multi-Agent Collaborative Mode with 4 specialist agents"
                >
                  {updatingMode ? "Switching..." : "🤖✨ Enable Multi-Agent"}
                </button>
              )}
            </div>
          </div>
        </section>

        {/* Specialist Agents Breakdown Tray (Shown when in Multi-Agent mode) */}
        {agentMode === "multi" && (
          <div className="multi-agent-specialists-tray">
            <span className="tray-label">Specialist Agents:</span>
            <span className="specialist-pill bug" title="Scans for runtime errors, NPEs, logic bugs">
              🐞 Bug Detective
            </span>
            <span className="specialist-pill sec" title="Audits OWASP Top 10 vulnerabilities & hardcoded secrets">
              🛡️ AppSec Auditor
            </span>
            <span className="specialist-pill perf" title="Profiles algorithmic complexity & memory efficiency">
              ⚡ Perf Architect
            </span>
            <span className="specialist-pill qual" title="Evaluates SOLID principles, clean code & maintainability">
              📐 Clean Code Specialist
            </span>
            <span className="tray-arrow">➔</span>
            <span className="specialist-pill merge" title="Synthesizes consensus findings into unified report">
              🧩 Synthesis Merger
            </span>
          </div>
        )}

        {modeNotice && (
          <div className="audit-mode-toast">
            {modeNotice}
          </div>
        )}

        {!review && !loading && workflowStep === "prompt" && (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px", marginBottom: "14px", flexWrap: "wrap" }}>
            <span className="section-label">STEP 2 OF 2 · SET UP YOUR REVIEW</span>
            <button type="button" className="btn-secondary" onClick={() => { clearReview(); setWorkflowStep("source"); }}>
              ← Change source
            </button>
          </div>
        )}

        {/* ==================================================
            PERSISTED ACTIVE AUDIT SESSION BANNER
            ================================================== */}
        {review && !loading && (
          <div className="active-session-alert-banner" style={{ marginBottom: "1.25rem" }}>
            <div className="session-banner-left">
              <span className="session-pulse-dot" />
              <div>
                <span className="session-banner-title">
                  Audit Report: <strong>{review.project?.name || "Code Review"}</strong>
                </span>
                <span className="session-banner-meta">
                  Category: <strong>{formatReviewType(currentReviewCategory)}</strong> • Architecture: <strong>{review.agent_mode === "multi" ? "🤖 Multi-Agent Ensemble" : "⚡ Single-Agent"}</strong> • Score: <strong>{review.score !== null && review.score !== undefined ? `${review.score}/100` : "N/A"}</strong>
                </span>
              </div>
            </div>
            <div className="session-banner-right">
              <button
                type="button"
                className="btn-session-scroll"
                onClick={() => setShowPromptCard(!showPromptCard)}
                title="Toggle question/prompt panel"
              >
                {showPromptCard ? "▲ Collapse Prompt Box" : "💬 New Prompt / Re-analyze"}
              </button>
              <button
                type="button"
                className="btn-session-clear"
                onClick={handleClearReview}
                title="Clear current review and start a fresh analysis"
              >
                + New Analysis
              </button>
            </div>
          </div>
        )}

        {/* ==================================================
            QUESTION PANEL
            ================================================== */}

        {(!review || showPromptCard) && (
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

          <div className="review-category-selector-container">
            <div className="category-selector-header">
              <span className="category-selector-label">SELECT REVIEW CATEGORY:</span>
              <span className="category-selector-hint">Click a category to run review immediately</span>
            </div>

            <div className="review-category-button-group">
              <button
                type="button"
                className={`category-select-btn ${activeCategory === "full_review" ? "active" : ""}`}
                onClick={() => handleSelectCategory("full_review")}
                disabled={loading}
              >
                <span className="category-btn-icon">🌟</span>
                <span className="category-btn-text">Full Project Review</span>
              </button>

              <button
                type="button"
                className={`category-select-btn ${activeCategory === "bugs" ? "active" : ""}`}
                onClick={() => handleSelectCategory("bugs")}
                disabled={loading}
              >
                <span className="category-btn-icon">🐛</span>
                <span className="category-btn-text">Bugs</span>
              </button>

              <button
                type="button"
                className={`category-select-btn ${activeCategory === "security" ? "active" : ""}`}
                onClick={() => handleSelectCategory("security")}
                disabled={loading}
              >
                <span className="category-btn-icon">🛡️</span>
                <span className="category-btn-text">Security</span>
              </button>

              <button
                type="button"
                className={`category-select-btn ${activeCategory === "performance" ? "active" : ""}`}
                onClick={() => handleSelectCategory("performance")}
                disabled={loading}
              >
                <span className="category-btn-icon">⚡</span>
                <span className="category-btn-text">Performance</span>
              </button>

              <button
                type="button"
                className={`category-select-btn ${activeCategory === "code_quality" ? "active" : ""}`}
                onClick={() => handleSelectCategory("code_quality")}
                disabled={loading}
              >
                <span className="category-btn-icon">✨</span>
                <span className="category-btn-text">Code Quality</span>
              </button>
            </div>
          </div>


        </section>
        )}


        {/* ==================================================
            ERROR
            ================================================== */}

        {error && (

          <section className="review-error-card">

            <div className="review-error-icon">
              !
            </div>

            <div className="review-error-content">

              <h3>{error.startsWith("Analysis stopped") ? "Analysis stopped" : error.startsWith("Stopping analysis") ? "Stopping analysis" : "Review failed"}</h3>

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
              {agentMode === "multi"
                ? "🤖 Multi-Agent Ensemble Analyzing Codebase..."
                : "⚡ Analyzing your project..."}
            </h3>

            <p>
              {agentMode === "multi"
                ? "4 Domain-Specialist AI Agents are concurrently auditing your codebase, followed by synthesis consensus."
                : "Retrieving relevant code, evaluating findings, and generating structured review."}
            </p>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "12px", marginTop: "14px", marginBottom: "16px", flexWrap: "wrap" }}>
              <span style={{ background: "rgba(56, 189, 248, 0.12)", color: "#38bdf8", border: "1px solid rgba(56, 189, 248, 0.3)", borderRadius: "20px", padding: "4px 14px", fontSize: "12.5px", fontWeight: 600 }}>
                ⏱ Elapsed: {elapsedSec}s • Active Inference
              </span>
              <button
                type="button"
                onClick={() => void cancelReview()}
                style={{ background: "rgba(239, 68, 68, 0.12)", color: "#ef4444", border: "1px solid rgba(239, 68, 68, 0.3)", borderRadius: "20px", padding: "4px 14px", fontSize: "12.5px", fontWeight: 600, cursor: "pointer" }}
                title="Stop the current analysis"
              >
                ✕ Stop Analysis
              </button>
            </div>

            {agentMode === "multi" ? (
              <div className="review-loading-steps multi-steps">
                {MULTI_AGENT_STAGES.map((stg, idx) => {
                  const isDone = idx < activeStage;
                  const isRunning = idx === activeStage;
                  return (
                    <div
                      key={stg.id}
                      className={`step-item ${isDone ? "completed" : isRunning ? "active running" : "queued"}`}
                    >
                      <div className="step-item-left">
                        <span className="step-icon">{stg.icon}</span>
                        <div className="step-text-group">
                          <span className="step-name">{stg.name}</span>
                          <span className="step-focus">{stg.focus}</span>
                        </div>
                      </div>
                      <div className="step-item-right">
                        {isDone && <span className="agent-status-pill completed">✓ Done</span>}
                        {isRunning && (
                          <span className="agent-status-pill running">
                            <span className="mini-spinner" /> Auditing...
                          </span>
                        )}
                        {!isDone && !isRunning && (
                          <span className="agent-status-pill queued">Queued</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="review-loading-steps single-steps">
                {SINGLE_AGENT_STAGES.map((stg, idx) => {
                  const isDone = idx < activeStage;
                  const isRunning = idx === activeStage;
                  return (
                    <div
                      key={stg.id}
                      className={`step-item ${isDone ? "completed" : isRunning ? "active running" : "queued"}`}
                    >
                      <div className="step-item-left">
                        <span className="step-icon">{stg.icon}</span>
                        <div className="step-text-group">
                          <span className="step-name">{stg.name}</span>
                          <span className="step-focus">{stg.focus}</span>
                        </div>
                      </div>
                      <div className="step-item-right">
                        {isDone && <span className="agent-status-pill completed">✓ Done</span>}
                        {isRunning && (
                          <span className="agent-status-pill running">
                            <span className="mini-spinner" /> Running...
                          </span>
                        )}
                        {!isDone && !isRunning && (
                          <span className="agent-status-pill queued">Queued</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

          </section>

        )}


        {/* ==================================================
            REVIEW RESULT
            ================================================== */}

        {review && !loading && (() => {
          const isFullReview =
            currentReviewCategory === "full_review" ||
            (!currentReviewCategory && review.review_types?.includes("full_review"));

          const isBugs = !isFullReview && currentReviewCategory === "bugs";
          const isSecurity = !isFullReview && currentReviewCategory === "security";
          const isPerformance = !isFullReview && currentReviewCategory === "performance";
          const isQuality = !isFullReview && currentReviewCategory === "code_quality";

          const bugCount = safeCount(review.bugs) + safeCount(review.errors);
          const secCount = review.security?.issues_found || safeCount(review.security?.issues);
          const perfCount = safeCount(review.performance?.issues);
          const qualCount =
            safeCount(review.code_quality?.observations) +
            safeCount(review.code_quality?.suggestions);

          return (
            <section className="review-result-section" id="review-result-section">
              {/* ================================================
                  RESULT HEADER
                  ================================================ */}
              <div className="review-result-header">
                <div>
                  <div className="section-label">
                    {isFullReview
                      ? "FULL PROJECT ANALYSIS COMPLETE"
                      : `${currentReviewCategory.toUpperCase()} ANALYSIS COMPLETE`}
                  </div>

                  <h2>{review.project?.name || "Project Review"}</h2>

                  <p>
                    {getLanguageLabel(review.project?.languages || [])}
                    {" • "}
                    {review.project?.total_files || 0} files
                    {" • "}
                    {review.project?.total_lines || 0} lines
                  </p>
                </div>

                <div className="result-header-actions">
                  <span className={`result-agent-mode-badge ${review.agent_mode === "multi" ? "multi" : "single"}`} title="AI Execution Architecture">
                    {review.agent_mode === "multi" ? "🤖 Multi-Agent Ensemble" : "⚡ Single-Agent"}
                  </span>
                  <span className="result-auditor-badge" title="Auditor linked to SQLite database">
                    👤 {review.audited_by?.name || (user?.fullName || user?.email || "Developer")}
                  </span>
                  {(isFullReview || isBugs || isSecurity || isPerformance || isQuality) && (
                    <span className="current-mode-pill">
                      {isFullReview && "🌟 Full Project Review"}
                      {isBugs && "🐛 Bugs Only"}
                      {isSecurity && "🛡️ Security Only"}
                      {isPerformance && "⚡ Performance Only"}
                      {isQuality && "✨ Code Quality Only"}
                    </span>
                  )}
                  <button
                    type="button"
                    className="review-clear-button"
                    onClick={handleClearReview}
                  >
                    New Review
                  </button>
                </div>
              </div>



              {/* ================================================
                  SUMMARY CARD
                  ================================================ */}
              <section className="review-summary-card">
                <div className="review-summary-icon">✦</div>
                <div>
                  <span>
                    {isFullReview ? "EXECUTIVE SUMMARY" : `${currentReviewCategory.toUpperCase()} SUMMARY`}
                  </span>
                  <p>
                    {review.answer_summary ||
                      "The review completed successfully. See the findings below for detailed analysis."}
                  </p>
                </div>
              </section>

              {/* ==============================================================
                  MODE 1: FULL PROJECT REVIEW (ALL CATEGORIES TOGETHER + SCORE)
                  ============================================================== */}
              {isFullReview && (
                <>
                  {/* Dynamic Grounded Health Score Hero */}
                  {review.score !== null && review.score !== undefined && (
                    <section className="full-review-score-hero">
                      <div className="score-hero-left">
                        <span className="score-hero-label">
                          PROJECT HEALTH SCORE
                        </span>
                        <div className="score-hero-number-row">
                          <span
                            className={`score-hero-val ${
                              review.score >= 80
                                ? "score-good"
                                : review.score >= 60
                                ? "score-mid"
                                : "score-poor"
                            }`}
                          >
                            {review.score}
                          </span>
                          <span className="score-hero-max">/ 100</span>
                        </div>
                        <p className="score-hero-explanation">
                          Calculated dynamically based on grounded static analysis, issue severity weights, and codebase stability.
                        </p>
                      </div>

                      <div className="score-hero-right">
                        <div className="score-hero-metric">
                          <span className="metric-lbl">AI CONFIDENCE</span>
                          <span className="metric-val">
                            {review.confidence || 90}%
                          </span>
                        </div>
                        <div className="score-hero-metric">
                          <span className="metric-lbl">TOTAL ISSUES</span>
                          <span className="metric-val">
                            {bugCount + secCount + perfCount + qualCount}
                          </span>
                        </div>
                      </div>
                    </section>
                  )}

                  {/* Multi-category Statistics Grid */}
                  <section className="review-stat-grid">
                    <div className="review-stat-card">
                      <span className="review-stat-label">BUGS</span>
                      <strong className="stat-red">{bugCount}</strong>
                      <small>detected</small>
                    </div>

                    <div className="review-stat-card">
                      <span className="review-stat-label">SECURITY</span>
                      <strong className="stat-yellow">{secCount}</strong>
                      <small>issues</small>
                    </div>

                    <div className="review-stat-card">
                      <span className="review-stat-label">PERFORMANCE</span>
                      <strong className="stat-blue">{perfCount}</strong>
                      <small>concerns</small>
                    </div>

                    <div className="review-stat-card">
                      <span className="review-stat-label">CODE QUALITY</span>
                      <strong className="stat-purple">{qualCount}</strong>
                      <small>findings</small>
                    </div>

                    <div className="review-stat-card">
                      <span className="review-stat-label">CONFIDENCE</span>
                      <strong className="stat-green">
                        {review.confidence || 90}%
                      </strong>
                      <small>AI confidence</small>
                    </div>
                  </section>

                  {/* Final Verdict */}
                  {review.final_verdict && (
                    <section className="review-verdict-card">
                      <div className="review-verdict-heading">
                        <span>FINAL VERDICT</span>
                        <div className="review-confidence">
                          {review.confidence || 90}% confidence
                        </div>
                      </div>
                      <p>{review.final_verdict}</p>
                    </section>
                  )}

                  {/* 1. Bugs */}
                  {review.bugs?.length > 0 && (
                    <section className="review-detail-section">
                      <div className="review-detail-heading">
                        <div>
                          <span className="detail-icon danger">!</span>
                          <div>
                            <h3>Bugs & Runtime Issues</h3>
                            <p>Confirmed and potential problems detected in the project.</p>
                          </div>
                        </div>
                        <strong>{review.bugs.length}</strong>
                      </div>

                      <div className="review-findings">
                        {review.bugs.map((bug, index) => (
                          <IssueSolutionCard
                            key={`bug-${index}`}
                            issue={bug}
                            categoryBadge="Bug"
                          />
                        ))}
                      </div>
                    </section>
                  )}

                  {/* 1b. Errors */}
                  {review.errors?.length > 0 && (
                    <section className="review-detail-section">
                      <div className="review-detail-heading">
                        <div>
                          <span className="detail-icon danger">!</span>
                          <div>
                            <h3>Runtime Errors & Exceptions</h3>
                            <p>Errors identified during the analysis.</p>
                          </div>
                        </div>
                        <strong>{review.errors.length}</strong>
                      </div>

                      <div className="review-findings">
                        {review.errors.map((item, index) => (
                          <IssueSolutionCard
                            key={`error-${index}`}
                            issue={item}
                            categoryBadge="Error"
                          />
                        ))}
                      </div>
                    </section>
                  )}

                  {/* 2. Security */}
                  {review.security && review.security.issues_found > 0 && (
                    <section className="review-detail-section">
                      <div className="review-detail-heading">
                        <div>
                          <span className="detail-icon warning">🛡️</span>
                          <div>
                            <h3>Security Issues</h3>
                            <p>Vulnerabilities and secret exposures identified by the AI reviewer.</p>
                          </div>
                        </div>
                        <strong>{review.security.issues_found}</strong>
                      </div>

                      <div className="review-findings">
                        {review.security.issues.map((issue, index) => (
                          <IssueSolutionCard
                            key={`sec-${index}`}
                            issue={issue}
                            categoryBadge="Security"
                          />
                        ))}
                      </div>
                    </section>
                  )}

                  {/* 3. Performance */}
                  {review.performance && (
                    <section className="review-detail-section">
                      <div className="review-detail-heading">
                        <div>
                          <span className="detail-icon info">⚡</span>
                          <div>
                            <h3>Performance</h3>
                            <p>Complexity and performance bottlenecks found in the project.</p>
                          </div>
                        </div>
                        <strong>{review.performance.issues?.length || 0}</strong>
                      </div>

                      <div className="complexity-grid">
                        <div>
                          <span>TIME COMPLEXITY</span>
                          <strong>
                            {review.performance.time_complexity || "Not determined"}
                          </strong>
                        </div>
                        <div>
                          <span>SPACE COMPLEXITY</span>
                          <strong>
                            {review.performance.space_complexity || "Not determined"}
                          </strong>
                        </div>
                      </div>

                      {review.performance.issues?.length > 0 && (
                        <div className="review-findings">
                          {review.performance.issues.map((issue, index) => (
                            <IssueSolutionCard
                              key={`perf-${index}`}
                              issue={issue}
                              categoryBadge="Performance"
                            />
                          ))}
                        </div>
                      )}
                    </section>
                  )}

                  {/* 4. Code Quality */}
                  {review.code_quality && (
                    <section className="review-detail-section">
                      <div className="review-detail-heading">
                        <div>
                          <span className="detail-icon purple">✦</span>
                          <div>
                            <h3>Code Quality</h3>
                            <p>Readability, maintainability, and structural observations.</p>
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
                </>
              )}

              {/* ==============================================================
                  MODE 2: BUGS ONLY (STRICT CATEGORY ISOLATION)
                  ============================================================== */}
              {isBugs && (
                <>
                  <section className="category-isolated-stat-hero">
                    <div className="cat-stat-box">
                      <span className="cat-stat-lbl">BUGS DETECTED</span>
                      <strong className="cat-stat-num red">{bugCount}</strong>
                    </div>
                    {review.score !== null && review.score !== undefined && (
                      <div className="cat-stat-box">
                        <span className="cat-stat-lbl">RELIABILITY HEALTH SCORE</span>
                        <strong className={`cat-stat-num ${review.score >= 80 ? "green" : review.score >= 60 ? "amber" : "red"}`}>
                          {review.score} / 100
                        </strong>
                      </div>
                    )}
                    <div className="cat-stat-box">
                      <span className="cat-stat-lbl">AI CONFIDENCE</span>
                      <strong className="cat-stat-num green">
                        {review.confidence || 90}%
                      </strong>
                    </div>
                  </section>

                  {bugCount === 0 ? (
                    <div className="empty-category-card">
                      <span className="empty-icon">🎉</span>
                      <h3>Zero Bugs Found</h3>
                      <p>No confirmed functional bugs or runtime exceptions were detected in the analyzed code.</p>
                    </div>
                  ) : (
                    <>
                      {review.bugs?.length > 0 && (
                        <section className="review-detail-section">
                          <div className="review-detail-heading">
                            <div>
                              <span className="detail-icon danger">!</span>
                              <div>
                                <h3>Confirmed Bugs</h3>
                                <p>Logical and functional defects identified in the project.</p>
                              </div>
                            </div>
                            <strong>{review.bugs.length}</strong>
                          </div>

                          <div className="review-findings">
                            {review.bugs.map((bug, index) => (
                              <IssueSolutionCard
                                key={`bug-only-${index}`}
                                issue={bug}
                                categoryBadge="Bug"
                              />
                            ))}
                          </div>
                        </section>
                      )}

                      {review.errors?.length > 0 && (
                        <section className="review-detail-section">
                          <div className="review-detail-heading">
                            <div>
                              <span className="detail-icon danger">!</span>
                              <div>
                                <h3>Runtime Errors & Exceptions</h3>
                                <p>Execution failures and unhandled exception risks.</p>
                              </div>
                            </div>
                            <strong>{review.errors.length}</strong>
                          </div>

                          <div className="review-findings">
                            {review.errors.map((item, index) => (
                              <IssueSolutionCard
                                key={`err-only-${index}`}
                                issue={item}
                                categoryBadge="Error"
                              />
                            ))}
                          </div>
                        </section>
                      )}
                    </>
                  )}
                </>
              )}

              {/* ==============================================================
                  MODE 3: SECURITY ONLY (STRICT CATEGORY ISOLATION)
                  ============================================================== */}
              {isSecurity && (
                <>
                  <section className="category-isolated-stat-hero">
                    <div className="cat-stat-box">
                      <span className="cat-stat-lbl">SECURITY VULNERABILITIES</span>
                      <strong className="cat-stat-num yellow">{secCount}</strong>
                    </div>
                    {review.score !== null && review.score !== undefined && (
                      <div className="cat-stat-box">
                        <span className="cat-stat-lbl">SECURITY HEALTH SCORE</span>
                        <strong className={`cat-stat-num ${review.score >= 80 ? "green" : review.score >= 60 ? "amber" : "red"}`}>
                          {review.score} / 100
                        </strong>
                      </div>
                    )}
                    <div className="cat-stat-box">
                      <span className="cat-stat-lbl">AI CONFIDENCE</span>
                      <strong className="cat-stat-num green">
                        {review.confidence || 90}%
                      </strong>
                    </div>
                  </section>

                  {secCount === 0 ? (
                    <div className="empty-category-card">
                      <span className="empty-icon">🛡️</span>
                      <h3>Zero Security Vulnerabilities</h3>
                      <p>No hardcoded secrets, injection flaws, or permission vulnerabilities were found.</p>
                    </div>
                  ) : (
                    <section className="review-detail-section">
                      <div className="review-detail-heading">
                        <div>
                          <span className="detail-icon warning">🛡️</span>
                          <div>
                            <h3>Security Findings</h3>
                            <p>Vulnerabilities and secret exposures identified in the project.</p>
                          </div>
                        </div>
                        <strong>{secCount}</strong>
                      </div>

                      <div className="review-findings">
                        {review.security?.issues?.map((issue, index) => (
                          <IssueSolutionCard
                            key={`sec-only-${index}`}
                            issue={issue}
                            categoryBadge="Security"
                          />
                        ))}
                      </div>
                    </section>
                  )}
                </>
              )}

              {/* ==============================================================
                  MODE 4: PERFORMANCE ONLY (STRICT CATEGORY ISOLATION)
                  ============================================================== */}
              {isPerformance && (
                <>
                  <section className="category-isolated-stat-hero">
                    <div className="cat-stat-box">
                      <span className="cat-stat-lbl">PERFORMANCE BOTTLENECK CONCERNS</span>
                      <strong className="cat-stat-num blue">{perfCount}</strong>
                    </div>
                    {review.score !== null && review.score !== undefined && (
                      <div className="cat-stat-box">
                        <span className="cat-stat-lbl">PERFORMANCE HEALTH SCORE</span>
                        <strong className={`cat-stat-num ${review.score >= 80 ? "green" : review.score >= 60 ? "amber" : "red"}`}>
                          {review.score} / 100
                        </strong>
                      </div>
                    )}
                    <div className="cat-stat-box">
                      <span className="cat-stat-lbl">AI CONFIDENCE</span>
                      <strong className="cat-stat-num green">
                        {review.confidence || 90}%
                      </strong>
                    </div>
                  </section>

                  {review.performance?.time_complexity && (
                    <div className="complexity-grid" style={{ marginBottom: "1.5rem" }}>
                      <div>
                        <span>TIME COMPLEXITY</span>
                        <strong>{review.performance.time_complexity}</strong>
                      </div>
                      <div>
                        <span>SPACE COMPLEXITY</span>
                        <strong>{review.performance.space_complexity || "O(1)"}</strong>
                      </div>
                    </div>
                  )}

                  {perfCount === 0 ? (
                    <div className="empty-category-card">
                      <span className="empty-icon">⚡</span>
                      <h3>Optimal Performance</h3>
                      <p>No high-complexity loops or memory bottlenecks were detected in this analysis.</p>
                    </div>
                  ) : (
                    <section className="review-detail-section">
                      <div className="review-detail-heading">
                        <div>
                          <span className="detail-icon info">⚡</span>
                          <div>
                            <h3>Performance Bottlenecks</h3>
                            <p>Algorithmic complexity and scalability concerns identified in the project.</p>
                          </div>
                        </div>
                        <strong>{perfCount}</strong>
                      </div>

                      <div className="review-findings">
                        {review.performance?.issues?.map((issue, index) => (
                          <IssueSolutionCard
                            key={`perf-only-${index}`}
                            issue={issue}
                            categoryBadge="Performance"
                          />
                        ))}
                      </div>
                    </section>
                  )}
                </>
              )}

              {/* ==============================================================
                  MODE 5: CODE QUALITY ONLY (STRICT CATEGORY ISOLATION)
                  ============================================================== */}
              {isQuality && (
                <>
                  <section className="category-isolated-stat-hero">
                    <div className="cat-stat-box">
                      <span className="cat-stat-lbl">QUALITY INSIGHTS</span>
                      <strong className="cat-stat-num purple">{qualCount}</strong>
                    </div>
                    {review.score !== null && review.score !== undefined && (
                      <div className="cat-stat-box">
                        <span className="cat-stat-lbl">CODE QUALITY HEALTH SCORE</span>
                        <strong className={`cat-stat-num ${review.score >= 80 ? "green" : review.score >= 60 ? "amber" : "red"}`}>
                          {review.score} / 100
                        </strong>
                      </div>
                    )}
                    <div className="cat-stat-box">
                      <span className="cat-stat-lbl">AI CONFIDENCE</span>
                      <strong className="cat-stat-num green">
                        {review.confidence || 90}%
                      </strong>
                    </div>
                  </section>

                  {qualCount === 0 ? (
                    <div className="empty-category-card">
                      <span className="empty-icon">✨</span>
                      <h3>High Code Quality</h3>
                      <p>The code adheres to readability, modularity, and clean coding guidelines.</p>
                    </div>
                  ) : (
                    <section className="review-detail-section">
                      <div className="review-detail-heading">
                        <div>
                          <span className="detail-icon purple">✦</span>
                          <div>
                            <h3>Code Quality & Maintainability</h3>
                            <p>Readability, architectural clarity, and refactoring opportunities.</p>
                          </div>
                        </div>
                        <strong>{qualCount}</strong>
                      </div>

                      <div className="review-findings">
                        {review.code_quality?.observations?.map((item, index) => (
                          <IssueSolutionCard
                            key={`qual-obs-${index}`}
                            issue={item}
                            categoryBadge="Quality Observation"
                          />
                        ))}
                        {review.code_quality?.suggestions?.map((item, index) => (
                          <IssueSolutionCard
                            key={`qual-sug-${index}`}
                            issue={item}
                            categoryBadge="Quality Suggestion"
                          />
                        ))}
                      </div>
                    </section>
                  )}
                </>
              )}

              {/* ================================================
                  COMPLETE CORRECTED CODE
                  ================================================ */}
              {review.corrected_code && review.corrected_code.length > 0 && (
                <section className="review-detail-section">
                  <div className="review-detail-heading">
                    <div>
                      <span className="detail-icon success">✓</span>
                      <div>
                        <h3>Complete Corrected Code</h3>
                        <p>Production-ready code with all corrections applied.</p>
                      </div>
                    </div>
                    <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                      <button
                        type="button"
                        className="btn-toolbar btn-download-code-inline"
                        onClick={handleDownloadCode}
                      >
                        📥 Download Code
                      </button>
                      <strong>
                        {review.corrected_code.length} File
                        {review.corrected_code.length !== 1 ? "s" : ""}
                      </strong>
                    </div>
                  </div>

                  <div className="corrected-code-list">
                    {review.corrected_code.map((item, idx) => (
                      <div
                        key={idx}
                        className="code-diff-card"
                        style={{ marginBottom: "1.5rem" }}
                      >
                        <div className="code-diff-header">
                          <span>📄 {item.file_name || "Refactored Code"}</span>
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
                  PROJECT DETAILS (Full Project Review only)
                  ================================================ */}
              {isFullReview && (
                <section className="review-detail-section">
                  <div className="review-detail-heading">
                    <div>
                      <span className="detail-icon info">#</span>
                      <div>
                        <h3>Project Details</h3>
                        <p>Code elements identified during analysis.</p>
                      </div>
                    </div>
                  </div>

                  <div className="project-detail-grid">
                    <div className="project-detail-box">
                      <span>FILES ANALYZED</span>
                      <strong>{safeCount(review.files_analyzed)}</strong>
                      {review.files_analyzed?.map((file, index) => (
                        <small key={`${file.path}-${index}`} title={file.path}>
                          {file.file_name}
                        </small>
                      ))}
                    </div>

                    <div className="project-detail-box">
                      <span>KEY METHODS</span>
                      <strong>{safeCount(review.key_methods)}</strong>
                      {review.key_methods?.map((method, index) => (
                        <small key={`${method}-${index}`}>{method}</small>
                      ))}
                    </div>

                    <div className="project-detail-box">
                      <span>KEY CLASSES</span>
                      <strong>{safeCount(review.key_classes)}</strong>
                      {review.key_classes?.map((item, index) => (
                        <small key={`${item}-${index}`}>{item}</small>
                      ))}
                    </div>

                    <div className="project-detail-box">
                      <span>LIBRARIES</span>
                      <strong>{safeCount(review.libraries)}</strong>
                      {review.libraries?.map((library, index) => (
                        <small key={`${library}-${index}`}>{library}</small>
                      ))}
                    </div>
                  </div>
                </section>
              )}

              {/* ================================================
                  REVIEW QUESTION FOOTER
                  ================================================ */}
              <section className="review-question-footer">
                <span>REVIEW QUESTION</span>
                <p>{review.question}</p>
              </section>

              {/* ==============================================================
                  JULES-STYLE INTERACTIVE CODE PREVIEW & DIFF
                  ============================================================== */}
              <CodeDiffPreview review={review} />

              {/* ==============================================================
                  FINAL ACTIONS: DOWNLOAD REPORT & CODE + DELIVER TO CLIENT EMAIL
                  (Positioned after all review results & final output code)
                  ============================================================== */}
              <section className="review-final-actions-section">
                <div className="final-actions-header">
                  <span className="final-actions-badge">Export & Remediation</span>
                  <h2>Download & Deliver Review Results</h2>
                  <p>
                    Export complete audit reports, download patched project archives, open an automated GitHub Pull Request, or send results via the hosted email service.
                  </p>
                </div>

                <div className="final-actions-grid">
                  {/* Multi-Format Reports */}
                  <div className="final-action-card download-card">
                    <div className="action-card-header">
                      <span className="card-icon">📄</span>
                      <div>
                        <h3>Audit Reports</h3>
                        <p>Comprehensive findings, scores & recommendations</p>
                      </div>
                    </div>
                    <div className="action-button-row">
                      <button
                        type="button"
                        className="btn-final-action"
                        onClick={() => handleDownloadReportFormat("pdf")}
                        disabled={downloadingFormat !== null}
                        title="Download publication-quality PDF audit report"
                      >
                        {downloadingFormat === "pdf" ? <span className="review-spinner-small" /> : "📕"} PDF Report
                      </button>
                      <button
                        type="button"
                        className="btn-final-action"
                        onClick={() => handleDownloadReportFormat("markdown")}
                        disabled={downloadingFormat !== null}
                        title="Download Markdown report formatted for documentation"
                      >
                        {downloadingFormat === "markdown" ? <span className="review-spinner-small" /> : "📝"} Markdown
                      </button>
                      <button
                        type="button"
                        className="btn-final-action"
                        onClick={() => handleDownloadReportFormat("html")}
                        disabled={downloadingFormat !== null}
                        title="Download standalone styled HTML report"
                      >
                        {downloadingFormat === "html" ? <span className="review-spinner-small" /> : "🌐"} HTML
                      </button>
                    </div>
                  </div>

                  {/* Code Remediation ZIPs */}
                  <div className="final-action-card download-card">
                    <div className="action-card-header">
                      <span className="card-icon">📦</span>
                      <div>
                        <h3>Corrected Code Packages</h3>
                        <p>Ready-to-run refactored archives</p>
                      </div>
                    </div>
                    <div className="action-button-row">
                      <button
                        type="button"
                        className="btn-final-action"
                        onClick={handleDownloadFullZip}
                        disabled={downloadingZip}
                        title="Download full project archive with all corrections applied"
                      >
                        {downloadingZip ? <span className="review-spinner-small" /> : "📦"} Full Project ZIP
                      </button>
                      <button
                        type="button"
                        className="btn-final-action"
                        onClick={handleDownloadCorrectedOnlyZip}
                        disabled={downloadingZip}
                        title="Download only the modified and corrected files"
                      >
                        {downloadingZip ? <span className="review-spinner-small" /> : "📁"} Patched Files ZIP
                      </button>
                    </div>
                  </div>

                  {/* GitHub Pull Request */}
                  <div className="final-action-card github-card">
                    <div className="action-card-header">
                      <span className="card-icon">🐙</span>
                      <div>
                        <h3>GitHub Pull Request</h3>
                        <p>Automate branch creation & PR merge review</p>
                      </div>
                    </div>
                    <div className="github-action-content">
                      <button
                        type="button"
                        onClick={handlePushGitHubPR}
                        disabled={pushingPR}
                        title="Commit fixes to a new branch and open a GitHub Pull Request"
                        className="btn-final-action github-pr-button"
                      >
                        {pushingPR ? (
                          <>
                            <span className="review-spinner-small" /> Creating PR on GitHub...
                          </>
                        ) : (
                          "🚀 Create Branch & Pull Request"
                        )}
                      </button>
                      <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "8px", marginBottom: 0 }}>
                        Commits patched files to <code>ai-review/fix-*</code> and opens a PR for your team.
                      </p>
                    </div>
                  </div>

                  {/* Email Delivery */}
                  <div className="final-action-card email-card">
                    <div className="action-card-header">
                      <span className="card-icon">📧</span>
                      <div>
                        <h3>Deliver to Client Email</h3>
                        <p>Send report and corrected files via Hosted Mail API</p>
                      </div>
                    </div>

                    <div className="email-input-wrapper">
                      <input
                        type="email"
                        className="final-email-input"
                        placeholder="client@company.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        disabled={sendingEmail}
                      />
                      <button
                        type="button"
                        className="btn-final-send"
                        onClick={handleSendEmail}
                        disabled={sendingEmail}
                      >
                        {sendingEmail ? (
                          <>
                            <span className="review-spinner-small" /> Sending...
                          </>
                        ) : (
                          "Send Report"
                        )}
                      </button>
                    </div>

                    {emailStatus && (
                      <div
                        className={`email-status-banner ${
                          emailStatus.success ? "status-success" : "status-error"
                        }`}
                        style={{ marginTop: "12px" }}
                      >
                        <div className="status-banner-content">
                          <span className="status-icon">
                            {emailStatus.success ? "✓" : "!"}
                          </span>
                          <span className="status-text">{emailStatus.message}</span>
                        </div>
                        <button
                          type="button"
                          className="status-close-btn"
                          onClick={() => setEmailStatus(null)}
                        >
                          ✕
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </section>

            </section>
          );
        })()}

        </>
        )}

      </div>

      {prResult && (
        <div className="jules-modal-backdrop" onClick={() => setPrResult(null)}>
          <div className="jules-modal-content" onClick={(event) => event.stopPropagation()}>
            <div className="jules-modal-icon">🎉</div>
            <h3>Pull Request Created Successfully!</h3>
            <p>
              Your accepted corrections have been committed to a dedicated branch and an official Pull Request has been opened on GitHub.
            </p>

            <div className="jules-pr-details-box">
              <div><strong>Branch:</strong> <code>{prResult.branch}</code></div>
              <div><strong>Files Changed:</strong> {prResult.files_changed} file(s)</div>
              <div><strong>PR Number:</strong> #{prResult.pr_number}</div>
            </div>

            <div className="jules-modal-actions">
              <a
                href={prResult.html_url}
                target="_blank"
                rel="noreferrer"
                className="btn-primary"
                style={{ textDecoration: "none" }}
              >
                View Pull Request on GitHub ↗
              </a>
              <button type="button" className="btn-secondary" onClick={() => setPrResult(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

export default Review;
