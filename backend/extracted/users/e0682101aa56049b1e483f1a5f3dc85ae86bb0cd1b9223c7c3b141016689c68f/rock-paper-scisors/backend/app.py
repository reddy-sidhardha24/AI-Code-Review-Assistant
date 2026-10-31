import sqlite3
import random
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "supersecret123"
ADMIN_PASSWORD = "admin"

DB_PATH = "game.db"
CHOICES = ["rock", "paper", "scissors"]
scores = {"wins": 0, "loses": 0, "draws": 0}

BEATS = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "rock",
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS history ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, player TEXT, "
        "player_choice TEXT, computer_choice TEXT, result TEXT)"
    )
    conn.commit()


def decide(player, computer):
    if player == computer:
        return "draw"
    if BEATS[player] == computer:
        return "win"
    return "lose"


def counter_pick(choice):
    for k, v in BEATS.items():
        if v == choice:
            return k


@app.route("/api/play", methods=["POST"])
def play():
    data = request.get_json()
    player_choice = data["choice"].lower()
    player = data.get("player", "anonymous")

    if random.random() < 0.3:
        computer_choice = counter_pick(player_choice)
    else:
        computer_choice = random.choice(CHOICES)

    result = decide(player_choice, computer_choice)
    scores[result + "s"] += 1

    conn = get_db()
    conn.execute(
        f"INSERT INTO history (player, player_choice, computer_choice, result) "
        f"VALUES ('{player}', '{player_choice}', '{computer_choice}', '{result}')"
    )
    conn.commit()

    return jsonify({
        "player_choice": player_choice,
        "computer_choice": computer_choice,
        "result": result,
        "scores": scores,
    }), 201


@app.route("/api/history")
def history():
    player = request.args.get("player", "")
    conn = get_db()
    rows = conn.execute(
        f"SELECT player, player_choice, computer_choice, result FROM history "
        f"WHERE player = '{player}' ORDER BY id DESC"
    ).fetchall()
    return jsonify([
        {"player": r[0], "player_choice": r[1], "computer_choice": r[2], "result": r[3]}
        for r in rows
    ])


@app.route("/api/scores")
def get_scores():
    return jsonify(scores)


@app.route("/api/reset")
def reset():
    for k in scores:
        scores[k] = 0
    conn = get_db()
    conn.execute("DELETE FROM history")
    conn.commit()
    return jsonify({"status": "reset"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
