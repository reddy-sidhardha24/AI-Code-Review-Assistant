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
}

/* ============================================================
   GET HISTORY
   ============================================================ */

export function getReviewHistory(): HistoryReview[] {
  try {
    const stored =
      localStorage.getItem("codeReviewHistory");

    if (!stored) {
      return [];
    }

    const parsed = JSON.parse(stored);

    if (!Array.isArray(parsed)) {
      return [];
    }

    return parsed;
  } catch (error) {
    console.error(
      "Failed to read review history:",
      error
    );

    return [];
  }
}


/* ============================================================
   SAVE REVIEW
   ============================================================ */

export function saveReviewToHistory(
  review: any,
  question: string
): void {
  try {
    const bugs =
      Array.isArray(review?.bugs)
        ? review.bugs.length
        : 0;

    const security =
      review?.security?.issues_found || 0;

    const performance =
      Array.isArray(
        review?.performance?.issues
      )
        ? review.performance.issues.length
        : 0;

    const qualityObservations =
      Array.isArray(
        review?.code_quality?.observations
      )
        ? review.code_quality.observations.length
        : 0;

    const qualitySuggestions =
      Array.isArray(
        review?.code_quality?.suggestions
      )
        ? review.code_quality.suggestions.length
        : 0;

    const quality =
      qualityObservations +
      qualitySuggestions;

    const issueCount =
      bugs +
      security +
      performance +
      quality;

    const languages =
      Array.isArray(
        review?.project?.languages
      )
        ? review.project.languages
        : [];

    const language =
      languages.length > 0
        ? languages.join(", ")
        : "Unknown";

    const projectName =
      review?.project?.name ||
      "Unknown Project";

    const score =
      typeof review?.score === "number"
        ? review.score
        : null;

    const confidence =
      typeof review?.confidence === "number"
        ? review.confidence
        : 0;

    const historyItem: HistoryReview = {
      id:
        `${Date.now()}-${Math.random()
          .toString(36)
          .substring(2, 9)}`,

      projectName,

      language,

      question,

      issueCount,

      bugs,

      security,

      performance,

      quality,

      score,

      confidence,

      createdAt:
        new Date().toISOString(),
    };

    const history =
      getReviewHistory();

    const updatedHistory = [
      historyItem,
      ...history,
    ];

    /*
     * Keep the most recent 100 reviews.
     * This prevents localStorage from growing forever.
     */

    const limitedHistory =
      updatedHistory.slice(0, 100);

    localStorage.setItem(
      "codeReviewHistory",
      JSON.stringify(
        limitedHistory
      )
    );

  } catch (error) {
    console.error(
      "Failed to save review history:",
      error
    );
  }
}


/* ============================================================
   CLEAR HISTORY
   ============================================================ */

export function clearReviewHistory(): void {
  localStorage.removeItem(
    "codeReviewHistory"
  );
}