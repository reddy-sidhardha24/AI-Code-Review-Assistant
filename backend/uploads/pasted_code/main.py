import json


def get_user(user_id):
    users = {
        1: {
            "name": "Alice",
            "age": 25,
            "email": "alice@example.com",
            "city": "Hyderabad"
        },
        2: {
            "name": "Bob",
            "age": 30,
            "email": "bob@example.com",
            "city": "Bangalore"
        }
    }

    return users.get(user_id)


def calculate_average(numbers):
    if not numbers:
        return 0

    total = sum(numbers)
    return total / len(numbers)


def process_user(user_id):
    user = get_user(user_id)

    if user is None:
        return None

    average = calculate_average([10, 20, 30])

    result = {
        "name": user["name"],
        "age": user["age"],
        "email": user["email"],
        "city": user["city"],
        "average": average
    }

    return result


def save_result(result, filename):
    with open(filename, "w") as file:
        json.dump(result, file)


def load_result(filename):
    with open(filename, "r") as file:
        return json.load(file)


def generate_report(user_id):
    user = process_user(user_id)

    if user is None:
        print("User not found")
        return

    print("User:", user["name"])
    print("Age:", user["age"])
    print("Average:", user["average"])


def main():
    try:
        user_id = int(input("Enter user ID: "))
    except ValueError:
        print("Invalid user ID")
        return

    result = process_user(user_id)

    if result:
        save_result(result, "result.json")
        generate_report(user_id)
    else:
        print("Unable to process user")


if __name__ == "__main__":
    main()