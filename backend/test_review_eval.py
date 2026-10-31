import requests

sample_code = """def process_payment(amount, tax_rate):
    # Potential ZeroDivisionError / logic flaw
    total = amount / (tax_rate - 10)
    return total

def lookup_user_account(cursor, user_input):
    # Critical security flaw: raw SQL Injection vulnerability
    sql = f"SELECT * FROM accounts WHERE username = '{user_input}'"
    return cursor.execute(sql).fetchall()

def infinite_recursion(n):
    # Unhandled recursion / crash
    return infinite_recursion(n)
"""

# 1. Index sample code via /paste-code
res_paste = requests.post(
    "http://localhost:8000/paste-code",
    json={"filename": "payments.py", "code": sample_code}
)
print("Paste code response:", res_paste.status_code)

# 2. Test Single Agent review
print("\n--- Testing Single-Agent Review ---")
res_single = requests.post(
    "http://localhost:8000/review",
    json={"question": "Perform a complete audit covering bugs and security vulnerabilities.", "category": "full_review"},
    headers={"X-User-Id": "test_user_eval"}
)
print("Single-Agent status:", res_single.status_code)
if res_single.status_code == 200:
    data = res_single.json()
    rev = data.get("review", {})
    print("Single-Agent Score:", rev.get("score"))
    print("Single-Agent Bugs Count:", len(rev.get("bugs", [])))
    print("Single-Agent Security Count:", rev.get("security", {}).get("issues_found"))
    print("Single-Agent Final Verdict:", rev.get("final_verdict")[:100] + "...")
else:
    print("Single-Agent Error:", res_single.text)

# 3. Test Multi-Agent review
print("\n--- Testing Multi-Agent Review ---")
# Set mode to multi in preferences
requests.put(
    "http://localhost:8000/api/config/preferences",
    json={"agent_mode": "multi"},
    headers={"X-User-Id": "test_user_eval"}
)

res_multi = requests.post(
    "http://localhost:8000/review",
    json={"question": "Perform a complete audit covering bugs and security vulnerabilities.", "category": "full_review"},
    headers={"X-User-Id": "test_user_eval"}
)
print("Multi-Agent status:", res_multi.status_code)
if res_multi.status_code == 200:
    data = res_multi.json()
    rev = data.get("review", {})
    print("Multi-Agent Score:", rev.get("score"))
    print("Multi-Agent Bugs Count:", len(rev.get("bugs", [])))
    print("Multi-Agent Security Count:", rev.get("security", {}).get("issues_found"))
    print("Multi-Agent Final Verdict:", rev.get("final_verdict")[:100] + "...")
else:
    print("Multi-Agent Error:", res_multi.text)
