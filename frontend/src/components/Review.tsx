import { useState } from "react";
import API from "../api";

function Review() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const askQuestion = async () => {
    if (!question.trim()) {
      alert("Please enter a question.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setError("");

    try {
      const res = await API.post("/review", {
        question,
      });

      if (res.data.answer) {
        setAnswer(res.data.answer);
      } else {
        setError("No response received.");
      }
    } catch (err: any) {
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError("Unable to connect to backend.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        width: "900px",
        margin: "40px auto",
      }}
    >
      <h1>AI Code Review Assistant</h1>

      <textarea
        rows={4}
        placeholder="Ask anything about the uploaded project..."
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        style={{
          width: "100%",
          padding: "12px",
          fontSize: "16px",
        }}
      />

      <br />
      <br />

      <button onClick={askQuestion}>
        Review Project
      </button>

      <br />
      <br />

      {loading && (
        <h3>Analyzing project...</h3>
      )}

      {error && (
        <div
          style={{
            color: "red",
            fontWeight: "bold",
          }}
        >
          {error}
        </div>
      )}

      {answer && (
        <div
          style={{
            marginTop: "30px",
            border: "1px solid #ddd",
            padding: "20px",
            borderRadius: "10px",
            whiteSpace: "pre-wrap",
            lineHeight: "1.8",
          }}
        >
          <h2>Review Result</h2>

          {answer}
        </div>
      )}
    </div>
  );
}

export default Review;