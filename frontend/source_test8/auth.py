def get_user_role(user_id):
    users = {
        1: {"name": "Alice", "role": "user"},
        2: {"name": "Admin", "role": "admin"}
    }
    return users.get(user_id)