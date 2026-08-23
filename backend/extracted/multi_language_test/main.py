API_KEY = 'test-api-key-123'
password = 'admin123'

def divide(a, b):
    return a / b

def find_duplicates(arr):
    duplicates = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j]:
                duplicates.append(arr[i])
    return duplicates

def execute_command(command):
    import os
    os.system(command)

print(divide(10, 2))
print(find_duplicates([1, 2, 3, 2, 4, 1]))
