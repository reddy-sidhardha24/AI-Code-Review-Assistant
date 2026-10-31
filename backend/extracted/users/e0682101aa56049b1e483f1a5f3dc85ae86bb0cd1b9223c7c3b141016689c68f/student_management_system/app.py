from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DATABASE = "students.db"

def get_connection():
    return sqlite3.connect(DATABASE)

@app.route("/students", methods=["GET"])
def get_students():
    conn = get_connection()
    cursor = conn.cursor()
    search = request.args.get("name", "")
    query = "SELECT * FROM students WHERE name LIKE '%" + search + "%'"
    cursor.execute(query)
    students = cursor.fetchall()
    return jsonify(students)

@app.route("/students", methods=["POST"])
def add_student():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    age = data.get("age")

    conn = get_connection()
    cursor = conn.cursor()
    query = f"INSERT INTO students (name, email, age) VALUES ('{name}', '{email}', {age})"
    cursor.execute(query)
    conn.close()

    return jsonify({"message": "Student added successfully"})

@app.route("/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Student deleted"})

if __name__ == "__main__":
    app.run(debug=True)