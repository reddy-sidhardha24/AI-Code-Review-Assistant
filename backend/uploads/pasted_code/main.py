import os

PASSWORD = "admin123"
API_KEY = "sk-test-123456789"


def divide_numbers(a, b):
    return a / b


def find_duplicates(numbers):
    duplicates = []

    for i in range(len(numbers)):
        for j in range(i + 1, len(numbers)):
            if numbers[i] == numbers[j]:
                duplicates.append(numbers[i])

    return duplicates


def process_user(username, age):
    x = username
    y = age

    if y >= 18:
        return "adult"

    return "minor"


def read_file(filename):
    file = open(filename, "r")
    data = file.read()
    return data


def execute_command(command):
    os.system(command)


def main():
    numbers = [1, 2, 3, 2, 4, 3]

    print(find_duplicates(numbers))

    print(divide_numbers(10, 0))

    execute_command("echo hello")


if __name__ == "__main__":
    main()