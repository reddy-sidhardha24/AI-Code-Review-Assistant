import { useRef, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import API from "../api";

type UploadType =
  | "zip"
  | "files"
  | "paste"
  | "github";

/* ============================================================
   CONSTANTS
   ============================================================ */

const MAX_ZIP_SIZE = 50 * 1024 * 1024;
const MAX_FILE_SIZE = 5 * 1024 * 1024;
const MAX_FILE_COUNT = 50;

const SOURCE_EXTENSIONS = [
  ".py", ".js", ".jsx", ".ts", ".tsx",
  ".java", ".c", ".h", ".cpp", ".cc", ".hpp",
  ".cs", ".go", ".rs", ".php", ".rb",
  ".swift", ".kt", ".kts", ".dart", ".scala",
  ".sh", ".bash", ".sql",
  ".html", ".htm", ".css", ".scss", ".sass", ".vue",
  ".json", ".xml", ".yml", ".yaml", ".md",
];

const ACCEPT_SOURCE =
  SOURCE_EXTENSIONS.join(",");

/* ============================================================
   HELPERS
   ============================================================ */

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024)
    return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / 1024 / 1024).toFixed(2) + " MB";
}

function getExtension(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot >= 0 ? name.slice(dot).toLowerCase() : "";
}

/* ============================================================
   COMPONENT
   ============================================================ */

function Upload() {
  const navigate = useNavigate();

  const zipInputRef =
    useRef<HTMLInputElement | null>(null);

  const filesInputRef =
    useRef<HTMLInputElement | null>(null);

  const [uploadType, setUploadType] =
    useState<UploadType>("zip");

  const [zipFile, setZipFile] =
    useState<File | null>(null);

  const [files, setFiles] =
    useState<File[]>([]);

  const [githubUrl, setGithubUrl] =
    useState("");

  const [filename, setFilename] =
    useState("main.py");

  const [code, setCode] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [status, setStatus] =
    useState("");

  const [message, setMessage] =
    useState("");

  const [messageType, setMessageType] =
    useState<"success" | "error" | "">("");

  const [dragActive, setDragActive] =
    useState(false);

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
    setStatus("");
  };

  /* ============================================================
     VALIDATE ZIP FILE
     ============================================================ */

  const validateZipFile = (
    file: File
  ): string | null => {

    if (
      !file.name
        .toLowerCase()
        .endsWith(".zip")
    ) {
      return "Please select a valid ZIP file.";
    }

    if (file.size > MAX_ZIP_SIZE) {
      return (
        `ZIP file is too large ` +
        `(${formatSize(file.size)}). ` +
        `Maximum is 50 MB.`
      );
    }

    if (file.size === 0) {
      return "ZIP file is empty.";
    }

    return null;
  };

  /* ============================================================
     VALIDATE SOURCE FILES
     ============================================================ */

  const validateSourceFiles = (
    fileList: File[]
  ): string | null => {

    if (fileList.length === 0) {
      return "No files selected.";
    }

    if (fileList.length > MAX_FILE_COUNT) {
      return (
        `Too many files (${fileList.length}). ` +
        `Maximum is ${MAX_FILE_COUNT}.`
      );
    }

    for (const file of fileList) {

      const ext = getExtension(file.name);

      if (!SOURCE_EXTENSIONS.includes(ext)) {
        return (
          `Unsupported file type: ` +
          `${file.name} (${ext})`
        );
      }

      if (file.size > MAX_FILE_SIZE) {
        return (
          `File too large: ${file.name} ` +
          `(${formatSize(file.size)}). ` +
          `Maximum is 5 MB per file.`
        );
      }
    }

    return null;
  };

  /* ============================================================
     UPLOAD
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
        setMessage("Please enter a filename.");
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
      setStatus("Indexing code...");

      try {
        const response = await API.post(
          "/paste-code",
          {
            filename: trimmedFilename,
            code: trimmedCode,
          }
        );

        setStatus("");
        setMessage(
          response.data?.message ??
            "Code indexed successfully."
        );
        setMessageType("success");

        setTimeout(() => {
          navigate("/review");
        }, 1000);
      } catch (error: any) {
        setStatus("");
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
       GITHUB
       ========================================================== */

    if (uploadType === "github") {
      const trimmedUrl = githubUrl.trim();

      if (!trimmedUrl) {
        setMessage(
          "Please enter a GitHub repository URL."
        );
        setMessageType("error");
        return;
      }

      if (
        !trimmedUrl.includes("github.com/")
      ) {
        setMessage(
          "Please enter a valid GitHub URL. " +
          "Example: https://github.com/owner/repo"
        );
        setMessageType("error");
        return;
      }

      setLoading(true);
      setStatus("Downloading repository...");

      try {
        const response = await API.post(
          "/upload-github",
          { repo_url: trimmedUrl }
        );

        setStatus("");
        setMessage(
          response.data?.message ??
            "Repository downloaded successfully."
        );
        setMessageType("success");

        setTimeout(() => {
          navigate("/review");
        }, 1000);
      } catch (error: any) {
        setStatus("");
        setMessage(
          error.response?.data?.detail ??
            "Failed to download GitHub repository."
        );
        setMessageType("error");
      } finally {
        setLoading(false);
      }

      return;
    }

    /* ==========================================================
       FILE UPLOADS (ZIP, Source Files)
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

        const zipError = validateZipFile(zipFile);
        if (zipError) {
          setMessage(zipError);
          setMessageType("error");
          return;
        }

        formData.append("file", zipFile);
        setLoading(true);
        setStatus(
          `Uploading ${zipFile.name} ` +
          `(${formatSize(zipFile.size)})...`
        );

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

        setStatus("");
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

      const filesError = validateSourceFiles(
        files
      );
      if (filesError) {
        setMessage(filesError);
        setMessageType("error");
        return;
      }

      files.forEach((file) => {
        formData.append("files", file);
      });

      setLoading(true);
      setStatus(
        `Uploading ${files.length} file` +
        `${files.length !== 1 ? "s" : ""}...`
      );

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

      setStatus("");
      setMessage(
        response.data?.message ??
          "Source files uploaded successfully."
      );
      setMessageType("success");

      setTimeout(() => {
        navigate("/review");
      }, 1000);
    } catch (error: any) {
      setStatus("");
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
     FILE CHANGE HANDLERS
     ============================================================ */

  const handleZipChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selected = event.target.files?.[0];
    if (!selected) return;

    const error = validateZipFile(selected);
    if (error) {
      setMessage(error);
      setMessageType("error");
      return;
    }

    setZipFile(selected);
    clearMessage();
  };

  const handleFilesChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    if (!event.target.files) return;

    const selectedFiles = Array.from(
      event.target.files
    );
    if (selectedFiles.length === 0) return;

    const error = validateSourceFiles(
      selectedFiles
    );
    if (error) {
      setMessage(error);
      setMessageType("error");
      return;
    }

    setFiles(selectedFiles);
    clearMessage();
  };

  /* ============================================================
     REMOVE FILE
     ============================================================ */

  const removeFile = (index: number) => {
    setFiles((prev) =>
      prev.filter((_, i) => i !== index)
    );
    clearMessage();
  };

  /* ============================================================
     FILE PICKER
     ============================================================ */

  const openFilePicker = () => {
    if (uploadType === "zip")
      zipInputRef.current?.click();
    else
      filesInputRef.current?.click();
  };

  /* ============================================================
     DRAG AND DROP
     ============================================================ */

  const handleDragOver = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      setDragActive(true);
    },
    []
  );

  const handleDragLeave = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      setDragActive(false);
    },
    []
  );

  const handleDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      event.stopPropagation();
      setDragActive(false);

      const droppedFiles = Array.from(
        event.dataTransfer.files
      );

      if (droppedFiles.length === 0) return;

      if (uploadType === "zip") {
        const file = droppedFiles[0];
        const error = validateZipFile(file);
        if (error) {
          setMessage(error);
          setMessageType("error");
          return;
        }
        setZipFile(file);
        clearMessage();
      } else if (uploadType === "files") {
        const error = validateSourceFiles(
          droppedFiles
        );
        if (error) {
          setMessage(error);
          setMessageType("error");
          return;
        }
        setFiles(droppedFiles);
        clearMessage();
      }
    },
    [uploadType]
  );

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
     WHICH MODES SHOW A DROP ZONE
     ============================================================ */

  const showDropZone = (
    uploadType === "zip" ||
    uploadType === "files"
  );

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
            : uploadType === "github"
            ? "⚡"
            : "↑"}
        </div>

        <h2>
          {uploadType === "paste"
            ? "Paste your code"
            : uploadType === "github"
            ? "Analyze GitHub repository"
            : "Analyze your codebase"}
        </h2>

        <p>
          {uploadType === "paste"
            ? "Quickly analyze a source file with AI-powered code review."
            : uploadType === "github"
            ? "Enter a public GitHub repository URL to analyze."
            : "Upload a complete project, select source files, or paste code."}
        </p>

        {/* ======================================================
            MODE TABS
            ====================================================== */}

        <div className="upload-tabs">

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
              <strong>ZIP Project</strong>
              <small>Complete codebase</small>
            </div>
          </button>

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
              <strong>Source Files</strong>
              <small>Multiple files</small>
            </div>
          </button>

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
              <strong>Paste Code</strong>
              <small>Quick review</small>
            </div>
          </button>

          <button
            type="button"
            className={
              uploadType === "github"
                ? "upload-tab active"
                : "upload-tab"
            }
            onClick={() =>
              changeUploadType("github")
            }
            disabled={loading}
          >
            <span>⚡</span>
            <div>
              <strong>GitHub</strong>
              <small>Repository URL</small>
            </div>
          </button>

        </div>


        {/* ======================================================
            HIDDEN FILE INPUTS
            ====================================================== */}

        <input
          ref={zipInputRef}
          type="file"
          accept=".zip"
          onChange={handleZipChange}
          style={{ display: "none" }}
        />

        <input
          ref={filesInputRef}
          type="file"
          accept={ACCEPT_SOURCE}
          multiple
          onChange={handleFilesChange}
          style={{ display: "none" }}
        />


        {/* ======================================================
            DROP ZONE (ZIP, Source Files)
            ====================================================== */}

        {showDropZone && (
          <>
            <div
              className={
                "drop-zone" +
                (dragActive ? " drag-active" : "")
              }
              onClick={openFilePicker}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >

              <div className="drop-zone-icon">
                {uploadType === "zip"
                  ? "ZIP"
                  : "{ }"}
              </div>

              {/* ZIP */}
              {uploadType === "zip" && (
                zipFile ? (
                  <>
                    <h3>{zipFile.name}</h3>
                    <p>{formatSize(zipFile.size)}</p>
                  </>
                ) : (
                  <>
                    <h3>
                      {dragActive
                        ? "Drop your ZIP file here"
                        : "Choose your project ZIP"}
                    </h3>
                    <p>
                      {!dragActive &&
                        "Upload a complete codebase"}
                    </p>
                  </>
                )
              )}

              {/* Source Files */}
              {uploadType === "files" && (
                files.length > 0 ? (
                  <>
                    <h3>
                      {files.length} file
                      {files.length !== 1
                        ? "s"
                        : ""}{" "}
                      selected
                    </h3>
                    <p>Click to change selection</p>
                  </>
                ) : (
                  <>
                    <h3>
                      {dragActive
                        ? "Drop your source files here"
                        : "Select source files"}
                    </h3>
                    <p>
                      {!dragActive &&
                        "Python, Java, JavaScript, TypeScript, C++, Go and more"}
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
                SELECTED FILES LIST (Source Files mode)
                ================================================== */}

            {uploadType === "files" &&
              files.length > 0 && (

                <div className="selected-files">

                  <div className="selected-files-header">
                    <strong>Selected Files</strong>
                    <span>{files.length}</span>
                  </div>

                  {files
                    .slice(0, 10)
                    .map((file, index) => (

                      <div
                        className="selected-file"
                        key={`${file.name}-${file.size}-${index}`}
                      >
                        <span>FILE</span>

                        <span className="selected-file-name">
                          {file.name}
                        </span>

                        <span className="selected-file-size">
                          {formatSize(file.size)}
                        </span>

                        <button
                          type="button"
                          className="remove-file-button"
                          onClick={() =>
                            removeFile(index)
                          }
                          title="Remove file"
                        >
                          ✕
                        </button>
                      </div>

                    ))}

                  {files.length > 10 && (
                    <div className="more-files">
                      + {files.length - 10} more files
                    </div>
                  )}

                </div>
              )}

          </>
        )}


        {/* ======================================================
            GITHUB URL INPUT
            ====================================================== */}

        {uploadType === "github" && (

          <div className="github-input-container">

            <div className="paste-field">

              <label htmlFor="github-url">
                Repository URL
              </label>

              <input
                id="github-url"
                type="text"
                value={githubUrl}
                maxLength={500}
                placeholder="https://github.com/owner/repository"
                disabled={loading}
                onChange={(event) =>
                  setGithubUrl(
                    event.target.value
                  )
                }
              />

            </div>

            <p className="github-hint">
              Enter a public GitHub repository URL.
              The entire codebase will be downloaded
              and analyzed.
            </p>

          </div>
        )}


        {/* ======================================================
            PASTE CODE
            ====================================================== */}

        {uploadType === "paste" && (

          <div className="paste-code-container">

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
              {status || "Processing..."}
            </>
          ) : (
            <>
              {uploadType === "paste"
                ? "Analyze Code"
                : uploadType === "github"
                ? "Analyze Repository"
                : "Analyze Project"}
              <span> →</span>
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
          <span>Local processing</span>
          <span>•</span>
          <span>RAG-powered analysis</span>
          <span>•</span>
          <span>AI review</span>
        </div>

      </div>

    </section>
  );
}

export default Upload;