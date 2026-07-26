import { useState } from "react";
import API from "../api";


// ============================================================
// Interfaces
// ============================================================

interface FileAnalyzed {
  file_name: string;
  path: string;
  language: string;
}


interface BugFinding {
  title: string;
  type: string;
  severity: string;
  file: string;
  line?: number | null;
  line_range?: string | null;
  evidence: string;
  description: string;
  impact: string;
  fix: string;
  confidence: number;
}


interface ErrorFinding {
  type: string;
  title: string;
  file: string;
  line?: number | null;
  line_range?: string | null;
  evidence: string;
  description: string;
  impact: string;
  fix: string;
  confidence: number;
}


interface PerformanceIssue {
  title: string;
  description: string;
  file: string;
  line?: number | null;
  line_range?: string | null;
  evidence: string;
  impact: string;
  suggestion: string;
  confidence: number;
}


interface PerformanceInfo {
  time_complexity: string;
  space_complexity: string;
  issues: PerformanceIssue[];
}


interface SecurityInfo {
  issues_found: number;
  issues: string[];
}


interface CodeQualityInfo {
  observations: string[];
  suggestions: string[];
}


interface ReviewData {
  project: {
    name?: string | null;
    languages: string[];
    total_files: number;
    total_lines: number;
  };

  question: string;

  review_types: string[];

  answer_summary: string;

  files_analyzed: FileAnalyzed[];

  bugs: BugFinding[];

  errors: ErrorFinding[];

  performance?: PerformanceInfo | null;

  security?: SecurityInfo | null;

  code_quality?: CodeQualityInfo | null;

  key_methods: string[];

  key_classes: string[];

  libraries: string[];

  expected_output?: string | null;

  score?: number | null;

  confidence: number;

  final_verdict: string;
}


// ============================================================
// Review Component
// ============================================================

function Review() {

  const [question, setQuestion] =
    useState("");

  const [review, setReview] =
    useState<ReviewData | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");


  // ==========================================================
  // Ask Question
  // ==========================================================

  const askQuestion = async () => {

    const trimmedQuestion =
      question.trim();

    if (!trimmedQuestion) {

      alert(
        "Please enter a question."
      );

      return;
    }

    setLoading(true);

    setReview(null);

    setError("");

    try {

      const res = await API.post(
        "/review",
        {
          question: trimmedQuestion,
        }
      );


      if (
        res.data?.success &&
        res.data?.review
      ) {

        setReview(
          res.data.review
        );

      } else {

        setError(
          "No review response received."
        );
      }

    } catch (err: any) {

      console.error(
        "Review request failed:",
        err
      );


      if (
        err.response?.data?.detail
      ) {

        setError(
          err.response.data.detail
        );

      } else {

        setError(
          "Unable to connect to backend."
        );
      }

    } finally {

      setLoading(false);
    }
  };


  // ==========================================================
  // UI
  // ==========================================================

  return (

    <div
      style={{
        width: "900px",
        maxWidth: "90%",
        margin: "40px auto",
      }}
    >

      <h1>
        AI Code Review Assistant
      </h1>


      {/* =====================================================
          QUESTION
      ===================================================== */}

      <textarea
        rows={6}
        placeholder="Ask anything about the uploaded project..."
        value={question}
        disabled={loading}
        onChange={(e) =>
          setQuestion(
            e.target.value
          )
        }
        style={{
          width: "100%",
          padding: "12px",
          fontSize: "16px",
          boxSizing: "border-box",
        }}
      />


      <br />
      <br />


      <button
        onClick={askQuestion}
        disabled={loading}
      >

        {
          loading
            ? "Analyzing..."
            : "Review Project"
        }

      </button>


      {/* =====================================================
          LOADING
      ===================================================== */}

      {
        loading && (

          <h3>
            Analyzing project...
          </h3>

        )
      }


      {/* =====================================================
          ERROR
      ===================================================== */}

      {
        error && (

          <div
            style={{
              marginTop: "20px",
              color: "red",
              fontWeight: "bold",
            }}
          >

            {error}

          </div>

        )
      }


      {/* =====================================================
          REVIEW RESULT
      ===================================================== */}

      {
        review && (

          <div
            style={{
              marginTop: "30px",
              border: "1px solid #ddd",
              padding: "25px",
              borderRadius: "10px",
              lineHeight: "1.7",
            }}
          >

            <h2>
              Review Result
            </h2>


            {/* =================================================
                PROJECT INFORMATION
            ================================================= */}

            <h3>
              Project Information
            </h3>


            <p>

              <strong>
                Project:
              </strong>{" "}

              {
                review.project?.name ||
                "Unknown"
              }

            </p>


            <p>

              <strong>
                Languages:
              </strong>{" "}

              {
                review.project
                  ?.languages
                  ?.length > 0

                  ? review.project.languages.join(
                      ", "
                    )

                  : "Unknown"
              }

            </p>


            <p>

              <strong>
                Total Files:
              </strong>{" "}

              {
                review.project
                  ?.total_files ?? 0
              }

            </p>


            <p>

              <strong>
                Total Lines:
              </strong>{" "}

              {
                review.project
                  ?.total_lines ?? 0
              }

            </p>


            {/* =================================================
                REVIEW TYPES
            ================================================= */}

            {
              review.review_types?.length > 0 && (

                <>
                  <h3>
                    Review Types
                  </h3>

                  <ul>

                    {
                      review.review_types.map(
                        (type, index) => (

                          <li key={index}>
                            {type}
                          </li>

                        )
                      )
                    }

                  </ul>
                </>

              )
            }


            {/* =================================================
                ANSWER SUMMARY
            ================================================= */}

            {
              review.answer_summary && (

                <>
                  <h3>
                    Code Summary
                  </h3>

                  <p>
                    {
                      review.answer_summary
                    }
                  </p>
                </>

              )
            }


            {/* =================================================
                FILES ANALYZED
            ================================================= */}

            {
              review.files_analyzed
                ?.length > 0 && (

                <>
                  <h3>
                    Files Analyzed
                  </h3>

                  <ul>

                    {
                      review.files_analyzed.map(
                        (file, index) => (

                          <li
                            key={index}
                            style={{
                              marginBottom:
                                "10px",
                            }}
                          >

                            <strong>
                              {file.file_name}
                            </strong>

                            {" — "}

                            {file.language}

                            <br />

                            <span>
                              {file.path}
                            </span>

                          </li>

                        )
                      )
                    }

                  </ul>
                </>

              )
            }


            {/* =================================================
                BUGS
            ================================================= */}

            <h3>
              Bugs Found
            </h3>


            {
              !review.bugs ||
              review.bugs.length === 0

                ? (

                  <p>
                    No verified bugs found.
                  </p>

                )

                : (

                  review.bugs.map(
                    (bug, index) => (

                      <div
                        key={index}
                        style={{
                          marginBottom:
                            "25px",
                          padding: "15px",
                          border:
                            "1px solid #444",
                          borderRadius:
                            "8px",
                        }}
                      >

                        <h4>
                          {bug.title}
                        </h4>


                        <p>

                          <strong>
                            Type:
                          </strong>{" "}

                          {bug.type}

                        </p>


                        <p>

                          <strong>
                            Severity:
                          </strong>{" "}

                          {bug.severity}

                        </p>


                        <p>

                          <strong>
                            File:
                          </strong>{" "}

                          {bug.file}

                        </p>


                        {
                          bug.line !== null &&
                          bug.line !== undefined && (

                            <p>

                              <strong>
                                Line:
                              </strong>{" "}

                              {bug.line}

                            </p>

                          )
                        }


                        {
                          bug.line_range && (

                            <p>

                              <strong>
                                Lines:
                              </strong>{" "}

                              {
                                bug.line_range
                              }

                            </p>

                          )
                        }


                        {
                          bug.description && (

                            <p>

                              <strong>
                                Description:
                              </strong>{" "}

                              {
                                bug.description
                              }

                            </p>

                          )
                        }


                        {
                          bug.evidence && (

                            <p>

                              <strong>
                                Evidence:
                              </strong>{" "}

                              {
                                bug.evidence
                              }

                            </p>

                          )
                        }


                        {
                          bug.impact && (

                            <p>

                              <strong>
                                Impact:
                              </strong>{" "}

                              {
                                bug.impact
                              }

                            </p>

                          )
                        }


                        {
                          bug.fix && (

                            <p>

                              <strong>
                                Fix:
                              </strong>{" "}

                              {
                                bug.fix
                              }

                            </p>

                          )
                        }


                        <p>

                          <strong>
                            Confidence:
                          </strong>{" "}

                          {
                            bug.confidence
                          }%

                        </p>

                      </div>

                    )
                  )

                )
            }


            {/* =================================================
                ERRORS
            ================================================= */}

            <h3>
              Errors
            </h3>


            {
              !review.errors ||
              review.errors.length === 0

                ? (

                  <p>
                    No confirmed errors found.
                  </p>

                )

                : (

                  review.errors.map(
                    (item, index) => (

                      <div
                        key={index}
                        style={{
                          marginBottom:
                            "25px",
                          padding: "15px",
                          border:
                            "1px solid #444",
                          borderRadius:
                            "8px",
                        }}
                      >

                        <h4>
                          {item.title}
                        </h4>


                        <p>

                          <strong>
                            Type:
                          </strong>{" "}

                          {item.type}

                        </p>


                        <p>

                          <strong>
                            File:
                          </strong>{" "}

                          {item.file}

                        </p>


                        {
                          item.line !== null &&
                          item.line !== undefined && (

                            <p>

                              <strong>
                                Line:
                              </strong>{" "}

                              {item.line}

                            </p>

                          )
                        }


                        {
                          item.line_range && (

                            <p>

                              <strong>
                                Lines:
                              </strong>{" "}

                              {
                                item.line_range
                              }

                            </p>

                          )
                        }


                        {
                          item.description && (

                            <p>

                              <strong>
                                Description:
                              </strong>{" "}

                              {
                                item.description
                              }

                            </p>

                          )
                        }


                        {
                          item.evidence && (

                            <p>

                              <strong>
                                Evidence:
                              </strong>{" "}

                              {
                                item.evidence
                              }

                            </p>

                          )
                        }


                        {
                          item.impact && (

                            <p>

                              <strong>
                                Impact:
                              </strong>{" "}

                              {
                                item.impact
                              }

                            </p>

                          )
                        }


                        {
                          item.fix && (

                            <p>

                              <strong>
                                Fix:
                              </strong>{" "}

                              {
                                item.fix
                              }

                            </p>

                          )
                        }


                        <p>

                          <strong>
                            Confidence:
                          </strong>{" "}

                          {
                            item.confidence
                          }%

                        </p>

                      </div>

                    )
                  )

                )
            }


            {/* =================================================
                PERFORMANCE
            ================================================= */}

            {
              review.performance && (

                <>

                  <h3>
                    Performance
                  </h3>


                  <p>

                    <strong>
                      Time Complexity:
                    </strong>{" "}

                    {
                      review.performance
                        .time_complexity ||
                      "Not determined"
                    }

                  </p>


                  <p>

                    <strong>
                      Space Complexity:
                    </strong>{" "}

                    {
                      review.performance
                        .space_complexity ||
                      "Not determined"
                    }

                  </p>


                  <h4>
                    Performance Issues
                  </h4>


                  {
                    !review.performance
                      .issues ||
                    review.performance
                      .issues.length === 0

                      ? (

                        <p>
                          No verified performance
                          issues found.
                        </p>

                      )

                      : (

                        review.performance
                          .issues.map(
                            (
                              issue,
                              index
                            ) => (

                              <div
                                key={index}
                                style={{
                                  marginBottom:
                                    "25px",
                                  padding:
                                    "15px",
                                  border:
                                    "1px solid #444",
                                  borderRadius:
                                    "8px",
                                }}
                              >

                                <h4>
                                  {
                                    issue.title
                                  }
                                </h4>


                                {
                                  issue.description && (

                                    <p>

                                      <strong>
                                        Description:
                                      </strong>{" "}

                                      {
                                        issue.description
                                      }

                                    </p>

                                  )
                                }


                                {
                                  issue.file && (

                                    <p>

                                      <strong>
                                        File:
                                      </strong>{" "}

                                      {
                                        issue.file
                                      }

                                    </p>

                                  )
                                }


                                {
                                  issue.line !==
                                    null &&
                                  issue.line !==
                                    undefined && (

                                    <p>

                                      <strong>
                                        Line:
                                      </strong>{" "}

                                      {
                                        issue.line
                                      }

                                    </p>

                                  )
                                }


                                {
                                  issue.line_range && (

                                    <p>

                                      <strong>
                                        Lines:
                                      </strong>{" "}

                                      {
                                        issue.line_range
                                      }

                                    </p>

                                  )
                                }


                                {
                                  issue.evidence && (

                                    <p>

                                      <strong>
                                        Evidence:
                                      </strong>{" "}

                                      {
                                        issue.evidence
                                      }

                                    </p>

                                  )
                                }


                                {
                                  issue.impact && (

                                    <p>

                                      <strong>
                                        Impact:
                                      </strong>{" "}

                                      {
                                        issue.impact
                                      }

                                    </p>

                                  )
                                }


                                {
                                  issue.suggestion && (

                                    <p>

                                      <strong>
                                        Suggestion:
                                      </strong>{" "}

                                      {
                                        issue.suggestion
                                      }

                                    </p>

                                  )
                                }


                                <p>

                                  <strong>
                                    Confidence:
                                  </strong>{" "}

                                  {
                                    issue.confidence
                                  }%

                                </p>

                              </div>

                            )
                          )

                      )
                  }

                </>

              )
            }


            {/* =================================================
                SECURITY
            ================================================= */}

            {
              review.security && (

                <>

                  <h3>
                    Security
                  </h3>


                  <p>

                    <strong>
                      Issues Found:
                    </strong>{" "}

                    {
                      review.security
                        .issues_found
                    }

                  </p>


                  {
                    review.security
                      .issues?.length > 0

                      ? (

                        <ul>

                          {
                            review.security
                              .issues.map(
                                (
                                  issue,
                                  index
                                ) => (

                                  <li
                                    key={
                                      index
                                    }
                                  >
                                    {
                                      issue
                                    }
                                  </li>

                                )
                              )
                          }

                        </ul>

                      )

                      : (

                        <p>
                          No verified security
                          issues found.
                        </p>

                      )
                  }

                </>

              )
            }


            {/* =================================================
                CODE QUALITY
            ================================================= */}

            {
              review.code_quality && (

                <>

                  <h3>
                    Code Quality
                  </h3>


                  {
                    review.code_quality
                      .observations
                      ?.length > 0

                      ? (

                        <ul>

                          {
                            review.code_quality
                              .observations
                              .map(
                                (
                                  item,
                                  index
                                ) => (

                                  <li
                                    key={
                                      index
                                    }
                                  >
                                    {
                                      item
                                    }
                                  </li>

                                )
                              )
                          }

                        </ul>

                      )

                      : (

                        <p>
                          No code-quality
                          observations reported.
                        </p>

                      )
                  }


                  <h3>
                    Suggestions
                  </h3>


                  {
                    review.code_quality
                      .suggestions
                      ?.length > 0

                      ? (

                        <ul>

                          {
                            review.code_quality
                              .suggestions
                              .map(
                                (
                                  item,
                                  index
                                ) => (

                                  <li
                                    key={
                                      index
                                    }
                                  >
                                    {
                                      item
                                    }
                                  </li>

                                )
                              )
                          }

                        </ul>

                      )

                      : (

                        <p>
                          No code-quality
                          suggestions reported.
                        </p>

                      )
                  }

                </>

              )
            }


            {/* =================================================
                KEY METHODS
            ================================================= */}

            {
              review.key_methods
                ?.length > 0 && (

                <>

                  <h3>
                    Key Methods
                  </h3>

                  <ul>

                    {
                      review.key_methods.map(
                        (
                          method,
                          index
                        ) => (

                          <li
                            key={index}
                          >
                            {method}
                          </li>

                        )
                      )
                    }

                  </ul>

                </>

              )
            }


            {/* =================================================
                KEY CLASSES
            ================================================= */}

            {
              review.key_classes
                ?.length > 0 && (

                <>

                  <h3>
                    Key Classes
                  </h3>

                  <ul>

                    {
                      review.key_classes.map(
                        (
                          item,
                          index
                        ) => (

                          <li
                            key={index}
                          >
                            {item}
                          </li>

                        )
                      )
                    }

                  </ul>

                </>

              )
            }


            {/* =================================================
                LIBRARIES
            ================================================= */}

            {
              review.libraries
                ?.length > 0 && (

                <>

                  <h3>
                    Libraries
                  </h3>

                  <ul>

                    {
                      review.libraries.map(
                        (
                          library,
                          index
                        ) => (

                          <li
                            key={index}
                          >
                            {library}
                          </li>

                        )
                      )
                    }

                  </ul>

                </>

              )
            }


            {/* =================================================
                EXPECTED OUTPUT
            ================================================= */}

            {
              review.expected_output && (

                <>

                  <h3>
                    Expected Output
                  </h3>


                  <pre
                    style={{
                      whiteSpace:
                        "pre-wrap",
                      overflowWrap:
                        "break-word",
                    }}
                  >

                    {
                      review.expected_output
                    }

                  </pre>

                </>

              )
            }


            {/* =================================================
                SCORE
            ================================================= */}

            {
              review.score !== null &&
              review.score !== undefined && (

                <p>

                  <strong>
                    Score:
                  </strong>{" "}

                  {
                    review.score
                  }/10

                </p>

              )
            }


            {/* =================================================
                CONFIDENCE
            ================================================= */}

            <p>

              <strong>
                Analysis Confidence:
              </strong>{" "}

              {
                review.confidence
              }%

            </p>


            {/* =================================================
                FINAL VERDICT
            ================================================= */}

            {
              review.final_verdict && (

                <>

                  <h3>
                    Final Verdict
                  </h3>

                  <p>
                    {
                      review.final_verdict
                    }
                  </p>

                </>

              )
            }

          </div>

        )
      }

    </div>
  );
}


export default Review;