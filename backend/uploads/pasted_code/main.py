import os

password = "admin123"

def divide(a, b):
    return a / b

def process_data(data):
    result = []
    for item in data:
        for other in data:
            if item == other:
                result.append(item)
    return result

print(divide(10, 0))
