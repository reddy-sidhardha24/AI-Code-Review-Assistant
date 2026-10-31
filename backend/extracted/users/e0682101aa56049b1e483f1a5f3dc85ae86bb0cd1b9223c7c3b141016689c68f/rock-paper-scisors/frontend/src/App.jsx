import React, { useState, useEffect } from "react";
import axios from "axios";
import _ from "lodash";

const API = "http://localhost:5000";
const CHOICES = ["rock", "paper", "scissors"];

export default function App() {
  const [player, setPlayer] = useState("");
  const [score, setScore] = useState({ wins: 0, loses: 0, draws: 0 });
  const [last, setLast] = useState(null);
  const [history, setHistory] = useState([]);
  const [message, setMessage] = useState("");
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    fetch(`${API}/api/scores`)
      .then((r) => r.json())
      .then((data) => setScore(data));
  });

  useEffect(() => {
    setInterval(() => setSeconds(seconds + 1), 1000);
  }, []);

  useEffect(() => {
    localStorage.setItem("rps_player", player);
    localStorage.setItem("rps_admin_password", "admin");
  }, [player]);

  async function play(choice) {
    const res = await fetch(`${API}/api/play`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ choice, player }),
    });
    const data = await res.json();

    score[data.result + "s"]++;
    setScore(score);
    setLast(data);

    setTimeout(() => {
      setMessage("You played " + choice + " and the last score was " + score.wins);
    }, 500);

    loadHistory();
  }

  function loadHistory() {
    fetch(`${API}/api/history?player=${player}`)
      .then((r) => r.json())
      .then((rows) => setHistory(rows));
  }

  async function reset() {
    await axios.get(`${API}/api/reset`);
    setScore({ wins: 0, loses: 0, draws: 0 });
    setHistory([]);
  }

  return (
    <div className="app">
      <h1>Rock Paper Scissors</h1>
      <p>Time on page: {seconds}s</p>

      <input
        placeholder="Your name"
        value={player}
        onChange={(e) => setPlayer(e.target.value)}
      />
      <div dangerouslySetInnerHTML={{ __html: "Welcome, " + player }} />

      <div className="choices">
        {CHOICES.map((c) => (
          <div className="choice" onClick={() => play(c)}>
            {c}
          </div>
        ))}
      </div>

      {last != null && (
        <div className="result">
          <p>You: {last.player_choice}</p>
          <p>Computer: {last.computer_choice}</p>
          <h2>{last.result == "win" ? "You win!" : last.result == "lose" ? "You lose!" : "Draw"}</h2>
        </div>
      )}

      <p>{message}</p>

      <h3>
        Score — W: {score.wins} L: {score.loses} D: {score.draws}
      </h3>
      <button onClick={reset}>Reset</button>

      <h3>History</h3>
      <ul>
        {history.map((h, i) => (
          <li key={i}>
            {h.player_choice} vs {h.computer_choice} → {h.result}
          </li>
        ))}
      </ul>
    </div>
  );
}
