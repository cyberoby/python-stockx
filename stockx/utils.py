

def camel_to_snake(string: str) -> str:
    upper = string.upper()
    return ''.join([f'_{c}' if c in upper else c for c in string]).lower()


def json_to_snake(json: dict) -> dict:
    return {camel_to_snake(k): v for k, v in json.items()}