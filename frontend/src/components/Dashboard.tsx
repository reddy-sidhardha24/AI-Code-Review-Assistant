function Dashboard() {
  return (
    <div className="dashboard">

      <h1>Dashboard</h1>

      <div className="cards">

        <div className="card">
          <h2>Total Reviews</h2>
          <h1>120</h1>
          <p>Total code reviews completed.</p>
        </div>

        <div className="card">
          <h2>Average Score</h2>
          <h1>8.9/10</h1>
          <p>Average score of reviewed code.</p>
        </div>

        <div className="card">
          <h2>Bugs Found</h2>
          <h1>42</h1>
          <p>Total bugs detected by AI.</p>
        </div>

        <div className="card">
          <h2>Security Issues</h2>
          <h1>18</h1>
          <p>Security issues identified.</p>
        </div>

      </div>

    </div>
  );
}

export default Dashboard;