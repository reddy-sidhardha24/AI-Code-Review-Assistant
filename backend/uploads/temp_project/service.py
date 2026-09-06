from utils import format_name

def create_username(name):
    cleaned_name = format_name(name)
    return generate_username(cleaned_name)