import os


def read_file(filename):
    file = open(filename, "r")
    return file.read()


def execute_command(command):
    return os.system(command)


def process_data(data):
    x = []
    y = []

    for item in data:
        if item:
            x.append(item)

    for item in x:
        y.append(item * 2)

    return 