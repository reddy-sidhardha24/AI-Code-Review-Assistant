import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

function Upload() {
  const navigate = useNavigate();

  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const uploadProject = async () => {
    if (!file) {
      alert("Please select a ZIP file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setMessage("Uploading project and building vector database...");

      const response = await axios.post(
        "http://127.0.0.1:8000/upload-project",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setMessage("✅ " + response.data.message);

      // Navigate to Review page after a short delay
      setTimeout(() => {
        navigate("/review");
      }, 1500);

    } catch (error: any) {
      setMessage(
        "❌ " +
          (error.response?.data?.detail ||
            "Failed to upload project.")
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        width: "600px",
        margin: "40px auto",
        textAlign: "center",
        padding: "20px",
        border: "1px solid #ddd",
        borderRadius: "10px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
      }}
    >
      <h2>Upload Project</h2>

      <p>Select a ZIP file containing your project.</p>

      <input
        type="file"
        accept=".zip"
        onChange={(e) => {
          if (e.target.files && e.target.files.length > 0) {
            setFile(e.target.files[0]);
          }
        }}
      />

      <br />
      <br />

      <button
        onClick={uploadProject}
        disabled={loading}
        style={{
          padding: "10px 20px",
          fontSize: "16px",
          cursor: loading ? "not-allowed" : "pointer",
        }}
      >
        {loading ? "Uploading..." : "Upload Project"}
      </button>

      <br />
      <br />

      {message && (
        <p
          style={{
            fontWeight: "bold",
            color: message.startsWith("✅") ? "green" : "red",
          }}
        >
          {message}
        </p>
      )}
    </div>
  );
}

export default Upload;