import { FormEvent, useState } from "react";
import { sendContactMessage } from "../api";

function Contact() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!name.trim() || !email.trim() || !message.trim()) {
      setFeedback({ type: "error", text: "Please fill in all required fields." });
      return;
    }

    setLoading(true);
    setFeedback(null);

    try {
      const res = await sendContactMessage({
        name: name.trim(),
        email: email.trim(),
        subject: subject.trim() || "General Inquiry",
        message: message.trim(),
      });

      if (res.data?.success) {
        setFeedback({
          type: "success",
          text: res.data.message || "Thank you! Your message has been sent successfully to our team.",
        });
        setName("");
        setEmail("");
        setSubject("");
        setMessage("");
      } else {
        setFeedback({
          type: "error",
          text: res.data?.error || "Could not deliver message. Please try again.",
        });
      }
    } catch (err: any) {
      setFeedback({
        type: "error",
        text: err.response?.data?.detail || "An error occurred while sending your message. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="contact-container">
      <div className="contact-card">
        <div className="contact-header">
          <div className="section-label">GET IN TOUCH</div>
          <h1>Contact Us</h1>
          <p>
            Have questions about CodeReview AI, need custom integrations, or want to discuss enterprise deployments? Send us a message directly.
          </p>
        </div>

        {feedback && (
          <div
            className={`alert ${feedback.type === "success" ? "alert-success" : "alert-error"}`}
            style={{ marginBottom: "24px" }}
          >
            {feedback.text}
          </div>
        )}

        <form className="contact-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label>Your Name *</label>
              <input
                type="text"
                placeholder="Jane Doe"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label>Email Address *</label>
              <input
                type="email"
                placeholder="jane@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="form-group full-width">
              <label>Subject</label>
              <input
                type="text"
                placeholder="Feature inquiry, bug report, or partnership"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              />
            </div>

            <div className="form-group full-width">
              <label>Message *</label>
              <textarea
                rows={5}
                placeholder="Tell us how we can help..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                required
              />
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "12px" }}>
            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ minWidth: "160px" }}
            >
              {loading ? "Sending..." : "Send Message →"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}

export default Contact;