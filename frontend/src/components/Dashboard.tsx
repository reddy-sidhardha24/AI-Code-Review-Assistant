import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

interface HistoryReview {
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
}

function Dashboard() {
  const navigate = useNavigate();

  const [history, setHistory] = useState<HistoryReview[]>([]);

  /* ==========================================================
     LOAD HISTORY
     ========================================================== */

  const loadHistory = () => {
    try {
      const stored =
        localStorage.getItem("codeReviewHistory");

      if (!stored) {
        setHistory([]);
        return;
      }

      const parsed = JSON.parse(stored);

      if (Array.isArray(parsed)) {
        setHistory(parsed);
      } else {
        setHistory([]);
      }
    } catch (error) {
      console.error(
        "Unable to load review history:",
        error
      );

      setHistory([]);
    }
  };

  useEffect(() => {
    loadHistory();

    const handleStorageChange = () => {
      loadHistory();
    };

    window.addEventListener(
      "storage",
      handleStorageChange
    );

    const interval = window.setInterval(
      loadHistory,
      1000
    );

    return () => {
      window.removeEventListener(
        "storage",
        handleStorageChange
      );

      window.clearInterval(interval);
    };
  }, []);

  /* ==========================================================
     CALCULATE STATISTICS
     ========================================================== */

  const statistics = useMemo(() => {
    const totalReviews = history.length;

    const bugs = history.reduce(
      (total, item) =>
        total + (item.bugs || 0),
      0
    );

    const security = history.reduce(
      (total, item) =>
        total + (item.security || 0),
      0
    );

    const performance = history.reduce(
      (total, item) =>
        total + (item.performance || 0),
      0
    );

    const quality = history.reduce(
      (total, item) =>
        total + (item.quality || 0),
      0
    );

    const totalIssues = history.reduce(
      (total, item) =>
        total + (item.issueCount || 0),
      0
    );

    const scoredReviews = history.filter(
      (item) =>
        typeof item.score === "number"
    );

    const averageScore =
      scoredReviews.length > 0
        ? scoredReviews.reduce(
            (total, item) =>
              total + (item.score || 0),
            0
          ) / scoredReviews.length
        : null;

    const averageConfidence =
      totalReviews > 0
        ? history.reduce(
            (total, item) =>
              total + (item.confidence || 0),
            0
          ) / totalReviews
        : 0;

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

  /* ==========================================================
     RECENT REVIEWS
     ========================================================== */

  const recentReviews =
    history.slice(0, 5);

  /* ==========================================================
     FORMAT DATE
     ========================================================== */

  const formatDate = (
    dateString: string
  ) => {
    try {
      return new Intl.DateTimeFormat(
        "en-IN",
        {
          day: "2-digit",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }
      ).format(
        new Date(dateString)
      );
    } catch {
      return "Unknown date";
    }
  };

  /* ==========================================================
     RENDER
     ========================================================== */

  return (
    <main className="dashboard-page-modern">
      <div className="container">

        {/* ==================================================
            HEADER
        ================================================== */}

        <section className="dashboard-header">

          <div>
            <div className="section-label">
              PROJECT OVERVIEW
            </div>

            <h1>
              Review Dashboard
            </h1>

            <p>
              Monitor your AI-powered code analysis
              activity and project health.
            </p>
          </div>

          <button
            className="dashboard-review-button"
            onClick={() =>
              navigate("/review")
            }
          >
            <span>✦</span>
            New Review
            <span>→</span>
          </button>

        </section>


        {/* ==================================================
            STATISTICS
        ================================================== */}

        <section className="dashboard-stats">

          {/* Reviews */}

          <article className="dashboard-stat-card">

            <div className="stat-card-top">

              <span>
                TOTAL REVIEWS
              </span>

              <div className="stat-icon purple">
                ◈
              </div>

            </div>

            <strong>
              {statistics.totalReviews}
            </strong>

            <small>
              projects analyzed
            </small>

          </article>


          {/* Bugs */}

          <article className="dashboard-stat-card">

            <div className="stat-card-top">

              <span>
                BUGS FOUND
              </span>

              <div className="stat-icon red">
                !
              </div>

            </div>

            <strong className="red-value">
              {statistics.bugs}
            </strong>

            <small>
              runtime issues detected
            </small>

          </article>


          {/* Security */}

          <article className="dashboard-stat-card">

            <div className="stat-card-top">

              <span>
                SECURITY
              </span>

              <div className="stat-icon yellow">
                ◇
              </div>

            </div>

            <strong className="yellow-value">
              {statistics.security}
            </strong>

            <small>
              security findings
            </small>

          </article>


          {/* Confidence */}

          <article className="dashboard-stat-card">

            <div className="stat-card-top">

              <span>
                AI CONFIDENCE
              </span>

              <div className="stat-icon green">
                ✓
              </div>

            </div>

            <strong className="green-value">
              {statistics.totalReviews > 0
                ? `${Math.round(
                    statistics.averageConfidence
                  )}%`
                : "—"}
            </strong>

            <small>
              average analysis confidence
            </small>

          </article>

        </section>


        {/* ==================================================
            SECONDARY STATISTICS
        ================================================== */}

        <section className="dashboard-secondary">

          <div className="dashboard-secondary-card">

            <span>
              TOTAL ISSUES
            </span>

            <strong>
              {statistics.totalIssues}
            </strong>

            <p>
              Across all completed reviews
            </p>

          </div>


          <div className="dashboard-secondary-card">

            <span>
              PERFORMANCE
            </span>

            <strong>
              {statistics.performance}
            </strong>

            <p>
              Performance findings
            </p>

          </div>


          <div className="dashboard-secondary-card">

            <span>
              CODE QUALITY
            </span>

            <strong>
              {statistics.quality}
            </strong>

            <p>
              Quality observations and suggestions
            </p>

          </div>


          <div className="dashboard-secondary-card">

            <span>
              AVERAGE SCORE
            </span>

            <strong>
              {statistics.averageScore !== null
                ? `${statistics.averageScore.toFixed(
                    1
                  )}/10`
                : "—"}
            </strong>

            <p>
              From scored reviews
            </p>

          </div>

        </section>


        {/* ==================================================
            RECENT ACTIVITY
        ================================================== */}

        <section className="dashboard-activity">

          <div className="dashboard-section-header">

            <div>
              <span className="section-label">
                RECENT ACTIVITY
              </span>

              <h2>
                Latest code reviews
              </h2>
            </div>

            <button
              onClick={() =>
                navigate("/history")
              }
            >
              View all →
            </button>

          </div>


          {recentReviews.length === 0 ? (

            <div className="dashboard-empty">

              <div className="dashboard-empty-icon">
                ◈
              </div>

              <h3>
                No reviews yet
              </h3>

              <p>
                Complete your first AI code review
                to see project activity here.
              </p>

              <button
                onClick={() =>
                  navigate("/review")
                }
              >
                Start your first review →
              </button>

            </div>

          ) : (

            <div className="dashboard-review-list">

              {recentReviews.map(
                (item) => (

                  <article
                    className="dashboard-review-row"
                    key={item.id}
                  >

                    <div className="dashboard-project-icon">
                      {item.language
                        ?.charAt(0)
                        .toUpperCase() || "C"}
                    </div>


                    <div className="dashboard-project-info">

                      <strong>
                        {item.projectName}
                      </strong>

                      <span>
                        {item.language}
                        {" • "}
                        {formatDate(
                          item.createdAt
                        )}
                      </span>

                    </div>


                    <div className="dashboard-issue-summary">

                      <span className="dashboard-bug-count">
                        {item.bugs || 0} bugs
                      </span>

                      <span className="dashboard-security-count">
                        {item.security || 0} security
                      </span>

                    </div>


                    <div className="dashboard-confidence">

                      <span>
                        {item.confidence || 0}%
                      </span>

                      <small>
                        confidence
                      </small>

                    </div>


                    <button
                      className="dashboard-row-arrow"
                      onClick={() =>
                        navigate("/history")
                      }
                    >
                      →
                    </button>

                  </article>

                )
              )}

            </div>

          )}

        </section>


        {/* ==================================================
            ANALYSIS BREAKDOWN
        ================================================== */}

        {statistics.totalReviews > 0 && (

          <section className="dashboard-breakdown">

            <div className="dashboard-section-header">

              <div>
                <span className="section-label">
                  ANALYSIS BREAKDOWN
                </span>

                <h2>
                  What the AI is finding
                </h2>
              </div>

            </div>


            <div className="breakdown-grid">

              <div className="breakdown-item">

                <div className="breakdown-heading">

                  <span>
                    Bugs
                  </span>

                  <strong>
                    {statistics.bugs}
                  </strong>

                </div>

                <div className="breakdown-bar">

                  <span
                    className="bugs-bar"
                    style={{
                      width: `${
                        statistics.totalIssues > 0
                          ? Math.min(
                              100,
                              (statistics.bugs /
                                statistics.totalIssues) *
                                100
                            )
                          : 0
                      }%`,
                    }}
                  />

                </div>

              </div>


              <div className="breakdown-item">

                <div className="breakdown-heading">

                  <span>
                    Security
                  </span>

                  <strong>
                    {statistics.security}
                  </strong>

                </div>

                <div className="breakdown-bar">

                  <span
                    className="security-bar"
                    style={{
                      width: `${
                        statistics.totalIssues > 0
                          ? Math.min(
                              100,
                              (statistics.security /
                                statistics.totalIssues) *
                                100
                            )
                          : 0
                      }%`,
                    }}
                  />

                </div>

              </div>


              <div className="breakdown-item">

                <div className="breakdown-heading">

                  <span>
                    Performance
                  </span>

                  <strong>
                    {statistics.performance}
                  </strong>

                </div>

                <div className="breakdown-bar">

                  <span
                    className="performance-bar"
                    style={{
                      width: `${
                        statistics.totalIssues > 0
                          ? Math.min(
                              100,
                              (statistics.performance /
                                statistics.totalIssues) *
                                100
                            )
                          : 0
                      }%`,
                    }}
                  />

                </div>

              </div>


              <div className="breakdown-item">

                <div className="breakdown-heading">

                  <span>
                    Code Quality
                  </span>

                  <strong>
                    {statistics.quality}
                  </strong>

                </div>

                <div className="breakdown-bar">

                  <span
                    className="quality-bar"
                    style={{
                      width: `${
                        statistics.totalIssues > 0
                          ? Math.min(
                              100,
                              (statistics.quality /
                                statistics.totalIssues) *
                                100
                            )
                          : 0
                      }%`,
                    }}
                  />

                </div>

              </div>

            </div>

          </section>

        )}

      </div>
    </main>
  );
}

export default Dashboard;