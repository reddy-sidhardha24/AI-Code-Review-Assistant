import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";

type UploadType = "zip" | "files" | "paste";

function Upload() {
  const navigate = useNavigate();

  const fileInputRef =
    useRef<HTMLInputElement | null>(null);

  const [uploadType, setUploadType] =
    useState<UploadType>("zip");

  const [zipFile, setZipFile] =
    useState<File | null>(null);

  const [files, setFiles] =
    useState<File[]>([]);

  const [filename, setFilename] =
    useState("main.py");

  const [code, setCode] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [messageType, setMessageType] =
    useState<"success" | "error" | "">("");

  /* ============================================================
     RESET MESSAGE
     ============================================================ */

  const clearMessage = () => {
    setMessage("");
    setMessageType("");
  };

  /* ============================================================
     CHANGE UPLOAD MODE
     ============================================================ */

  const changeUploadType = (
    type: UploadType
  ) => {
    setUploadType(type);
    clearMessage();

    if (type !== "zip") {
      setZipFile(null);
    }

    if (type !== "files") {
      setFiles([]);
    }
  };

  /* ============================================================
     UPLOAD / PASTE CODE
     ============================================================ */

  const upload = async () => {
    if (loading) {
      return;
    }

    clearMessage();

    /* ==========================================================
       PASTE CODE
       ========================================================== */

    if (uploadType === "paste") {
      const trimmedCode = code.trim();
      const trimmedFilename = filename.trim();

      if (!trimmedFilename) {
        setMessage(
          "Please enter a filename."
        );
        setMessageType("error");
        return;
      }

      if (!trimmedCode) {
        setMessage(
          "Please paste some source code first."
        );
        setMessageType("error");
        return;
      }

      setLoading(true);

      try {
        const response = await API.post(
          "/paste-code",
          {
            filename: trimmedFilename,
            code: trimmedCode,
          }
        );

        setMessage(
          response.data?.message ??
            "Code indexed successfully."
        );

        setMessageType("success");

        setTimeout(() => {
          navigate("/review");
        }, 1000);
      } catch (error: any) {
        console.error(
          "Paste code error:",
          error
        );

        setMessage(
          error.response?.data?.detail ??
            "Failed to process the pasted code."
        );

        setMessageType("error");
      } finally {
        setLoading(false);
      }

      return;
    }

    /* ==========================================================
       FILE UPLOAD
       ========================================================== */

    try {
      const formData = new FormData();

      /* ========================================================
         ZIP PROJECT
         ======================================================== */

      if (uploadType === "zip") {
        if (!zipFile) {
          setMessage(
            "Please select a ZIP project first."
          );
          setMessageType("error");
          return;
        }

        formData.append(
          "file",
          zipFile
        );

        setLoading(true);

        const response = await API.post(
          "/upload-project",
          formData,
          {
            headers: {
              "Content-Type":
                "multipart/form-data",
            },
          }
        );

        setMessage(
          response.data?.message ??
            "Project uploaded successfully."
        );

        setMessageType("success");

        setTimeout(() => {
          navigate("/review");
        }, 1000);

        return;
      }

      /* ========================================================
         MULTIPLE SOURCE FILES
         ======================================================== */

      if (files.length === 0) {
        setMessage(
          "Please select at least one source file."
        );
        setMessageType("error");
        return;
      }

      files.forEach((file) => {
        formData.append(
          "files",
          file
        );
      });

      setLoading(true);

      const response = await API.post(
        "/upload-files",
        formData,
        {
          headers: {
            "Content-Type":
              "multipart/form-data",
          },
        }
      );

      setMessage(
        response.data?.message ??
          "Source files uploaded successfully."
      );

      setMessageType("success");

      setTimeout(() => {
        navigate("/review");
      }, 1000);
    } catch (error: any) {
      console.error(
        "Upload error:",
        error
      );

      setMessage(
        error.response?.data?.detail ??
          "Upload failed. Please check the backend."
      );

      setMessageType("error");
    } finally {
      setLoading(false);
    }
  };

  /* ============================================================
     ZIP CHANGE
     ============================================================ */

  const handleZipChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selected =
      event.target.files?.[0];

    if (!selected) {
      return;
    }

    if (
      !selected.name
        .toLowerCase()
        .endsWith(".zip")
    ) {
      setMessage(
        "Please select a valid ZIP file."
      );
      setMessageType("error");
      return;
    }

    setZipFile(selected);
    clearMessage();
  };

  /* ============================================================
     SOURCE FILE CHANGE
     ============================================================ */

  const handleFilesChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (!event.target.files) {
      return;
    }

    const selectedFiles =
      Array.from(
        event.target.files
      );

    if (selectedFiles.length === 0) {
      return;
    }

    setFiles(selectedFiles);
    clearMessage();
  };

  /* ============================================================
     FILE PICKER
     ============================================================ */

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  /* ============================================================
     PASTE CODE EXAMPLE
     ============================================================ */

  const loadExampleCode = () => {
    setFilename("main.py");

    setCode(
`def divide(a, b):
    password = "admin123"

    for i in range(10):
        for j in range(10):
            print(i, j)

    return a / b


print(divide(10, 0))`
    );

    clearMessage();
  };

  /* ============================================================
     RENDER
     ============================================================ */

  return (
    <section className="upload-container">

      <div className="upload-box">

        {/* ======================================================
            HEADER
            ====================================================== */}

        <div className="upload-icon">
          {uploadType === "paste"
            ? "</>"
            : "↑"}
        </div>

        <h2>
          {uploadType === "paste"
            ? "Paste your code"
            : "Analyze your codebase"}
        </h2>

        <p>
          {uploadType === "paste"
            ? "Quickly analyze a source file with AI-powered code review."
            : "Upload a complete project, select source files, or paste code."}
        </p>

        {/* ======================================================
            MODE TABS
            ====================================================== */}

        <div className="upload-tabs">

          {/* ZIP */}

          <button
            type="button"
            className={
              uploadType === "zip"
                ? "upload-tab active"
                : "upload-tab"
            }
            onClick={() =>
              changeUploadType("zip")
            }
            disabled={loading}
          >
            <span>ZIP</span>

            <div>
              <strong>
                ZIP Project
              </strong>

              <small>
                Complete codebase
              </small>
            </div>
          </button>


          {/* SOURCE FILES */}

          <button
            type="button"
            className={
              uploadType === "files"
                ? "upload-tab active"
                : "upload-tab"
            }
            onClick={() =>
              changeUploadType("files")
            }
            disabled={loading}
          >
            <span>{"{ }"}</span>

            <div>
              <strong>
                Source Files
              </strong>

              <small>
                Multiple files
              </small>
            </div>
          </button>


          {/* PASTE CODE */}

          <button
            type="button"
            className={
              uploadType === "paste"
                ? "upload-tab active"
                : "upload-tab"
            }
            onClick={() =>
              changeUploadType("paste")
            }
            disabled={loading}
          >
            <span>&lt;/&gt;</span>

            <div>
              <strong>
                Paste Code
              </strong>

              <small>
                Quick review
              </small>
            </div>
          </button>

        </div>


        {/* ======================================================
            ZIP / SOURCE FILE INPUT
            ====================================================== */}

        {uploadType !== "paste" && (
          <>

            <input
              ref={fileInputRef}
              type="file"
              accept={
                uploadType === "zip"
                  ? ".zip"
                  : `
                    .py,
                    .java,
                    .cpp,
                    .c,
                    .js,
                    .ts,
                    .tsx,
                    .jsx,
                    .cs,
                    .go,
                    .php,
                    .rb,
                    .swift,
                    .kt,
                    .rs
                  `
              }
              multiple={
                uploadType === "files"
              }
              onChange={
                uploadType === "zip"
                  ? handleZipChange
                  : handleFilesChange
              }
              style={{
                display: "none",
              }}
            />

            {/* ==================================================
                DROP / FILE AREA
                ================================================== */}

            <div
              className="drop-zone"
              onClick={openFilePicker}
            >

              <div className="drop-zone-icon">
                {uploadType === "zip"
                  ? "ZIP"
                  : "{ }"}
              </div>

              {uploadType === "zip" ? (
                zipFile ? (
                  <>
                    <h3>
                      {zipFile.name}
                    </h3>

                    <p>
                      {(
                        zipFile.size /
                        1024 /
                        1024
                      ).toFixed(2)}{" "}
                      MB
                    </p>
                  </>
                ) : (
                  <>
                    <h3>
                      Choose your project ZIP
                    </h3>

                    <p>
                      Upload a complete
                      codebase
                    </p>
                  </>
                )
              ) : (
                files.length > 0 ? (
                  <>
                    <h3>
                      {files.length} file
                      {files.length !== 1
                        ? "s"
                        : ""}{" "}
                      selected
                    </h3>

                    <p>
                      Click to change
                      selection
                    </p>
                  </>
                ) : (
                  <>
                    <h3>
                      Select source files
                    </h3>

                    <p>
                      Python, Java,
                      JavaScript,
                      TypeScript, C++,
                      Go and more
                    </p>
                  </>
                )
              )}

              <button
                type="button"
                className="secondary-button browse-button"
                onClick={(event) => {
                  event.stopPropagation();
                  openFilePicker();
                }}
              >
                Browse Files
              </button>

            </div>


            {/* ==================================================
                SELECTED FILES
                ================================================== */}

            {uploadType === "files" &&
              files.length > 0 && (

                <div className="selected-files">

                  <div className="selected-files-header">

                    <strong>
                      Selected Files
                    </strong>

                    <span>
                      {files.length}
                    </span>

                  </div>

                  {files
                    .slice(0, 5)
                    .map((file) => (

                      <div
                        className="selected-file"
                        key={`${file.name}-${file.size}`}
                      >
                        <span>
                          FILE
                        </span>

                        <span>
                          {file.name}
                        </span>
                      </div>

                    ))}

                  {files.length > 5 && (
                    <div className="more-files">
                      + {files.length - 5} more files
                    </div>
                  )}

                </div>
              )}

          </>
        )}


        {/* ======================================================
            PASTE CODE
            ====================================================== */}

        {uploadType === "paste" && (

          <div className="paste-code-container">

            {/* Filename */}

            <div className="paste-field">

              <label htmlFor="paste-filename">
                Filename
              </label>

              <input
                id="paste-filename"
                type="text"
                value={filename}
                maxLength={255}
                placeholder="main.py"
                disabled={loading}
                onChange={(event) =>
                  setFilename(
                    event.target.value
                  )
                }
              />

            </div>


            {/* Code */}

            <div className="paste-field">

              <div className="paste-code-header">

                <label htmlFor="paste-code">
                  Source Code
                </label>

                <span>
                  {code.length} characters
                </span>

              </div>

              <textarea
                id="paste-code"
                className="paste-code-editor"
                value={code}
                disabled={loading}
                placeholder={`Paste your source code here...

Example:

def divide(a, b):
    return a / b

print(divide(10, 0))`}
                onChange={(event) =>
                  setCode(
                    event.target.value
                  )
                }
              />

            </div>


            {/* Example */}

            <button
              type="button"
              className="example-code-button"
              onClick={loadExampleCode}
              disabled={loading}
            >
              Load Demo Code
            </button>

          </div>
        )}


        {/* ======================================================
            ANALYZE BUTTON
            ====================================================== */}

        <button
          type="button"
          className="primary-button analyze-button"
          onClick={upload}
          disabled={loading}
        >

          {loading ? (
            <>
              <span className="button-spinner" />
              {uploadType === "paste"
                ? "Indexing Code..."
                : "Indexing Project..."}
            </>
          ) : (
            <>
              {uploadType === "paste"
                ? "Analyze Code"
                : "Analyze Project"}

              <span>
                →
              </span>
            </>
          )}

        </button>


        {/* ======================================================
            STATUS
            ====================================================== */}

        {message && (

          <div
            className={`upload-message ${messageType}`}
          >
            {message}
          </div>

        )}


        {/* ======================================================
            INFO
            ====================================================== */}

        <div className="upload-info">

          <span>
            Local processing
          </span>

          <span>
            •
          </span>

          <span>
            RAG-powered analysis
          </span>

          <span>
            •
          </span>

          <span>
            AI review
          </span>

        </div>

      </div>

    </section>
  );
}

export default Upload;