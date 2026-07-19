function History() {
  const history = [
    {
      id: 1,
      file: "app.py",
      language: "Python",
      score: "9/10",
      date: "14-07-2026",
    },
    {
      id: 2,
      file: "Home.tsx",
      language: "React",
      score: "8/10",
      date: "13-07-2026",
    },
    {
      id: 3,
      file: "main.java",
      language: "Java",
      score: "10/10",
      date: "12-07-2026",
    },
  ];

  return (
    <div className="history">
      <h1>Review History</h1>

      <table>
        <thead>
          <tr>
            <th>S.No</th>
            <th>File Name</th>
            <th>Language</th>
            <th>Score</th>
            <th>Date</th>
          </tr>
        </thead>

        <tbody>
          {history.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              <td>{item.file}</td>
              <td>{item.language}</td>
              <td>{item.score}</td>
              <td>{item.date}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default History;