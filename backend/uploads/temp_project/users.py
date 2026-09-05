def get_user(user_id):
    users = {
        1: {
            "name": "Alice",
            "age": 25
        }
    }

    return users.get(user_id)