import uuid


def generate_api_key():
    return f'key-{uuid.uuid4()}'
