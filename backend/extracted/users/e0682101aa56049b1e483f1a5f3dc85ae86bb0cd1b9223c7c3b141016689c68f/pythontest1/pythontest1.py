import sqlite3
import subprocess

def calculate_average(numbers):
    return sum(numbers) / len(numbers)

def find_user(username):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()

def run_command(command):
    return subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )

numbers = []
print(calculate_average(numbers))