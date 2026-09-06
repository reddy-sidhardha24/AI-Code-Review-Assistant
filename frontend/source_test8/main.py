from service import delete_account

def main():
    user_id = 1
    result = delete_account(user_id)
    print(result)

if __name__ == "__main__":
    main()