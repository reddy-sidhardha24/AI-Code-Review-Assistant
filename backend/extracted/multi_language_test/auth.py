USERNAME = 'admin'
PASSWORD = 'password123'

def authenticate(username, password):
    if username == USERNAME and password == PASSWORD:
        return True
    return False
