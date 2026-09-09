import sqlite3
import subprocess


def get_user(user_id):
    users = {
        1: {"name": "Alice", "age": 21}
    }
    return users.get(user_id)


def calculate_average(numbers):
    return sum(numbers) / len(numbers)


def find_user(username):
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    query = "SELECT * FROM users WHERE username = '" + username + "'"

    cursor.execute(query)
    return cursor.fetchall()


def run_command(command):
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout


def process_user(user_id):
    user = get_user(user_id)

    print("Name:", user["name"])
    print("Email:", user["email"])

    scores = []
    average = calculate_average(scores)

    return {
        "name": user["name"],
        "average": average
    }


def main():
    user_id = int(input("Enter user ID: "))

    user = process_user(user_id)

    username = input("Enter username: ")
    users = find_user(username)

    command = input("Enter command: ")
    output = run_command(command)

    print(user)
    print(users)
    print(output)


if __name__ == "__main__":
    main()