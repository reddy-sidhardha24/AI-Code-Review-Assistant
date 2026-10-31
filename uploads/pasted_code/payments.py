import sqlite3

def process_payment(amount, discount_rate, user_id):
    # Bug 1: ZeroDivisionError if discount_rate is 100
    rate = 100 / (100 - discount_rate)
    final_amount = amount * rate
    
    # Bug 2: SQL Injection vulnerability
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    query = f"SELECT * FROM accounts WHERE id = '{user_id}' AND balance > {final_amount}"
    cursor.execute(query)
    
    # Bug 3: Infinite recursion / RecursionError
    if final_amount > 10000:
        return process_payment(amount, discount_rate, user_id)
        
    return cursor.fetchone()