import os
import sqlite3

PASSWORD = "admin123"
API_KEY = "sk-demo-123456789"


def divide(a, b):
    return a / b


def find_duplicates(numbers):
    duplicates = []

    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] == numbers[j]:
                duplicates.append(numbers[i])

    return duplicates


def get_user(username):
    connection = sqlite3.connect("users.db")

    query = (
        "SELECT * FROM users WHERE username = '"
        + username
        + "'"
    )

    cursor = connection.cursor()
    cursor.execute(query)

    return cursor.fetchall()


def read_file(filename):
    file = open(filename, "r")
    return file.read()


def execute_command(command):
    os.system(command)


def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)


def main():
    print(divide(10, 0))

    print(
        find_duplicates(
            [1, 2, 2, 3, 3, 4]
        )
    )

    print(
        get_user(
            input("Username: ")
        )
    )

    print(
        read_file(
            "missing.txt"
        )
    )

    execute_command(
        input("Command: ")
    )

    print(
        calculate_average([])
    )


if __name__ == "__main__":
    main()