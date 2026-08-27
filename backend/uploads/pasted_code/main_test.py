import sqlite3
import subprocess

USERNAME = "admin"
PASSWORD = "password123"

def authenticate(username, password):
    if username == USERNAME and password == PASSWORD:
        return True
    return False


def get_user(user_id):
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    query = "SELECT * FROM users WHERE id = " + str(user_id)
    cursor.execute(query)

    return cursor.fetchone()


def run_command(user_input):
    result = subprocess.check_output(
        "ping " + user_input,
        shell=True
    )
    return result


def find_duplicates(numbers):
    duplicates = []

    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] == numbers[j]:
                duplicates.append(numbers[i])

    return duplicates


def divide(a, b):
    return a / b


def main():
    print(get_user(1))
    print(run_command("google.com"))
    print(find_duplicates([1, 2, 2, 3, 3]))
    print(divide(10, 0))


if __name__ == "__main__":
    main()