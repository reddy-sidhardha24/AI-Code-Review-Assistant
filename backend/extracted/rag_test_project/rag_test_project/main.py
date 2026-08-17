from auth import login
from database import get_user, find_users
from utils import execute_command


def divide(a, b):
    return a / b


def start_application():
    username = "admin"
    password = "admin123"

    if login(username, password):

        user = get_user(0)

        numbers = [1, 2, 3, 4, 5]

        print(
            "Users:",
            find_users(
                numbers,
                3
            )
        )

        print(
            divide(10, 0)
        )

        execute_command(
            "echo application started"
        )


if __name__ == "__main__":
    start_application()