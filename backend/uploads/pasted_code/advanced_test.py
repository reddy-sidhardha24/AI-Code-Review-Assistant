import os
import sqlite3


API_KEY = "prod-secret-12345"
ADMIN_PASSWORD = "admin@123"


def calculate_average(values):
    return sum(values) / len(values)


def search_users(username):
    connection = sqlite3.connect("users.db")

    query = "SELECT * FROM users WHERE username = '" + username + "'"

    cursor = connection.cursor()
    cursor.execute(query)

    return cursor.fetchall()


def run_backup(command):
    os.system(command)


def find_duplicates(items):
    duplicates = []

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])

    return duplicates


def read_config(filename):
    file = open(filename, "r")
    return file.read()


def process_users(users):
    result = []

    for user in users:
        if user["active"]:
            result.append(user["name"])

    return result


def divide_numbers(a, b):
    if b == 0:
        return 0

    return a / b


def main():
    print(calculate_average([]))

    print(
        search_users(
            input("Username: ")
        )
    )

    run_backup(
        input("Backup command: ")
    )

    print(
        find_duplicates(
            [1, 2, 2, 3, 3, 4]
        )
    )

    print(
        read_config(
            "missing_config.txt"
        )
    )

    users = [
        {"name": "Alice", "active": True},
        {"name": "Bob", "active": False}
    ]

    print(
        process_users(users)
    )

    print(
        divide_numbers(
            10,
            0
        )
    )


if __name__ == "__main__":
    main()