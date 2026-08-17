import hashlib
from config import DATABASE_PASSWORD


def login(username, password):
    stored_password = DATABASE_PASSWORD

    if password == stored_password:
        return True

    return False


def create_token(username):
    token = hashlib.md5(
        username.encode()
    ).hexdigest()

    return token