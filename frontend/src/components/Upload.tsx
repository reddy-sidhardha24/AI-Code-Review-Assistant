import { useRef, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Upload() {
  const navigate = useNavigate();

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [uploadType, setUploadType] =
    useState<"zip" | "files">("zip");

  const [zipFile, setZipFile] =
    useState<File | null>(null);

  const [files, setFiles] =
    useState<File[]>([]);

  const [loading, setLoading] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const upload = async () => {
    if (loading) {
      return;
    }

    try {
      const formData = new FormData();

      let url = "";

      if (uploadType === "zip") {
        if (!zipFile) {
          setMessage("Please select a ZIP project first.");
          return;
        }

        formData.append("file", zipFile);

        url =
          "http://127.0.0.1:8000/upload-project";
      } else {
        if (files.length === 0) {
          setMessage("Please select at least one source file.");
          return;
        }

        files.forEach((file) => {
          formData.append("files", file);
        });

        url =
          "http://127.0.0.1:8000/upload-files";
      }

      setLoading(true);
      setMessage("");

      const response = await axios.post(
        url,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setMessage(
        response.data?.message ??
          "Project uploaded successfully."
      );

      setTimeout(() => {
        navigate("/review");
      }, 1000);
    } catch (error: any) {
      console.error("Upload error:", error);

      setMessage(
        error.response?.data?.detail ??
          "Upload failed. Please check the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleZipChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selected =
      event.target.files?.[0];

    if (!selected) {
      return;
    }

    if (!selected.name.toLowerCase().endsWith(".zip")) {
      setMessage("Please select a valid ZIP file.");
      return;
    }

    setZipFile(selected);
    setMessage("");
  };

  const handleFilesChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (!event.target.files) {
      return;
    }

    const selectedFiles =
      Array.from(event.target.files);

    setFiles(selectedFiles);
    setMessage("");
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  return (
    <section className="upload-container">
      <div className="upload-box">
        <div className="upload-icon">
          ↑
        </div>

        <h2>
          Analyze your codebase
        </h2>

        <p>
          Upload a complete project or select
          individual source files.
        </p>

        {/* Upload Type */}
        <div className="upload-tabs">
          <button
            type="button"
            className={
              uploadType === "zip"
                ? "upload-tab active"
                : "upload-tab"
            }
            onClick={() => {
              setUploadType("zip");
              setMessage("");
            }}
          >
            <span>📦</span>

            <div>
              <strong>ZIP Project</strong>
              <small>
                Complete codebase
              </small>
            </div>
          </button>

          <button
            type="button"
            className={
              uploadType === "files"
                ? "upload-tab active"
                : "upload-tab"
            }
            onClick={() => {
              setUploadType("files");
              setMessage("");
            }}
          >
            <span>📄</span>

            <div>
              <strong>Source Files</strong>
              <small>
                Individual files
              </small>
            </div>
          </button>
        </div>

        {/* Hidden Input */}
        {uploadType === "zip" ? (
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip"
            onChange={handleZipChange}
            style={{ display: "none" }}
          />
        ) : (
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="
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
            "
            onChange={handleFilesChange}
            style={{ display: "none" }}
          />
        )}

        {/* Selected Project */}
        <div
          className="drop-zone"
          onClick={openFilePicker}
        >
          <div className="drop-zone-icon">
            {uploadType === "zip"
              ? "📦"
              : "📁"}
          </div>

          {uploadType === "zip" ? (
            <>
              {zipFile ? (
                <>
                  <h3>
                    {zipFile.name}
                  </h3>

                  <p>
                    {(zipFile.size / 1024 / 1024).toFixed(
                      2
                    )}{" "}
                    MB
                  </p>
                </>
              ) : (
                <>
                  <h3>
                    Choose your project ZIP
                  </h3>

                  <p>
                    Click here to browse your
                    computer
                  </p>
                </>
              )}
            </>
          ) : (
            <>
              {files.length > 0 ? (
                <>
                  <h3>
                    {files.length} file
                    {files.length !== 1
                      ? "s"
                      : ""}{" "}
                    selected
                  </h3>

                  <p>
                    Click to change selection
                  </p>
                </>
              ) : (
                <>
                  <h3>
                    Select source files
                  </h3>

                  <p>
                    Python, Java, JavaScript,
                    TypeScript, C++, Go and more
                  </p>
                </>
              )}
            </>
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

        {/* Selected Files */}
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

              {files.slice(0, 5).map(
                (file) => (
                  <div
                    className="selected-file"
                    key={
                      `${file.name}-${file.size}`
                    }
                  >
                    <span>📄</span>

                    <span>
                      {file.name}
                    </span>
                  </div>
                )
              )}

              {files.length > 5 && (
                <div className="more-files">
                  + {files.length - 5} more files
                </div>
              )}
            </div>
          )}

        {/* Analyze */}
        <button
          type="button"
          className="primary-button analyze-button"
          onClick={upload}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="button-spinner"></span>
              Indexing Project...
            </>
          ) : (
            <>
              ✨ Analyze Project
            </>
          )}
        </button>

        {/* Status */}
        {message && (
          <div
            className={
              message.toLowerCase().includes("failed") ||
              message.toLowerCase().includes("please")
                ? "upload-message error"
                : "upload-message success"
            }
          >
            {message}
          </div>
        )}

        <div className="upload-info">
          <span>🔒 Your code stays local</span>
          <span>•</span>
          <span>⚡ RAG-powered analysis</span>
          <span>•</span>
          <span>🤖 AI review</span>
        </div>
      </div>
    </section>
  );
}

export default Upload;