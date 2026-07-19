import Upload from "../components/Upload";

function Home() {
  return (
    <div className="home-container">
      <div className="home-card">
        <h1>AI Code Review Assistant</h1>

        <p>
          Upload a ZIP file of your project. The system will build a vector
          database and prepare it for AI-powered code review.
        </p>

        <Upload />
      </div>
    </div>
  );
}

export default Home;