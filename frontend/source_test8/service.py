from auth import get_user_role

def delete_account(user_id):
    user = get_user_role(user_id)

    if user:
        return "Account deleted"

    return "User not found"