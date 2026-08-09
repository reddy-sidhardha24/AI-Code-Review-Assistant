import { FormEvent, useState } from "react";

function Contact() {
  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [message, setMessage] =
    useState("");

  const [submitted, setSubmitted] =
    useState(false);

  const handleSubmit = (
    event: FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    if (
      !name.trim() ||
      !email.trim() ||
      !message.trim()
    ) {
      return;
    }

    /*
     * Frontend-only contact form for now.
     *
     * A real submission endpoint can be
     * connected later.
     */

    setSubmitted(true);

    setName("");
    setEmail("");
    setMessage("");
  };

  return (
    <main className="contact-page-modern">

      <div className="container">

        {/* ==================================================
            HEADER
            ================================================== */}

        <section className="contact-hero">

          <div className="section-label">
            CONTACT
          </div>

          <h1>
            Let's talk about
            <span> CodeReview AI.</span>
          </h1>

          <p>
            Have a question about the project, RAG pipeline,
            code analysis, or the frontend? Send us a message.
          </p>

        </section>


        {/* ==================================================
            CONTACT CONTENT
            ================================================== */}

        <section className="contact-layout">

          {/* ==================================================
              INFORMATION
              ================================================== */}

          <div className="contact-information">

            <div className="contact-info-header">

              <span className="contact-info-icon">
                ✦
              </span>

              <div>

                <h2>
                  Project Information
                </h2>

                <p>
                  CodeReview AI is an academic AI project
                  focused on contextual automated code review.
                </p>

              </div>

            </div>


            {/* ----------------------------------------------
                CONTACT ITEMS
                ---------------------------------------------- */}

            <div className="contact-info-list">

              <div className="contact-info-item">

                <span className="contact-item-icon">
                  @
                </span>

                <div>

                  <span>
                    PROJECT
                  </span>

                  <strong>
                    CodeReview AI
                  </strong>

                </div>

              </div>


              <div className="contact-info-item">

                <span className="contact-item-icon">
                  AI
                </span>

                <div>

                  <span>
                    ARCHITECTURE
                  </span>

                  <strong>
                    RAG-Powered Analysis
                  </strong>

                </div>

              </div>


              <div className="contact-info-item">

                <span className="contact-item-icon">
                  #
                </span>

                <div>

                  <span>
                    BACKEND
                  </span>

                  <strong>
                    FastAPI + Python
                  </strong>

                </div>

              </div>


              <div className="contact-info-item">

                <span className="contact-item-icon">
                  ◈
                </span>

                <div>

                  <span>
                    FRONTEND
                  </span>

                  <strong>
                    React + TypeScript
                  </strong>

                </div>

              </div>

            </div>


            {/* ----------------------------------------------
                NOTE
                ---------------------------------------------- */}

            <div className="contact-note">

              <span>
                PROJECT NOTE
              </span>

              <p>
                This contact form is currently a frontend
                demonstration. Connecting it to an email
                or backend messaging service can be added
                later.
              </p>

            </div>

          </div>


          {/* ==================================================
              CONTACT FORM
              ================================================== */}

          <div className="contact-form-card">

            {!submitted ? (

              <>

                <div className="contact-form-header">

                  <span className="section-label">
                    SEND A MESSAGE
                  </span>

                  <h2>
                    How can we help?
                  </h2>

                  <p>
                    Fill in the details below and tell us
                    what you would like to know.
                  </p>

                </div>


                <form
                  onSubmit={handleSubmit}
                  className="contact-form"
                >

                  {/* ----------------------------------------
                      NAME
                      ---------------------------------------- */}

                  <div className="contact-field">

                    <label htmlFor="contact-name">
                      Name
                    </label>

                    <input
                      id="contact-name"
                      type="text"
                      placeholder="Your name"
                      value={name}
                      onChange={(event) =>
                        setName(
                          event.target.value
                        )
                      }
                      required
                    />

                  </div>


                  {/* ----------------------------------------
                      EMAIL
                      ---------------------------------------- */}

                  <div className="contact-field">

                    <label htmlFor="contact-email">
                      Email
                    </label>

                    <input
                      id="contact-email"
                      type="email"
                      placeholder="you@example.com"
                      value={email}
                      onChange={(event) =>
                        setEmail(
                          event.target.value
                        )
                      }
                      required
                    />

                  </div>


                  {/* ----------------------------------------
                      MESSAGE
                      ---------------------------------------- */}

                  <div className="contact-field">

                    <label htmlFor="contact-message">
                      Message
                    </label>

                    <textarea
                      id="contact-message"
                      rows={7}
                      placeholder="Tell us what you would like to know..."
                      value={message}
                      onChange={(event) =>
                        setMessage(
                          event.target.value
                        )
                      }
                      required
                    />

                  </div>


                  {/* ----------------------------------------
                      SUBMIT
                      ---------------------------------------- */}

                  <button
                    type="submit"
                    className="contact-submit-button"
                  >
                    Send Message
                    <span>→</span>
                  </button>

                </form>

              </>

            ) : (

              /* ============================================
                 SUCCESS STATE
                 ============================================ */

              <div className="contact-success">

                <div className="contact-success-icon">
                  ✓
                </div>

                <span className="section-label">
                  MESSAGE READY
                </span>

                <h2>
                  Thanks for reaching out.
                </h2>

                <p>
                  Your message has been captured by the
                  frontend demo. A real backend submission
                  service can be connected in the next phase.
                </p>

                <button
                  className="contact-secondary-button"
                  onClick={() =>
                    setSubmitted(false)
                  }
                >
                  Send Another Message
                </button>

              </div>

            )}

          </div>

        </section>


        {/* ==================================================
            PROJECT TOPICS
            ================================================== */}

        <section className="contact-topics">

          <div className="contact-topics-header">

            <div className="section-label">
              PROJECT TOPICS
            </div>

            <h2>
              Questions about the
              <span> system?</span>
            </h2>

          </div>


          <div className="contact-topic-grid">

            <div className="contact-topic">

              <span>
                01
              </span>

              <strong>
                RAG Pipeline
              </strong>

              <p>
                Questions about chunking, embeddings,
                vector search, or retrieval.
              </p>

            </div>


            <div className="contact-topic">

              <span>
                02
              </span>

              <strong>
                AI Review
              </strong>

              <p>
                Questions about prompts, structured
                responses, or review generation.
              </p>

            </div>


            <div className="contact-topic">

              <span>
                03
              </span>

              <strong>
                Frontend
              </strong>

              <p>
                Questions about the React interface,
                dashboard, review, and history.
              </p>

            </div>


            <div className="contact-topic">

              <span>
                04
              </span>

              <strong>
                Project Demo
              </strong>

              <p>
                Questions about the architecture,
                workflow, or project demonstration.
              </p>

            </div>

          </div>

        </section>

      </div>

    </main>
  );
}

export default Contact;