import { useEffect, useState, useCallback, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";
import { useAppAuth } from "../context/AuthContext";
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
  const { user } = useAppAuth();

  const [activeTab, setActiveTab] = useState<"overview" | "reviews" | "files">("overview");
  const [history, setHistory] = useState<HistoryReview[]>([]);
  const [files, setFiles] = useState<UploadedFileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedReview, setSelectedReview] = useState<HistoryReview | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

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
            review: r.review || {},
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

  const handleDeleteReview = async (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!window.confirm("Delete this review from history?")) return;

    try {
      await API.delete(`/api/reviews/${id}`);
    } catch (err) {
      console.warn("Could not delete from SQLite API:", err);
    }

    const updated = history.filter((item) => item.id !== id);
    setHistory(updated);
    localStorage.setItem("codeReviewHistory", JSON.stringify(updated));
  };

  const handleDeleteFile = async (id: string) => {
    if (!window.confirm("Delete this file record?")) return;
    try {
      await API.delete(`/api/files/${id}`);
      setFiles((prev) => prev.filter((f) => f.id !== id));
    } catch (err) {
      console.warn("Could not delete file:", err);
    }
  };

  // Real statistics derived purely from actual live data
  const stats = useMemo(() => {
    const totalReviews = history.length;
    const totalFiles = files.length;
    const totalIssues = history.reduce((sum, r) => sum + (r.issueCount || 0), 0);
    const validScores = history.filter((r) => r.score !== null).map((r) => r.score as number);
    const avgScore = validScores.length > 0 ? Math.round(validScores.reduce((a, b) => a + b, 0) / validScores.length) : null;

    return {
      totalReviews,
      totalFiles,
      totalIssues,
      avgScore,
    };
  }, [history, files]);

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

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1024 / 1024).toFixed(2) + " MB";
  };

  const formatDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <main className="dashboard-container">
      <div className="dashboard-header">
        <div>
          <h1>Workspace Dashboard</h1>
          <p style={{ color: "var(--text-secondary)", marginTop: "4px" }}>
            Welcome back{user?.fullName ? `, ${user.fullName}` : ""}. Track your audits, files, and health scores.
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button className="btn-secondary" onClick={() => navigate("/configuration")}>
            ⚙️ Configuration
          </button>
          <button className="btn-primary" onClick={() => navigate("/review")}>
            + Run New Review
          </button>
        </div>
      </div>

      {/* REAL DATA STATS CARDS */}
      <div className="dashboard-stats-grid">
        <div className="stat-card">
          <div className="stat-num">{stats.totalReviews}</div>
          <div className="stat-label">Total Completed Reviews</div>
        </div>

        <div className="stat-card">
          <div className="stat-num">{stats.totalIssues}</div>
          <div className="stat-label">Detected Issues Flagged</div>
        </div>

        <div className="stat-card">
          <div className="stat-num">
            {stats.avgScore !== null ? `${stats.avgScore}/100` : "—"}
          </div>
          <div className="stat-label">Average Code Health Score</div>
        </div>

        <div className="stat-card">
          <div className="stat-num">{stats.totalFiles}</div>
          <div className="stat-label">Indexed Files Tracked</div>
        </div>
      </div>

      {/* DASHBOARD TABS */}
      <div className="dashboard-tabs">
        <button
          type="button"
          className={`dash-tab-btn ${activeTab === "overview" ? "active" : ""}`}
          onClick={() => setActiveTab("overview")}
        >
          📊 Activity Overview
        </button>
        <button
          type="button"
          className={`dash-tab-btn ${activeTab === "reviews" ? "active" : ""}`}
          onClick={() => setActiveTab("reviews")}
        >
          📝 Past Reviews ({history.length})
        </button>
        <button
          type="button"
          className={`dash-tab-btn ${activeTab === "files" ? "active" : ""}`}
          onClick={() => setActiveTab("files")}
        >
          📁 Uploaded Files ({files.length})
        </button>
      </div>

      {/* TAB 1: OVERVIEW */}
      {activeTab === "overview" && (
        <div>
          {history.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🚀</div>
              <h3>No Reviews Executed Yet</h3>
              <p>Upload a project ZIP, source files, or connect your GitHub repository to generate your first audit.</p>
              <button className="btn-primary" onClick={() => navigate("/")}>
                Upload Project Now →
              </button>
            </div>
          ) : (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h3 style={{ fontSize: "18px" }}>Recent Review Activity</h3>
                <button className="btn-secondary" onClick={() => setActiveTab("reviews")}>
                  View All ({history.length}) →
                </button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
                {history.slice(0, 5).map((rev) => (
                  <div
                    key={rev.id}
                    className="capability-card"
                    style={{ cursor: "pointer", justifyContent: "space-between", alignItems: "center" }}
                    onClick={() => setSelectedReview(rev)}
                  >
                    <div>
                      <strong style={{ fontSize: "16px", color: "var(--text-primary)" }}>{rev.projectName}</strong>
                      <div style={{ fontSize: "13px", color: "var(--text-muted)", marginTop: "4px" }}>
                        {rev.language} • {rev.issueCount} issues • {formatDate(rev.createdAt)}
                      </div>
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      {rev.score !== null && (
                        <span
                          className="meta-badge"
                          style={{
                            fontSize: "14px",
                            fontWeight: 700,
                            backgroundColor: rev.score >= 80 ? "var(--success-bg)" : rev.score >= 60 ? "var(--warning-bg)" : "var(--danger-bg)",
                            color: rev.score >= 80 ? "var(--success)" : rev.score >= 60 ? "var(--warning)" : "var(--danger)",
                            border: `1px solid ${rev.score >= 80 ? "rgba(16, 185, 129, 0.3)" : rev.score >= 60 ? "rgba(245, 158, 11, 0.3)" : "rgba(239, 68, 68, 0.3)"}`
                          }}
                        >
                          Score: {rev.score}/100
                        </span>
                      )}
                      <button
                        type="button"
                        className="btn-secondary"
                        style={{ padding: "6px 12px", fontSize: "13px" }}
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedReview(rev);
                        }}
                      >
                        Inspect
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: REVIEWS */}
      {activeTab === "reviews" && (
        <div>
          <div style={{ marginBottom: "18px" }}>
            <input
              type="text"
              placeholder="Search reviews by project, question, or language..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: "100%", maxWidth: "400px" }}
            />
          </div>

          {filteredReviews.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔍</div>
              <h3>No Reviews Found</h3>
              <p>No past reviews match your query.</p>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
              {filteredReviews.map((rev) => (
                <div
                  key={rev.id}
                  className="capability-card"
                  style={{ cursor: "pointer", justifyContent: "space-between", alignItems: "center" }}
                  onClick={() => setSelectedReview(rev)}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                      <strong style={{ fontSize: "17px", color: "var(--text-primary)" }}>{rev.projectName}</strong>
                      <span className="meta-badge">{rev.language}</span>
                      {rev.score !== null && (
                        <span className="meta-badge" style={{ backgroundColor: "var(--success-bg)", color: "var(--success)" }}>
                          Score: {rev.score}/100
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: "14px", color: "var(--text-secondary)" }}>
                      Query: "{rev.question}"
                    </div>
                    <div style={{ fontSize: "12.5px", color: "var(--text-muted)", marginTop: "4px" }}>
                      {formatDate(rev.createdAt)} • {rev.bugs} Bugs • {rev.security} Security • {rev.performance} Perf • {rev.quality} Quality
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: "6px 14px", fontSize: "13px" }}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedReview(rev);
                      }}
                    >
                      View Report
                    </button>
                    <button
                      type="button"
                      className="btn-secondary"
                      style={{ padding: "6px 10px", fontSize: "13px", color: "var(--danger)" }}
                      onClick={(e) => handleDeleteReview(rev.id, e)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: FILES */}
      {activeTab === "files" && (
        <div>
          {files.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📁</div>
              <h3>No Files Tracked</h3>
              <p>Uploaded archives and scripts will appear here.</p>
              <button className="btn-primary" onClick={() => navigate("/")}>
                Upload Code →
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
                      <td>
                        <strong>{file.file_name}</strong>
                      </td>
                      <td>
                        <span className="meta-badge">{file.file_type || "code"}</span>
                      </td>
                      <td>{formatFileSize(file.file_size)}</td>
                      <td>{formatDate(file.upload_time)}</td>
                      <td>
                        <div style={{ display: "flex", gap: "8px" }}>
                          <button
                            type="button"
                            className="btn-secondary"
                            style={{ padding: "4px 10px", fontSize: "12px" }}
                            onClick={() => navigate("/review")}
                          >
                            Analyze
                          </button>
                          <button
                            type="button"
                            className="btn-secondary"
                            style={{ padding: "4px 10px", fontSize: "12px", color: "var(--danger)" }}
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

      {/* INSPECT REVIEW MODAL */}
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