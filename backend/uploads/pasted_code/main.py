import subprocess

def get_user(user_id):
    users = {
        1: {"name": "Alice", "age": 21},
        2: {"name": "Bob", "age": 25}
    }
    return users[user_id]

def calculate_average(numbers):
    return sum(numbers) / len(numbers)

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

def run_command(command):
    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True
    )
    return result.stdout

def main():
    user_id = int(input("Enter user ID: "))

    user = process_user(user_id)

    command = input("Enter command: ")
    output = run_command(command)

    print(user)
    print(output)

if __name__ == "__main__":
    main()