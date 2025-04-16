def load_api_key():
    """
    Loads the OpenAI API key from a file named 'api_key.txt' by default.
    If the file is not found, exits with an error message.
    """
    try:
        with open("api_key.txt", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        print("Error: 'api_key.txt' not found. Create this file and add your API key.")
