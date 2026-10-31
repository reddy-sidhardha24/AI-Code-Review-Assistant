import React, {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo
} from "react";
import API, { cancelReviewRequest, fetchPreferences, updatePreferences } from "../api";
import { useAppAuth } from "./AuthContext";
import { saveReviewToHistory } from "../utils/reviewHistory";

/* ============================================================
   TYPES
   ============================================================ */

export interface FileAnalyzed {
  file_name: string;
  path: string;
  language: string;
}

export interface CorrectedCodeItem {
  file_name: string;
  code: string;
}

export interface CommonFinding {
  title: string;
  category?: string;
  type?: string;
  severity?: string;
  file?: string;
  line?: number | null;
  line_range?: string | null;
  evidence?: string;
  description?: string;
  explanation?: string;
  impact?: string;
  fix?: string;
  suggestion?: string;
  suggested_solution?: string;
  before_code?: string;
  after_code?: string;
  corrected_code?: string;
  reason_for_correction?: string;
  confidence?: number;
}

export interface PerformanceInfo {
  time_complexity: string;
  space_complexity: string;
  issues: CommonFinding[];
}

export interface SecurityInfo {
  issues_found: number;
  issues: CommonFinding[];
}

export interface CodeQualityInfo {
  observations: CommonFinding[];
  suggestions: CommonFinding[];
}

export interface ProjectInfo {
  name?: string | null;
  languages: string[];
  total_files: number;
  total_lines: number;
}

export interface ReviewData {
  project_name?: string;
  project: ProjectInfo;
  question: string;
  review_types: string[];
  answer_summary: string;
  files_analyzed: FileAnalyzed[];
  bugs: CommonFinding[];
  errors: CommonFinding[];
  performance?: PerformanceInfo | null;
  security?: SecurityInfo | null;
  code_quality?: CodeQualityInfo | null;
  detected_issues?: CommonFinding[];
  corrected_code?: CorrectedCodeItem[];
  key_methods: string[];
  key_classes: string[];
  libraries: string[];
  category?: string;
  best_practices?: CommonFinding[];
  score?: number | null;
  confidence: number;
  final_verdict: string;
  agent_mode?: string;
  audited_by?: {
    id?: string;
    name?: string;
    email?: string;
  } | null;
}

export type ReviewCategory =
  | "full_review"
  | "bugs"
  | "security"
  | "performance"
  | "code_quality";

interface ReviewContextType {
  review: ReviewData | null;
  loading: boolean;
  question: string;
  setQuestion: (q: string) => void;
  activeCategory: ReviewCategory;
  setActiveCategory: (cat: ReviewCategory) => void;
  currentReviewCategory: string;
  setCurrentReviewCategory: (cat: string) => void;
  error: string;
  setError: (err: string) => void;
  agentMode: "single" | "multi";
  updatingMode: boolean;
  modeNotice: string | null;
  handleToggleAgentMode: (newMode: "single" | "multi") => Promise<void>;
  runReview: (
    targetCategory: ReviewCategory,
    customQuery?: string
  ) => Promise<void>;
  cancelReview: () => Promise<void>;
  clearReview: () => void;
  loadReviewDirectly: (
    reviewData: ReviewData,
    cat?: string,
    q?: string
  ) => void;
}

const ReviewContext = createContext<ReviewContextType | undefined>(undefined);

const SESSION_STORAGE_KEY = "active_code_review_session";
const IN_PROGRESS_KEY = "review_in_progress";

const categoryPrompts: Record<ReviewCategory, string> = {
  full_review:
    "Perform a complete project-wide review covering bugs, security, performance, and code quality.",
  bugs: "Find all bugs and runtime errors in the project.",
  security: "Perform a security review and identify security vulnerabilities.",
  performance: "Analyze the project's performance and identify performance bottlenecks.",
  code_quality: "Review code quality, readability, maintainability, and architecture."
};

export const ReviewProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const { user } = useAppAuth();

  // 1. Initial State from Storage (prioritizing in-progress audits)
  const initialSession = useMemo(() => {
    try {
      const rawProgress = localStorage.getItem(IN_PROGRESS_KEY);
      if (rawProgress) {
        const p = JSON.parse(rawProgress);
        const elapsed = Date.now() - (p.startTime || 0);
        if (elapsed < 180000) {
          // An audit is currently running! Do not load old completed review
          return {
            review: null as ReviewData | null,
            question: p.question || "",
            category: (p.category as ReviewCategory) || "full_review",
            isLoading: true,
            requestId: typeof p.requestId === "string" ? p.requestId : null
          };
        } else {
          localStorage.removeItem(IN_PROGRESS_KEY);
        }
      }

      const raw = localStorage.getItem(SESSION_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && parsed.review && typeof parsed.review === "object") {
          return {
            review: parsed.review as ReviewData,
            question: parsed.question || "",
            category: (parsed.category as ReviewCategory) || "full_review",
            isLoading: false,
            requestId: null
          };
        }
      }
    } catch (e) {
      console.warn("Could not load initial review session:", e);
    }
    return {
      review: null as ReviewData | null,
      question: "",
      category: "full_review" as ReviewCategory,
      isLoading: false,
      requestId: null
    };
  }, []);

  const [review, setReview] = useState<ReviewData | null>(initialSession.review);
  const [question, setQuestion] = useState<string>(initialSession.question);
  const [activeCategory, setActiveCategory] = useState<ReviewCategory>(
    initialSession.category
  );
  const [currentReviewCategory, setCurrentReviewCategory] = useState<string>(
    initialSession.category
  );
  const [loading, setLoading] = useState<boolean>(initialSession.isLoading);
  const [error, setError] = useState<string>("");
  const [agentMode, setAgentMode] = useState<"single" | "multi">("single");
  const [updatingMode, setUpdatingMode] = useState<boolean>(false);
  const [modeNotice, setModeNotice] = useState<string | null>(null);

  // Keep track of active review promise across route shifts
  const isAnalyzingRef = useRef<boolean>(initialSession.isLoading);
  const activeReviewRequestIdRef = useRef<string | null>(initialSession.requestId);
  const activeReviewAbortControllerRef = useRef<AbortController | null>(null);
  const cancelledReviewRequestIdsRef = useRef<Set<string>>(new Set());

  // 2. Load Agent Preferences
  useEffect(() => {
    let isMounted = true;
    const loadPreferences = async () => {
      try {
        const res = await fetchPreferences();
        if (isMounted && res.data?.success && res.data.preferences?.agent_mode) {
          setAgentMode(
            res.data.preferences.agent_mode === "multi" ? "multi" : "single"
          );
        }
      } catch (e) {
        console.warn("Could not load agent preferences:", e);
      }
    };
    loadPreferences();
    return () => {
      isMounted = false;
    };
  }, []);

  // 3. Check for In-Progress Review on Mount / Refresh
  useEffect(() => {
    const rawProgress = localStorage.getItem(IN_PROGRESS_KEY);
    if (!rawProgress) return;

    try {
      const progressObj = JSON.parse(rawProgress);
      const elapsed = Date.now() - (progressObj.startTime || 0);
      if (elapsed > 180000) {
        localStorage.removeItem(IN_PROGRESS_KEY);
        setLoading(false);
        isAnalyzingRef.current = false;
        return;
      }

      setLoading(true);
      setReview(null);
      setQuestion(progressObj.question || "");
      setActiveCategory(progressObj.category || "full_review");
      setCurrentReviewCategory(progressObj.category || "full_review");
      isAnalyzingRef.current = true;

      let pollInterval: any = null;
      const pollStartTime = progressObj.startTime || Date.now();

      const pollForLatestReview = async () => {
        let currentProgress: any = null;
        try {
          currentProgress = JSON.parse(localStorage.getItem(IN_PROGRESS_KEY) || "null");
        } catch {
          currentProgress = null;
        }
        if (!currentProgress || currentProgress.requestId !== progressObj.requestId) {
          if (pollInterval) clearInterval(pollInterval);
          return true;
        }
        try {
          const res = await API.get("/api/reviews");
          if (res.data?.success && Array.isArray(res.data.reviews) && res.data.reviews.length > 0) {
            const latest = res.data.reviews[0];
            const reviewTime = new Date(latest.created_at).getTime();
            if (reviewTime >= pollStartTime - 15000) {
              const reviewData = (latest.review || latest.raw_review) as ReviewData;
              if (reviewData) {
                const resCat = latest.category || progressObj.category || "full_review";
                reviewData.category = resCat;
                reviewData.agent_mode = latest.agent_mode || agentMode;
                reviewData.audited_by = latest.audited_by || {
                  id: user?.id,
                  name: user?.fullName || user?.email || "Developer",
                  email: user?.email
                };

                setCurrentReviewCategory(resCat);
                setReview(reviewData);
                setLoading(false);
                isAnalyzingRef.current = false;
                localStorage.removeItem(IN_PROGRESS_KEY);
                localStorage.setItem(
                  SESSION_STORAGE_KEY,
                  JSON.stringify({
                    review: reviewData,
                    question: latest.question || progressObj.question,
                    category: resCat,
                    id: latest.id,
                    timestamp: Date.now()
                  })
                );
                return true;
              }
            }
          }
        } catch (err) {
          console.warn("Polling error:", err);
        }
        return false;
      };

      pollInterval = setInterval(async () => {
        const found = await pollForLatestReview();
        if (found) {
          clearInterval(pollInterval);
        }
      }, 2500);

      const timeoutTimer = setTimeout(() => {
        clearInterval(pollInterval);
        if (localStorage.getItem(IN_PROGRESS_KEY)) {
          localStorage.removeItem(IN_PROGRESS_KEY);
          setLoading(false);
          isAnalyzingRef.current = false;
        }
      }, 180000);

      return () => {
        if (pollInterval) clearInterval(pollInterval);
        clearTimeout(timeoutTimer);
      };
    } catch (e) {
      localStorage.removeItem(IN_PROGRESS_KEY);
    }
  }, [user]);

  // 4. Toggle Agent Mode
  const handleToggleAgentMode = async (newMode: "single" | "multi") => {
    if (agentMode === newMode || updatingMode) return;
    setUpdatingMode(true);
    try {
      const res = await updatePreferences({ agent_mode: newMode });
      if (res.data?.success) {
        setAgentMode(newMode);
        setModeNotice(
          newMode === "multi"
            ? "✨ Multi-Agent Collaborative Mode enabled! Reviews will now run 4 specialized agents concurrently."
            : "⚡ Fast Single-Agent Mode enabled! Reviews will run in a single high-speed LLM pass."
        );
        setTimeout(() => setModeNotice(null), 4500);
      }
    } catch (err) {
      console.error("Failed to switch agent mode:", err);
      alert("Failed to update execution mode preference.");
    } finally {
      setUpdatingMode(false);
    }
  };

  // Helper to check SQLite for freshly completed review
  const checkSQLiteForCompletedReview = async (
    startTime: number,
    cat: string,
    q: string
  ): Promise<boolean> => {
    try {
      const res = await API.get("/api/reviews");
      if (res.data?.success && Array.isArray(res.data.reviews) && res.data.reviews.length > 0) {
        const latest = res.data.reviews[0];
        const reviewTime = new Date(latest.created_at).getTime();
        if (reviewTime >= startTime - 15000) {
          const reviewData = (latest.review || latest.raw_review) as ReviewData;
          if (reviewData) {
            const resCat = latest.category || cat;
            reviewData.category = resCat;
            reviewData.agent_mode = latest.agent_mode || agentMode;
            reviewData.audited_by = latest.audited_by || {
              id: user?.id,
              name: user?.fullName || user?.email || "Developer",
              email: user?.email
            };

            setCurrentReviewCategory(resCat);
            setReview(reviewData);
            setLoading(false);
            isAnalyzingRef.current = false;
            localStorage.removeItem(IN_PROGRESS_KEY);
            localStorage.setItem(
              SESSION_STORAGE_KEY,
              JSON.stringify({
                review: reviewData,
                question: latest.question || q,
                category: resCat,
                id: latest.id,
                timestamp: Date.now()
              })
            );
            saveReviewToHistory(reviewData, q, latest.id);
            return true;
          }
        }
      }
    } catch (e) {
      console.warn("Could not check SQLite for review:", e);
    }
    return false;
  };

  // 5. Run Review (PERSISTENT & SURVIVES ROUTE TRANSITIONS)
  const runReview = async (
    targetCategory: ReviewCategory,
    customQuery?: string
  ) => {
    if (isAnalyzingRef.current) {
      console.warn("An audit is already running.");
      return;
    }

    const q =
      (customQuery !== undefined ? customQuery : question).trim() ||
      categoryPrompts[targetCategory];

    const startTime = Date.now();
    const requestId = typeof window.crypto?.randomUUID === "function"
      ? window.crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const abortController = new AbortController();
    activeReviewRequestIdRef.current = requestId;
    activeReviewAbortControllerRef.current = abortController;
    setQuestion(q);
    setActiveCategory(targetCategory);
    setCurrentReviewCategory(targetCategory);
    setLoading(true);
    setReview(null);
    setError("");
    isAnalyzingRef.current = true;

    // Remove stale completed session so old results don't linger
    localStorage.removeItem(SESSION_STORAGE_KEY);

    // Record in-progress audit marker so route shifts or refreshes preserve loading
    localStorage.setItem(
      IN_PROGRESS_KEY,
      JSON.stringify({
        question: q,
        category: targetCategory,
        startTime: startTime,
        requestId
      })
    );

    try {
      const response = await API.post("/review", {
        question: q,
        category: targetCategory
      }, {
        headers: { "X-Review-Request-Id": requestId },
        signal: abortController.signal
      });

      if (response.data?.success && response.data?.review) {
        const reviewData = response.data.review as ReviewData;
        const resCat = response.data.category || targetCategory;
        reviewData.category = resCat;
        reviewData.agent_mode = response.data?.agent_mode || agentMode;
        reviewData.audited_by = response.data?.audited_by || {
          id: user?.id,
          name: user?.fullName || user?.email || "Developer",
          email: user?.email
        };

        setCurrentReviewCategory(resCat);
        setReview(reviewData);

        // PERSIST SESSION TO LOCALSTORAGE
        localStorage.setItem(
          SESSION_STORAGE_KEY,
          JSON.stringify({
            review: reviewData,
            question: q,
            category: resCat,
            id: response.data?.id,
            timestamp: Date.now()
          })
        );
        localStorage.removeItem(IN_PROGRESS_KEY);

        saveReviewToHistory(reviewData, q, response.data?.id);
      } else {
        // Fallback: check SQLite if review was saved despite non-success payload
        const recovered = await checkSQLiteForCompletedReview(startTime, targetCategory, q);
        if (!recovered) {
          setError("The backend did not return a valid review.");
          localStorage.removeItem(IN_PROGRESS_KEY);
        }
      }
    } catch (err: any) {
      if (cancelledReviewRequestIdsRef.current.has(requestId)) {
        localStorage.removeItem(IN_PROGRESS_KEY);
        return;
      }
      console.warn("Review request threw error, checking if backend saved review to SQLite...", err);
      // Give backend brief window to finish writing to SQLite in case connection closed mid-save
      let recovered = false;
      for (let attempt = 0; attempt < 4; attempt++) {
        await new Promise((r) => setTimeout(r, 2000));
        recovered = await checkSQLiteForCompletedReview(startTime, targetCategory, q);
        if (recovered) break;
      }

      if (!recovered) {
        localStorage.removeItem(IN_PROGRESS_KEY);
        const backendError = err.response?.data?.detail;
        if (backendError) {
          setError(
            typeof backendError === "string"
              ? backendError
              : "The review request failed."
          );
        } else if (err.response?.status === 502) {
          setError(
            "The AI review response could not be validated by the backend."
          );
        } else {
          setError("Unable to connect to the backend or review was canceled.");
        }
      }
    } finally {
      cancelledReviewRequestIdsRef.current.delete(requestId);
      if (activeReviewRequestIdRef.current === requestId) {
        activeReviewRequestIdRef.current = null;
        activeReviewAbortControllerRef.current = null;
        setLoading(false);
        isAnalyzingRef.current = false;
      }
    }
  };

  const cancelReview = async () => {
    const requestId = activeReviewRequestIdRef.current;
    let cancellationRequest: Promise<any> | null = null;
    if (requestId) {
      cancelledReviewRequestIdsRef.current.add(requestId);
      cancellationRequest = cancelReviewRequest(requestId);
      activeReviewAbortControllerRef.current?.abort();
      activeReviewRequestIdRef.current = null;
      activeReviewAbortControllerRef.current = null;
    }

    setReview(null);
    setError("Stopping analysis…");
    setLoading(false);
    isAnalyzingRef.current = false;
    localStorage.removeItem(SESSION_STORAGE_KEY);
    localStorage.removeItem(IN_PROGRESS_KEY);

    if (cancellationRequest) {
      try {
        const response = await cancellationRequest;
        if (!response.data?.cancelled) {
          setError("Stopped waiting for this review, but the server could not confirm cancellation. The active provider request may finish in the background.");
          return;
        }
        setError("Analysis stopped. Any provider request already in progress may finish in the background.");
      } catch (err) {
        console.warn("Could not notify the server to stop this review:", err);
        setError("Stopped waiting for this review, but the server could not confirm cancellation. The active provider request may finish in the background.");
      }
    } else {
      setError("Analysis stopped. Any provider request already in progress may finish in the background.");
    }
  };

  // 6. Clear Review
  const clearReview = () => {
    setReview(null);
    setError("");
    setQuestion("");
    setLoading(false);
    isAnalyzingRef.current = false;
    localStorage.removeItem(SESSION_STORAGE_KEY);
    localStorage.removeItem(IN_PROGRESS_KEY);
  };

  // 7. Load Review Directly (e.g. from Modal)
  const loadReviewDirectly = (
    reviewData: ReviewData,
    cat?: string,
    q?: string
  ) => {
    const finalCat = (cat as ReviewCategory) || "full_review";
    setReview(reviewData);
    setCurrentReviewCategory(finalCat);
    setActiveCategory(finalCat);
    if (q) setQuestion(q);
    localStorage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify({
        review: reviewData,
        question: q || reviewData.question || "",
        category: finalCat,
        timestamp: Date.now()
      })
    );
  };

  return (
    <ReviewContext.Provider
      value={{
        review,
        loading,
        question,
        setQuestion,
        activeCategory,
        setActiveCategory,
        currentReviewCategory,
        setCurrentReviewCategory,
        error,
        setError,
        agentMode,
        updatingMode,
        modeNotice,
        handleToggleAgentMode,
        runReview,
        cancelReview,
        clearReview,
        loadReviewDirectly
      }}
    >
      {children}
    </ReviewContext.Provider>
  );
};

export const useReview = (): ReviewContextType => {
  const context = useContext(ReviewContext);
  if (!context) {
    throw new Error("useReview must be used within a ReviewProvider");
  }
  return context;
};
