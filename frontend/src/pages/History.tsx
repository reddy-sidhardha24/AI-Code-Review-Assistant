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

type FilterType =
  | "all"
  | "bugs"
  | "security"
  | "performance"
  | "quality";

function History() {
  const navigate = useNavigate();

  const [history, setHistory] = useState<
    HistoryReview[]
  >([]);

  const [search, setSearch] = useState("");

  const [filter, setFilter] =
    useState<FilterType>("all");

  const [selectedReview, setSelectedReview] =
    useState<HistoryReview | null>(null);

  /* ==========================================================
     LOAD HISTORY
     ========================================================== */

  const loadHistory = () => {
    try {
      const stored =
        localStorage.getItem(
          "codeReviewHistory"
        );

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
     FILTER HISTORY
     ========================================================== */

  const filteredHistory = useMemo(() => {
    const normalizedSearch =
      search.trim().toLowerCase();

    return history.filter((item) => {
      const matchesSearch =
        !normalizedSearch ||
        item.projectName
          ?.toLowerCase()
          .includes(normalizedSearch) ||
        item.language
          ?.toLowerCase()
          .includes(normalizedSearch) ||
        item.question
          ?.toLowerCase()
          .includes(normalizedSearch);

      let matchesFilter = true;

      switch (filter) {
        case "bugs":
          matchesFilter =
            (item.bugs || 0) > 0;
          break;

        case "security":
          matchesFilter =
            (item.security || 0) > 0;
          break;

        case "performance":
          matchesFilter =
            (item.performance || 0) > 0;
          break;

        case "quality":
          matchesFilter =
            (item.quality || 0) > 0;
          break;

        default:
          matchesFilter = true;
      }

      return (
        matchesSearch &&
        matchesFilter
      );
    });
  }, [history, search, filter]);

  /* ==========================================================
     DELETE ONE REVIEW
     ========================================================== */

  const deleteReview = (
    id: string
  ) => {
    const confirmed = window.confirm(
      "Delete this review from history?"
    );

    if (!confirmed) {
      return;
    }

    const updated = history.filter(
      (item) => item.id !== id
    );

    setHistory(updated);

    localStorage.setItem(
      "codeReviewHistory",
      JSON.stringify(updated)
    );

    if (
      selectedReview?.id === id
    ) {
      setSelectedReview(null);
    }
  };

  /* ==========================================================
     CLEAR HISTORY
     ========================================================== */

  const clearHistory = () => {
    if (history.length === 0) {
      return;
    }

    const confirmed = window.confirm(
      "This will permanently remove all review history from this browser. Continue?"
    );

    if (!confirmed) {
      return;
    }

    localStorage.removeItem(
      "codeReviewHistory"
    );

    setHistory([]);

    setSelectedReview(null);
  };

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
     TOTAL ISSUES
     ========================================================== */

  const totalIssues = history.reduce(
    (total, item) =>
      total + (item.issueCount || 0),
    0
  );

  /* ==========================================================
     RENDER
     ========================================================== */

  return (
    <main className="history-page-modern">

      <div className="container">

        {/* ==================================================
            HEADER
        ================================================== */}

        <section className="history-header">

          <div>

            <div className="section-label">
              REVIEW ACTIVITY
            </div>

            <h1>
              Analysis History
            </h1>

            <p>
              View and manage your previous AI-powered
              code reviews.
            </p>

          </div>


          <button
            className="history-new-button"
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
            SUMMARY
        ================================================== */}

        <section className="history-summary">

          <div className="history-summary-card">

            <span>
              TOTAL REVIEWS
            </span>

            <strong>
              {history.length}
            </strong>

          </div>


          <div className="history-summary-card">

            <span>
              TOTAL ISSUES
            </span>

            <strong>
              {totalIssues}
            </strong>

          </div>


          <div className="history-summary-card">

            <span>
              BUGS
            </span>

            <strong className="history-red">
              {history.reduce(
                (total, item) =>
                  total + (item.bugs || 0),
                0
              )}
            </strong>

          </div>


          <div className="history-summary-card">

            <span>
              SECURITY
            </span>

            <strong className="history-yellow">
              {history.reduce(
                (total, item) =>
                  total +
                  (item.security || 0),
                0
              )}
            </strong>

          </div>

        </section>


        {/* ==================================================
            CONTROLS
        ================================================== */}

        <section className="history-controls">

          <div className="history-search">

            <span>
              ⌕
            </span>

            <input
              type="text"
              placeholder="Search projects, languages, or questions..."
              value={search}
              onChange={(e) =>
                setSearch(
                  e.target.value
                )
              }
            />

            {search && (
              <button
                onClick={() =>
                  setSearch("")
                }
              >
                ×
              </button>
            )}

          </div>


          <div className="history-filters">

            <button
              className={
                filter === "all"
                  ? "history-filter active"
                  : "history-filter"
              }
              onClick={() =>
                setFilter("all")
              }
            >
              All
            </button>

            <button
              className={
                filter === "bugs"
                  ? "history-filter active"
                  : "history-filter"
              }
              onClick={() =>
                setFilter("bugs")
              }
            >
              Bugs
            </button>

            <button
              className={
                filter === "security"
                  ? "history-filter active"
                  : "history-filter"
              }
              onClick={() =>
                setFilter("security")
              }
            >
              Security
            </button>

            <button
              className={
                filter === "performance"
                  ? "history-filter active"
                  : "history-filter"
              }
              onClick={() =>
                setFilter("performance")
              }
            >
              Performance
            </button>

            <button
              className={
                filter === "quality"
                  ? "history-filter active"
                  : "history-filter"
              }
              onClick={() =>
                setFilter("quality")
              }
            >
              Quality
            </button>

          </div>


          {history.length > 0 && (

            <button
              className="history-clear-button"
              onClick={clearHistory}
            >
              Clear history
            </button>

          )}

        </section>


        {/* ==================================================
            RESULTS COUNT
        ================================================== */}

        <div className="history-results-info">

          <span>
            {filteredHistory.length}{" "}
            {filteredHistory.length === 1
              ? "review"
              : "reviews"}
          </span>

          {search && (
            <span>
              matching "{search}"
            </span>
          )}

        </div>


        {/* ==================================================
            EMPTY STATE
        ================================================== */}

        {history.length === 0 ? (

          <section className="history-empty">

            <div className="history-empty-icon">
              ◷
            </div>

            <h2>
              No review history yet
            </h2>

            <p>
              Your completed code reviews will
              automatically appear here.
            </p>

            <button
              onClick={() =>
                navigate("/review")
              }
            >
              Start your first review →
            </button>

          </section>

        ) : filteredHistory.length === 0 ? (

          <section className="history-empty">

            <div className="history-empty-icon">
              ⌕
            </div>

            <h2>
              No matching reviews
            </h2>

            <p>
              Try changing your search or
              selecting a different filter.
            </p>

            <button
              onClick={() => {
                setSearch("");
                setFilter("all");
              }}
            >
              Reset filters
            </button>

          </section>

        ) : (

          /* ==================================================
             REVIEW LIST
             ================================================== */

          <section className="history-list">

            {filteredHistory.map(
              (item) => (

                <article
                  className="history-card"
                  key={item.id}
                >

                  {/* PROJECT ICON */}

                  <div className="history-project-icon">
                    {item.language
                      ?.charAt(0)
                      .toUpperCase() || "C"}
                  </div>


                  {/* PROJECT INFORMATION */}

                  <div className="history-project">

                    <h3>
                      {item.projectName}
                    </h3>

                    <span>
                      {item.language}
                      {" • "}
                      {formatDate(
                        item.createdAt
                      )}
                    </span>

                    <p>
                      {item.question}
                    </p>

                  </div>


                  {/* ISSUE COUNTS */}

                  <div className="history-issues">

                    <div className="history-issue">

                      <span className="issue-number red">
                        {item.bugs || 0}
                      </span>

                      <span>
                        bugs
                      </span>

                    </div>


                    <div className="history-issue">

                      <span className="issue-number yellow">
                        {item.security || 0}
                      </span>

                      <span>
                        security
                      </span>

                    </div>


                    <div className="history-issue">

                      <span className="issue-number blue">
                        {item.performance || 0}
                      </span>

                      <span>
                        performance
                      </span>

                    </div>


                    <div className="history-issue">

                      <span className="issue-number purple">
                        {item.quality || 0}
                      </span>

                      <span>
                        quality
                      </span>

                    </div>

                  </div>


                  {/* CONFIDENCE */}

                  <div className="history-confidence">

                    <strong>
                      {item.confidence || 0}%
                    </strong>

                    <span>
                      confidence
                    </span>

                  </div>


                  {/* ACTIONS */}

                  <div className="history-actions">

                    <button
                      className="history-view-button"
                      onClick={() =>
                        setSelectedReview(item)
                      }
                    >
                      View
                    </button>

                    <button
                      className="history-delete-button"
                      onClick={() =>
                        deleteReview(item.id)
                      }
                      title="Delete review"
                    >
                      ×
                    </button>

                  </div>

                </article>

              )
            )}

          </section>

        )}


        {/* ==================================================
            REVIEW DETAILS MODAL
            ================================================== */}

        {selectedReview && (

          <div
            className="history-modal-overlay"
            onClick={() =>
              setSelectedReview(null)
            }
          >

            <div
              className="history-modal"
              onClick={(e) =>
                e.stopPropagation()
              }
            >

              <div className="history-modal-header">

                <div>

                  <span className="section-label">
                    REVIEW DETAILS
                  </span>

                  <h2>
                    {selectedReview.projectName}
                  </h2>

                </div>

                <button
                  className="history-modal-close"
                  onClick={() =>
                    setSelectedReview(null)
                  }
                >
                  ×
                </button>

              </div>


              <div className="history-modal-meta">

                <span>
                  {selectedReview.language}
                </span>

                <span>
                  {formatDate(
                    selectedReview.createdAt
                  )}
                </span>

                <span>
                  {selectedReview.confidence}%
                  confidence
                </span>

              </div>


              <div className="history-modal-question">

                <span>
                  REVIEW QUESTION
                </span>

                <p>
                  {selectedReview.question}
                </p>

              </div>


              <div className="history-modal-stats">

                <div>
                  <strong className="history-red">
                    {selectedReview.bugs || 0}
                  </strong>

                  <span>
                    Bugs
                  </span>
                </div>


                <div>
                  <strong className="history-yellow">
                    {selectedReview.security || 0}
                  </strong>

                  <span>
                    Security
                  </span>
                </div>


                <div>
                  <strong className="history-blue">
                    {selectedReview.performance || 0}
                  </strong>

                  <span>
                    Performance
                  </span>
                </div>


                <div>
                  <strong className="history-purple">
                    {selectedReview.quality || 0}
                  </strong>

                  <span>
                    Quality
                  </span>
                </div>

              </div>


              <div className="history-modal-footer">

                <button
                  onClick={() => {
                    setSelectedReview(null);
                    navigate("/review");
                  }}
                >
                  Run another review →
                </button>

              </div>

            </div>

          </div>

        )}

      </div>

    </main>
  );
}

export default History;