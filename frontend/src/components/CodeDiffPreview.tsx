import React, { useState, useMemo } from "react";
import { createPortal } from "react-dom";
import { refineReviewFix, fetchGitHubStatus, pushGitHubFix } from "../api";

export interface DiffItem {
  id: string;
  file: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  category: string;
  beforeCode: string;
  afterCode: string;
  explanation: string;
  accepted: boolean;
  refinePrompt?: string;
  isRefining?: boolean;
}

interface CodeDiffPreviewProps {
  review: any;
  onPushSuccess?: (prData: any) => void;
}

export const CodeDiffPreview: React.FC<CodeDiffPreviewProps> = ({ review, onPushSuccess }) => {
  // Extract all file changes from review findings
  const initialDiffItems = useMemo<DiffItem[]>(() => {
    if (!review) return [];

    const items: DiffItem[] = [];
    const seen = new Set<string>();

    // 1. Check review.corrected_code
    if (Array.isArray(review.corrected_code)) {
      review.corrected_code.forEach((c: any, idx: number) => {
        const path = c.file_name || c.file || `file_${idx + 1}.py`;
        const code = c.code || c.content || "";
        if (code && !seen.has(path)) {
          seen.add(path);
          items.push({
            id: `corr-${idx}`,
            file: path,
            title: `Refactored & Grounded Correction for ${path}`,
            severity: "high",
            category: "Full Correction",
            beforeCode: c.original_code || "// Original source snippet",
            afterCode: code,
            explanation: c.explanation || "Automated architectural refactoring & bug remediation.",
            accepted: true
          });
        }
      });
    }

    // 2. Check specialist issues (bugs, security, performance, quality)
    const allIssues = (review.bugs || [])
      .concat(review.errors || [])
      .concat(review.security?.issues || [])
      .concat(review.performance?.issues || [])
      .concat(review.code_quality?.observations || [])
      .concat(review.detected_issues || []);

    allIssues.forEach((issue: any, idx: number) => {
      const path = issue.file || "source_file.py";
      const before = issue.before_code || "";
      const after = issue.after_code || issue.corrected_code || issue.suggested_solution || "";

      // Add if it has a code correction and haven't already included this exact fix
      const key = `${path}::${issue.title || idx}`;
      if (after && after.trim() && !seen.has(key)) {
        seen.add(key);
        items.push({
          id: `issue-${idx}`,
          file: path,
          title: issue.title || `Issue in ${path}`,
          severity: (issue.severity || "medium").toLowerCase() as any,
          category: issue.category || "Issue Fix",
          beforeCode: before.trim() || "// Original issue location",
          afterCode: after.trim(),
          explanation: issue.explanation || issue.suggested_solution || issue.description || "Resolved detected flaw.",
          accepted: true
        });
      }
    });

    return items;
  }, [review]);

  const [diffItems, setDiffItems] = useState<DiffItem[]>(initialDiffItems);
  const [activeRefineId, setActiveRefineId] = useState<string | null>(null);
  const [refineInputs, setRefineInputs] = useState<Record<string, string>>({});
  const [refiningMap, setRefiningMap] = useState<Record<string, boolean>>({});

  // Push / PR state
  const [pushing, setPushing] = useState(false);
  const [baseBranch, setBaseBranch] = useState("main");
  const [prResult, setPrResult] = useState<{
    html_url: string;
    pr_number: number;
    branch: string;
    files_changed: number;
  } | null>(null);

  const acceptedCount = diffItems.filter((i) => i.accepted).length;

  const toggleAccept = (id: string) => {
    setDiffItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, accepted: !item.accepted } : item))
    );
  };

  const handleRefineSubmit = async (item: DiffItem) => {
    const instruction = refineInputs[item.id]?.trim();
    if (!instruction) return;

    setRefiningMap((prev) => ({ ...prev, [item.id]: true }));
    try {
      const res = await refineReviewFix({
        file_name: item.file,
        before_code: item.beforeCode,
        current_fix: item.afterCode,
        instruction
      });

      if (res.data?.success && res.data.corrected_code) {
        setDiffItems((prev) =>
          prev.map((i) =>
            i.id === item.id
              ? {
                  ...i,
                  afterCode: res.data.corrected_code,
                  explanation: `${i.explanation} (Refined: ${instruction})`
                }
              : i
          )
        );
        setActiveRefineId(null);
        setRefineInputs((prev) => ({ ...prev, [item.id]: "" }));
      }
    } catch (err: any) {
      alert(err.response?.data?.detail || "Could not refine code fix. Please try again.");
    } finally {
      setRefiningMap((prev) => ({ ...prev, [item.id]: false }));
    }
  };

  const handleAcceptAndPush = async () => {
    const acceptedFiles = diffItems.filter((i) => i.accepted);
    if (acceptedFiles.length === 0) {
      alert("Please accept at least one change before creating a Pull Request.");
      return;
    }

    setPushing(true);
    try {
      const statusRes = await fetchGitHubStatus();
      if (!statusRes.data?.connected) {
        alert("Please connect your GitHub account via GitHub App in Configuration first.");
        return;
      }

      const filesPayload = acceptedFiles.map((f) => ({
        path: f.file,
        code: f.afterCode
      }));

      // Extract repo name safely (could be review.project?.name or review.project_name)
      let repoName = review.project?.name || review.project_name || "project";
      if (repoName.includes("/")) {
        repoName = repoName.split("/").pop() || repoName;
      }

      // Call API push-fix via pushGitHubFix helper
      const res = await pushGitHubFix({
        owner: statusRes.data.username,
        repo: repoName,
        base_branch: baseBranch || "main",
        corrected_files: filesPayload,
        pr_title: `AI Code Review: Verified Fixes (${acceptedFiles.length} files)`,
        pr_body: `## 🤖 CodeReview AI — Accepted Fixes\n\nThe following **${acceptedFiles.length}** code corrections were reviewed and accepted:\n\n${acceptedFiles
          .map((f) => `- **\`${f.file}\`**: ${f.title} (${f.severity.toUpperCase()})`)
          .join("\n")}\n\n---\n*Prepared by CodeReview AI.*`
      });

      const data = res.data;
      if (data?.html_url) {
        setPrResult({
          html_url: data.html_url,
          pr_number: data.pr_number,
          branch: data.branch,
          files_changed: acceptedFiles.length
        });
        if (onPushSuccess) onPushSuccess(data);
      } else {
        alert(data?.detail || "Failed to create GitHub Pull Request.");
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || e.message || "Failed to push fixes to GitHub.");
    } finally {
      setPushing(false);
    }
  };

  if (diffItems.length === 0) {
    return null;
  }

  return (
    <section className="jules-diff-container">
      {/* Header */}
      <div className="jules-diff-header">
        <div className="jules-header-left">
          <span className="jules-logo-badge">🤖 CodeReview AI Fixes</span>
          <h2>Interactive Code Preview & Diff</h2>
          <p>
            Inspect proposed corrections before committing. Accept or reject specific changes, or ask the AI agent to modify them.
          </p>
        </div>
        <div className="jules-header-status-pills">
          <span className="jules-status-pill green">✓ Repository Analyzed</span>
          <span className="jules-status-pill green">✓ Bugs & Vulnerabilities Identified</span>
          <span className="jules-status-pill purple">✓ Proposed Corrections Ready</span>
        </div>
      </div>

      {/* Diff items list */}
      <div className="jules-diff-list">
        {diffItems.map((item) => {
          const isRefining = refiningMap[item.id] || false;
          const isFormOpen = activeRefineId === item.id;

          const beforeLines = item.beforeCode.split("\n");
          const afterLines = item.afterCode.split("\n");

          return (
            <div key={item.id} className={`jules-diff-card ${item.accepted ? "is-accepted" : "is-rejected"}`}>
              {/* Card Header */}
              <div className="jules-card-topbar">
                <div className="jules-file-info">
                  <span className="jules-file-icon">📄</span>
                  <span className="jules-file-name">{item.file}</span>
                  <span className={`jules-severity-tag severity-${item.severity}`}>{item.severity}</span>
                  <span className="jules-category-tag">{item.category}</span>
                </div>

                <div className="jules-actions-group">
                  <button
                    type="button"
                    className={`btn-jules-action ${item.accepted ? "btn-accepted" : "btn-unaccepted"}`}
                    onClick={() => toggleAccept(item.id)}
                    title={item.accepted ? "Accepted to commit" : "Excluded from commit"}
                  >
                    {item.accepted ? "✓ Accepted" : "✕ Rejected"}
                  </button>

                  <button
                    type="button"
                    className="btn-jules-action btn-modify"
                    onClick={() => setActiveRefineId(isFormOpen ? null : item.id)}
                  >
                    💬 Ask AI to Modify
                  </button>
                </div>
              </div>

              {/* Title & Explanation */}
              <div className="jules-card-details">
                <strong>{item.title}</strong>
                <p>{item.explanation}</p>
              </div>

              {/* Inline AI Refinement Box */}
              {isFormOpen && (
                <div className="jules-refine-box">
                  <div className="jules-refine-label">
                    <span>✨</span> Give instruction to modify this code fix:
                  </div>
                  <div className="jules-refine-inputs">
                    <input
                      type="text"
                      placeholder="e.g. Use a guard clause, keep backward compatibility, or use async/await..."
                      value={refineInputs[item.id] || ""}
                      onChange={(e) =>
                        setRefineInputs((prev) => ({ ...prev, [item.id]: e.target.value }))
                      }
                      onKeyDown={(e) => {
                        if (e.key === "Enter") handleRefineSubmit(item);
                      }}
                      disabled={isRefining}
                    />
                    <button
                      type="button"
                      className="btn-primary"
                      onClick={() => handleRefineSubmit(item)}
                      disabled={isRefining || !refineInputs[item.id]?.trim()}
                    >
                      {isRefining ? "Refining..." : "Refine Fix"}
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      onClick={() => setActiveRefineId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Visual Diff Comparison Box */}
              <div className="jules-diff-box">
                <div className="diff-panel before-panel">
                  <div className="diff-panel-title">
                    <span className="diff-badge red">-</span> Original Code
                  </div>
                  <pre className="diff-code">
                    {beforeLines.map((line, lIdx) => (
                      <div key={lIdx} className="diff-line diff-del">
                        <span className="diff-line-num">{lIdx + 1}</span>
                        <span className="diff-line-marker">-</span>
                        <span className="diff-line-text">{line || " "}</span>
                      </div>
                    ))}
                  </pre>
                </div>

                <div className="diff-panel after-panel">
                  <div className="diff-panel-title">
                    <span className="diff-badge green">+</span> Proposed AI Fix
                  </div>
                  <pre className="diff-code">
                    {afterLines.map((line, lIdx) => (
                      <div key={lIdx} className="diff-line diff-add">
                        <span className="diff-line-num">{lIdx + 1}</span>
                        <span className="diff-line-marker">+</span>
                        <span className="diff-line-text">{line || " "}</span>
                      </div>
                    ))}
                  </pre>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Review Footer Summary & PR Trigger */}
      <div className="jules-diff-footer">
        <div className="jules-footer-left">
          <div className="jules-selection-summary">
            <strong>{acceptedCount} of {diffItems.length}</strong> changes accepted for Pull Request
          </div>
          <div className="jules-target-branch">
            Target: <code>main</code> branch · Creates separate branch: <code>ai-review/fix-*</code>
          </div>
        </div>

        <div className="jules-footer-right">
          <button
            type="button"
            className="btn-jules-push"
            onClick={handleAcceptAndPush}
            disabled={pushing || acceptedCount === 0}
          >
            {pushing ? (
              <>
                <span className="review-spinner-small" /> Creating Branch & Pull Request...
              </>
            ) : (
              <>
                <span>🚀</span> Accept Changes & Push to GitHub (Open PR)
              </>
            )}
          </button>
        </div>
      </div>

      {/* Celebratory Pull Request Success Modal */}
      {prResult && createPortal((
        <div className="jules-modal-backdrop" onClick={() => setPrResult(null)}>
          <div className="jules-modal-content" onClick={(e) => e.stopPropagation()}>
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
              <button
                type="button"
                className="btn-secondary"
                onClick={() => setPrResult(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      ), document.body)}
    </section>
  );
};

export default CodeDiffPreview;
