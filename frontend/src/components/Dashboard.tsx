import { useEffect, useMemo, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";
import { useAppAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import ReviewModal from "./ReviewModal";

export interface HistoryReview {
  id: string;
  projectName: string;
  language: string;
  question: string;
  issueCount: number;
  bugs: number;
  security: number;
  performance: number;
  quality: number;
  score: number | null;
  confidence: number;
  createdAt: string;
  review?: any;
}

export interface UploadedFileItem {
  id: string;
  file_name: string;
  file_size: number;
  file_type: string;
  upload_time: string;
}

function Dashboard() {
  const navigate = useNavigate();
  const { user, isClerkConfigured } = useAppAuth();
  const { theme, setTheme, themes } = useTheme();

  const [activeTab, setActiveTab] = useState<"overview" | "reviews" | "files" | "settings">("overview");
  const [history, setHistory] = useState<HistoryReview[]>([]);
  const [files, setFiles] = useState<UploadedFileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedReview, setSelectedReview] = useState<HistoryReview | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  /* ==========================================================
     LOAD HISTORY & FILES FROM SQLITE (with localStorage fallback)
     ========================================================== */

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      // 1. Fetch reviews from backend SQLite
      let dbReviews: HistoryReview[] = [];
      try {
        const res = await API.get("/api/reviews");
        if (res.data?.success && Array.isArray(res.data.reviews)) {
          dbReviews = res.data.reviews.map((r: any) => ({
            id: r.id,
            projectName: r.project_name || "Code Review",
            language: r.language || "Multi-language",
            question: r.question,
            issueCount: r.issue_count ?? 0,
            bugs: r.bugs_count ?? 0,
            security: r.security_count ?? 0,
            performance: r.performance_count ?? 0,
            quality: r.quality_count ?? 0,
            score: r.score ?? null,
            confidence: r.confidence ?? 90,
            createdAt: r.created_at,
            review: r.review || {}
          }));
        }
      } catch (err) {
        console.warn("Could not fetch reviews from SQLite API, using local storage cache:", err);
      }

      // Read local storage as well to guarantee no lost data
      const stored = localStorage.getItem("codeReviewHistory");
      const localReviews: HistoryReview[] = stored ? JSON.parse(stored) : [];

      // Combine uniquely by id
      const map = new Map<string, HistoryReview>();
      dbReviews.forEach((item) => map.set(item.id, item));
      localReviews.forEach((item) => {
        if (!map.has(item.id)) {
          map.set(item.id, item);
        }
      });

      const merged = Array.from(map.values()).sort(
        (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
      setHistory(merged);

      // 2. Fetch uploaded files from SQLite
      try {
        const filesRes = await API.get("/api/files");
        if (filesRes.data?.success && Array.isArray(filesRes.data.files)) {
          setFiles(filesRes.data.files);
        }
      } catch (fErr) {
        console.warn("Could not fetch uploaded files from SQLite:", fErr);
      }
    } catch (e) {
      console.error("Dashboard data load error:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  /* ==========================================================
     DELETE SINGLE REVIEW
     ========================================================== */

  const handleDeleteReview = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this review record?")) return;

    try {
      await API.delete(`/api/reviews/${id}`).catch(() => {});
    } catch (err) {
      console.warn("API delete notice:", err);
    }

    const updated = history.filter((h) => h.id !== id);
    setHistory(updated);
    localStorage.setItem("codeReviewHistory", JSON.stringify(updated));
    showNotice("Review record deleted successfully.");
  };

  /* ==========================================================
     CLEAR ALL REVIEWS
     ========================================================== */

  const handleClearAll = async () => {
    if (!window.confirm("Are you sure you want to clear your entire review history? This cannot be undone.")) return;

    try {
      await API.delete("/api/reviews").catch(() => {});
    } catch (err) {
      console.warn("API clear notice:", err);
    }

    setHistory([]);
    localStorage.removeItem("codeReviewHistory");
    showNotice("All review history cleared.");
  };

  /* ==========================================================
     DELETE UPLOADED FILE
     ========================================================== */

  const handleDeleteFile = async (id: string) => {
    if (!window.confirm("Delete this uploaded file record?")) return;

    try {
      await API.delete(`/api/files/${id}`);
      setFiles((prev) => prev.filter((f) => f.id !== id));
      showNotice("Uploaded file record deleted.");
    } catch (err) {
      console.error("Failed to delete file:", err);
      showNotice("Failed to delete file record.");
    }
  };

  const showNotice = (msg: string) => {
    setActionNotice(msg);
    setTimeout(() => setActionNotice(null), 4000);
  };

  /* ==========================================================
     STATISTICS
     ========================================================== */

  const statistics = useMemo(() => {
    const totalReviews = history.length;
    const bugs = history.reduce((total, item) => total + (item.bugs || 0), 0);
    const security = history.reduce((total, item) => total + (item.security || 0), 0);
    const performance = history.reduce((total, item) => total + (item.performance || 0), 0);
    const quality = history.reduce((total, item) => total + (item.quality || 0), 0);
    const totalIssues = history.reduce((total, item) => total + (item.issueCount || 0), 0);

    const scoredReviews = history.filter((item) => typeof item.score === "number");
    const averageScore =
      scoredReviews.length > 0
        ? Math.round(scoredReviews.reduce((total, item) => total + (item.score || 0), 0) / scoredReviews.length)
        : null;

    const averageConfidence =
      totalReviews > 0
        ? Math.round(history.reduce((total, item) => total + (item.confidence || 0), 0) / totalReviews)
        : 92;

    return {
      totalReviews,
      bugs,
      security,
      performance,
      quality,
      totalIssues,
      averageScore,
      averageConfidence,
    };
  }, [history]);

  const filteredReviews = useMemo(() => {
    if (!searchQuery.trim()) return history;
    const q = searchQuery.toLowerCase();
    return history.filter(
      (r) =>
        r.projectName.toLowerCase().includes(q) ||
        r.question.toLowerCase().includes(q) ||
        r.language.toLowerCase().includes(q)
    );
  }, [history, searchQuery]);

  const formatDate = (dateString: string) => {
    try {
      return new Intl.DateTimeFormat("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(dateString));
    } catch {
      return "Recent";
    }
  };

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <main className="dashboard-page-modern">
      <div className="container">
        {/* Notice alert */}
        {actionNotice && (
          <div className="dashboard-notification-banner">
            <span>✓ {actionNotice}</span>
          </div>
        )}

        {/* HEADER */}
        <section className="dashboard-header">
          <div>
            <div className="section-label">AUTHENTICATED WORKSPACE</div>
            <h1>Developer Dashboard</h1>
            <p>
              Welcome back, <strong>{user?.fullName || user?.email || "Developer"}</strong>. Manage your code reviews, inspect previous reports, and review uploaded codebase files.
            </p>
          </div>

          <div className="header-action-buttons">
            <button
              className="dashboard-review-button"
              onClick={() => navigate("/review")}
            >
              <span>✦</span> New Review <span>→</span>
            </button>
          </div>
        </section>

        {/* NAVIGATION TABS */}
        <div className="dashboard-nav-tabs">
          <button
            className={`dash-tab ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            📊 Analytics & Overview
          </button>
          <button
            className={`dash-tab ${activeTab === "reviews" ? "active" : ""}`}
            onClick={() => setActiveTab("reviews")}
          >
            📋 Previous Reviews ({history.length})
          </button>
          <button
            className={`dash-tab ${activeTab === "files" ? "active" : ""}`}
            onClick={() => setActiveTab("files")}
          >
            📁 Uploaded Files ({files.length})
          </button>
          <button
            className={`dash-tab ${activeTab === "settings" ? "active" : ""}`}
            onClick={() => setActiveTab("settings")}
          >
            ⚙️ Profile & Themes
          </button>
        </div>

        {/* TAB 1: OVERVIEW */}
        {activeTab === "overview" && (
          <div className="dashboard-tab-content">
            {/* STATS GRID */}
            <section className="dashboard-stats">
              <article className="dashboard-stat-card">
                <div className="stat-card-top">
                  <span>TOTAL REVIEWS</span>
                  <div className="stat-icon purple">◈</div>
                </div>
                <strong>{statistics.totalReviews}</strong>
                <small>sessions indexed in SQLite</small>
              </article>

              <article className="dashboard-stat-card">
                <div className="stat-card-top">
                  <span>BUGS FOUND</span>
                  <div className="stat-icon red">!</div>
                </div>
                <strong className="red-value">{statistics.bugs}</strong>
                <small>bugs & errors detected</small>
              </article>

              <article className="dashboard-stat-card">
                <div className="stat-card-top">
                  <span>SECURITY</span>
                  <div className="stat-icon amber">⚠</div>
                </div>
                <strong className="amber-value">{statistics.security}</strong>
                <small>vulnerabilities reported</small>
              </article>

              <article className="dashboard-stat-card">
                <div className="stat-card-top">
                  <span>AVG SCORE</span>
                  <div className="stat-icon green">★</div>
                </div>
                <strong className="green-value">
                  {statistics.averageScore !== null ? `${statistics.averageScore}%` : "N/A"}
                </strong>
                <small>code health index</small>
              </article>
            </section>

            {/* QUICK ACTIONS & RECENT ACTIVITY */}
            <section className="dashboard-panels-grid">
              <div className="dashboard-panel">
                <div className="panel-header">
                  <h3>⚡ Quick Actions</h3>
                </div>
                <div className="quick-actions-list">
                  <div className="quick-action-item" onClick={() => navigate("/review")}>
                    <div className="action-icon">🔍</div>
                    <div className="action-meta">
                      <strong>Start Code Analysis</strong>
                      <span>Submit prompts or check for bugs & security flaws</span>
                    </div>
                    <span className="action-arrow">→</span>
                  </div>

                  <div className="quick-action-item" onClick={() => navigate("/")}>
                    <div className="action-icon">📤</div>
                    <div className="action-meta">
                      <strong>Upload Codebase / ZIP</strong>
                      <span>Index multiple source files or repositories into FAISS</span>
                    </div>
                    <span className="action-arrow">→</span>
                  </div>

                  <div className="quick-action-item" onClick={() => navigate("/themes")}>
                    <div className="action-icon">🎨</div>
                    <div className="action-meta">
                      <strong>Customize Workspace Theme</strong>
                      <span>Select Dark, Light, Purple Lavender, or Emerald Green</span>
                    </div>
                    <span className="action-arrow">→</span>
                  </div>
                </div>
              </div>

              <div className="dashboard-panel">
                <div className="panel-header">
                  <h3>🕒 Recent Reviews</h3>
                  <button className="panel-sub-btn" onClick={() => setActiveTab("reviews")}>
                    View All ({history.length})
                  </button>
                </div>

                {history.length === 0 ? (
                  <div className="panel-empty-state">
                    <p>No reviews analyzed yet.</p>
                    <button className="btn-primary" onClick={() => navigate("/review")}>
                      Run Your First Review
                    </button>
                  </div>
                ) : (
                  <div className="recent-reviews-stream">
                    {history.slice(0, 4).map((rev) => (
                      <div
                        key={rev.id}
                        className="recent-review-row"
                        onClick={() => setSelectedReview(rev)}
                      >
                        <div className="row-left">
                          <span className="row-proj-name">{rev.projectName}</span>
                          <span className="row-question">"{rev.question}"</span>
                        </div>
                        <div className="row-right">
                          <span className="row-date">{formatDate(rev.createdAt)}</span>
                          <button
                            type="button"
                            className="btn-reopen-mini"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedReview(rev);
                            }}
                          >
                            Reopen ↗
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          </div>
        )}

        {/* TAB 2: PREVIOUS REVIEWS */}
        {activeTab === "reviews" && (
          <div className="dashboard-tab-content">
            <div className="reviews-filter-bar">
              <input
                type="text"
                placeholder="Search reviews by project name, language, or question..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="reviews-search-input"
              />
              {history.length > 0 && (
                <button className="btn-danger-outline" onClick={handleClearAll}>
                  🗑️ Clear All Reviews
                </button>
              )}
            </div>

            {filteredReviews.length === 0 ? (
              <div className="reviews-empty-box">
                <div className="empty-icon">📂</div>
                <h3>No Review Records Found</h3>
                <p>
                  {searchQuery
                    ? "No reviews matched your search criteria."
                    : "You haven't run any code reviews yet. Start by analyzing a file or project."}
                </p>
                <button className="btn-primary" onClick={() => navigate("/review")}>
                  Analyze Code Now
                </button>
              </div>
            ) : (
              <div className="reviews-cards-list">
                {filteredReviews.map((item) => (
                  <div
                    key={item.id}
                    className="review-history-card"
                    onClick={() => setSelectedReview(item)}
                  >
                    <div className="card-top-row">
                      <div className="card-title-group">
                        <span className="card-proj-name">{item.projectName}</span>
                        <span className="lang-tag">{item.language}</span>
                      </div>

                      <div className="card-metrics-group">
                        {item.score !== null && (
                          <span className="score-pill">
                            ★ Score: {item.score}/100
                          </span>
                        )}
                        <span className="date-text">{formatDate(item.createdAt)}</span>
                      </div>
                    </div>

                    <div className="card-question-box">
                      <strong>Question:</strong> {item.question}
                    </div>

                    <div className="card-issues-row">
                      <span className="issue-chip red">🐞 {item.bugs} Bugs</span>
                      <span className="issue-chip amber">🛡️ {item.security} Security</span>
                      <span className="issue-chip blue">⚡ {item.performance} Perf</span>
                      <span className="issue-chip green">✨ {item.quality} Quality</span>
                    </div>

                    <div className="card-bottom-actions">
                      <button
                        type="button"
                        className="btn-reopen-primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedReview(item);
                        }}
                      >
                        🔍 Reopen Past Review
                      </button>

                      <button
                        type="button"
                        className="btn-delete-icon"
                        onClick={(e) => handleDeleteReview(item.id, e)}
                        title="Delete Review"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: UPLOADED FILES */}
        {activeTab === "files" && (
          <div className="dashboard-tab-content">
            <div className="files-section-header">
              <div>
                <h3>User Uploaded Files</h3>
                <p>All source code files and ZIP archives stored and indexed in SQLite.</p>
              </div>
              <button className="btn-primary" onClick={() => navigate("/")}>
                Upload New Files 📤
              </button>
            </div>

            {files.length === 0 ? (
              <div className="files-empty-box">
                <div className="empty-icon">📁</div>
                <h3>No Uploaded Files Yet</h3>
                <p>When you upload ZIP projects or source files, they are safely registered and tracked here.</p>
                <button className="btn-primary" onClick={() => navigate("/")}>
                  Go to Project Uploader
                </button>
              </div>
            ) : (
              <div className="files-table-wrapper">
                <table className="files-table">
                  <thead>
                    <tr>
                      <th>File Name</th>
                      <th>Type</th>
                      <th>Size</th>
                      <th>Uploaded Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {files.map((file) => (
                      <tr key={file.id}>
                        <td className="file-name-cell">
                          <span className="file-icon">
                            {file.file_type === "zip" ? "📦" : "📄"}
                          </span>
                          <span>{file.file_name}</span>
                        </td>
                        <td>
                          <span className="type-badge">
                            {file.file_type || "code"}
                          </span>
                        </td>
                        <td>{formatFileSize(file.file_size)}</td>
                        <td>{formatDate(file.upload_time)}</td>
                        <td>
                          <div className="file-actions">
                            <button
                              type="button"
                              className="btn-analyze-mini"
                              onClick={() => navigate("/review")}
                            >
                              Analyze
                            </button>
                            <button
                              type="button"
                              className="btn-delete-mini"
                              onClick={() => handleDeleteFile(file.id)}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: PROFILE & SETTINGS */}
        {activeTab === "settings" && (
          <div className="dashboard-tab-content">
            <div className="settings-grid">
              {/* Profile Card */}
              <div className="settings-card">
                <h3>👤 Profile Information</h3>
                <p className="card-sub">Authenticated details linked via Clerk.</p>

                <div className="profile-display-box">
                  {user?.imageUrl ? (
                    <img src={user.imageUrl} alt="Avatar" className="profile-large-avatar" />
                  ) : (
                    <div className="profile-large-placeholder">
                      {(user?.fullName || user?.email || "U")[0].toUpperCase()}
                    </div>
                  )}

                  <div className="profile-meta-fields">
                    <div className="field-group">
                      <label>Full Name</label>
                      <span className="field-value">{user?.fullName || "Developer"}</span>
                    </div>

                    <div className="field-group">
                      <label>Email Address</label>
                      <span className="field-value">{user?.email || "No email"}</span>
                    </div>

                    <div className="field-group">
                      <label>Clerk User ID</label>
                      <span className="field-value mono">{user?.id || "Local User"}</span>
                    </div>

                    <div className="field-group">
                      <label>Authentication Provider</label>
                      <span className="field-value">
                        {isClerkConfigured ? "Clerk Security Cloud" : "Local Developer Session"}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Theme Preference Settings */}
              <div className="settings-card">
                <h3>🎨 Workspace Theme Preference</h3>
                <p className="card-sub">Select your active visual theme. Persists across browser refreshes and syncs to SQLite.</p>

                <div className="themes-quick-selector">
                  {themes.map((t) => {
                    const isSelected = theme === t.id;
                    return (
                      <div
                        key={t.id}
                        className={`theme-pill-select ${isSelected ? "selected" : ""}`}
                        onClick={() => setTheme(t.id)}
                      >
                        <span className="theme-color-dot" style={{ backgroundColor: t.primaryColor }}></span>
                        <div>
                          <strong>{t.name}</strong>
                          <span className="theme-pill-sub">{t.subtitle}</span>
                        </div>
                        {isSelected && <span className="check-mark">✓</span>}
                      </div>
                    );
                  })}
                </div>

                <div style={{ marginTop: "16px" }}>
                  <button className="btn-secondary" onClick={() => navigate("/themes")}>
                    Open Full Themes Customizer →
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* REOPEN PAST REVIEW MODAL */}
      {selectedReview && (
        <ReviewModal
          reviewData={selectedReview}
          onClose={() => setSelectedReview(null)}
        />
      )}
    </main>
  );
}

export default Dashboard;