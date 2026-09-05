from users import get_user
from calculator import calculate_average


def process_user(user_id):
    user = get_user(user_id)

    if user is None:
        return None

    average = calculate_average([10, 20, 30])

    return {
        "name": user["name"],
        "age": user["age"],
        "email": user["email"],
        "average": average
    }


def main():
    user_id = 1

    result = process_user(user_id)

    if result:
        print(result)


if __name__ == "__main__":
    main()