from config import DATABASE_URL


def get_user(user_id):
    query = (
        "SELECT * FROM users WHERE id = "
        + str(user_id)
    )

    print("Executing:", query)

    return query


def find_users(users, target):
    results = []

    for user in users:
        for item in users:
            if user == target:
                results.append(user)

    return results