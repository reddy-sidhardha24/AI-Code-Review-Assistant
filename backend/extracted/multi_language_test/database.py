import sqlite3

def get_user(user_id):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()

    query = 'SELECT * FROM users WHERE id = ' + str(user_id)
    cursor.execute(query)

    result = cursor.fetchall()
    connection.close()

    return result
