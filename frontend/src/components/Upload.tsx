import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Upload() {
  const navigate = useNavigate();

  const [uploadType, setUploadType] = useState<"zip" | "files">("zip");

  const [zipFile, setZipFile] = useState<File | null>(null);

  const [files, setFiles] = useState<File[]>([]);

  const [loading, setLoading] = useState(false);

  const [message, setMessage] = useState("");

  const upload = async () => {
    try {
      setLoading(true);

      const formData = new FormData();

      let url = "";

      if (uploadType === "zip") {
        if (!zipFile) {
          alert("Please select a ZIP file.");
          return;
        }

        formData.append("file", zipFile);

        url = "http://127.0.0.1:8000/upload-project";
      } else {
        if (files.length === 0) {
          alert("Please select source files.");
          return;
        }

        files.forEach((file) => {
          formData.append("files", file);
        });

        url = "http://127.0.0.1:8000/upload-files";
      }

      setMessage("Uploading project...");

      const response = await axios.post(url, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setMessage("✅ " + response.data.message);

      setTimeout(() => {
        navigate("/review");
      }, 1500);

    } catch (error: any) {

      setMessage(
        "❌ " +
          (error.response?.data?.detail ??
            "Upload failed.")
      );

    } finally {

      setLoading(false);

    }
  };

  return (
    <div
      style={{
        width: "700px",
        margin: "40px auto",
        padding: "30px",
        border: "1px solid #ddd",
        borderRadius: "12px",
        textAlign: "center",
      }}
    >
      <h2>Upload Project</h2>

      <div
        style={{
          marginBottom: "25px",
        }}
      >
        <label>
          <input
            type="radio"
            checked={uploadType === "zip"}
            onChange={() => setUploadType("zip")}
          />

          ZIP Project
        </label>

        <span style={{ marginLeft: 20 }} />

        <label>
          <input
            type="radio"
            checked={uploadType === "files"}
            onChange={() => setUploadType("files")}
          />

          Source Files
        </label>
      </div>

      {uploadType === "zip" ? (
        <>
          <p>Select your project ZIP.</p>

          <input
            type="file"
            accept=".zip"
            onChange={(e) => {
              if (e.target.files?.length) {
                setZipFile(e.target.files[0]);
              }
            }}
          />
        </>
      ) : (
        <>
          <p>Select one or more source files.</p>

          <input
            type="file"
            multiple
            accept=".py,.java,.cpp,.c,.js,.ts,.tsx,.jsx,.cs,.go,.php,.rb,.swift,.kt,.rs"
            onChange={(e) => {
              if (e.target.files) {
                setFiles(Array.from(e.target.files));
              }
            }}
          />

          <div
            style={{
              marginTop: 15,
              textAlign: "left",
            }}
          >
            {files.map((file) => (
              <div key={file.name}>
                📄 {file.name}
              </div>
            ))}
          </div>
        </>
      )}

      <br />

      <button
        onClick={upload}
        disabled={loading}
        style={{
          padding: "10px 25px",
          fontSize: "16px",
        }}
      >
        {loading ? "Uploading..." : "Upload"}
      </button>

      <br />
      <br />

      {message && (
        <h4
          style={{
            color: message.startsWith("✅")
              ? "green"
              : "red",
          }}
        >
          {message}
        </h4>
      )}
    </div>
  );
}

export default Upload;