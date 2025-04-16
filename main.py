import openai  # <-- same import, but the usage below changes
import os
import subprocess
import json
import tiktoken  # For token counting
import time
import sys

#################################
# 1. HELPER: Load API Key
#################################
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
        sys.exit(1)

# Set your OpenAI API key from file
openai.api_key = load_api_key()

#################################
# 2. FUNCTION DEFINITIONS
#################################

# Global note variable
notes = ""

def write_note(note):
    """
    Overwrites any existing note used in the system prompt.
    """
    global notes
    notes = note
    return "Note written."

def create_or_edit_file(project_name, file_path, content):
    """
    Creates a new file if it doesn't exist, or edits it if it already exists.
    """
    full_path = os.path.join(project_name, file_path)
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Check if the file already exists
        if os.path.isfile(full_path):
            action = "edited"
        else:
            action = "created"

        with open(full_path, 'w', encoding="utf-8") as f:
            f.write(content)

        return f"File '{file_path}' {action} successfully in project '{project_name}'."
    except Exception as e:
        return f"Error: {str(e)}"

def read_file(full_path):
    """
    Reads and returns the content of a file.
    """
    try:
        with open(full_path, 'r', encoding="utf-8") as f:
            content = f.read()
        return f"Content of '{full_path}':\n{content}"
    except Exception as e:
        return f"Error: {str(e)}"

def create_virtual_env(env_name="venv"):
    """
    Creates a Python virtual environment with the given name.
    """
    try:
        subprocess.check_call([sys.executable, "-m", "venv", env_name])
        return f"Virtual environment '{env_name}' created successfully."
    except Exception as e:
        return f"Error creating virtual environment: {str(e)}"

def install_package(env_name, package_name):
    """
    Installs a package in the specified virtual environment.
    """
    try:
        python_exec = (
            os.path.join(env_name, "Scripts", "python")
            if os.name == 'nt'
            else os.path.join(env_name, "bin", "python")
        )
        subprocess.check_call([python_exec, "-m", "pip", "install", package_name])
        return f"Package '{package_name}' installed successfully in '{env_name}'."
    except Exception as e:
        return f"Error installing package '{package_name}': {str(e)}"

def run_python_file(env_name, file_path):
    """
    Runs a Python file inside the specified virtual environment.
    """
    try:
        python_exec = (
            os.path.join(env_name, "Scripts", "python")
            if os.name == 'nt'
            else os.path.join(env_name, "bin", "python")
        )
        result = subprocess.run([python_exec, file_path], capture_output=True, text=True)
        if result.returncode == 0:
            return f"Output:\n{result.stdout}"
        else:
            return f"Error running file:\n{result.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"

#################################
# 3. OPENAI FUNCTION SCHEMA
#################################

functions = [
    {
        "name": "create_or_edit_file",
        "description": "Create or edit a file within the project folder.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Project folder name or path."},
                "file_path": {"type": "string", "description": "File path (relative to the project)."},
                "content": {"type": "string", "description": "Content to write into the file."}
            },
            "required": ["project_name", "file_path", "content"]
        }
    },
    {
        "name": "write_note",
        "description": "Write a note about the fundamentals of this project, always included in the system prompt. Overwrites any previous note.",
        "parameters": {
            "type": "object",
            "properties": {
                "note": {"type": "string", "description": "The note to be written."}
            },
            "required": ["note"]
        }
    },
    {
        "name": "read_file",
        "description": "Read and return the content of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "full_path": {"type": "string", "description": "Full path to the file to read."}
            },
            "required": ["full_path"]
        }
    },
    {
        "name": "create_virtual_env",
        "description": "Create a Python virtual environment in the current directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "env_name": {"type": "string", "description": "Name of the virtual environment folder."}
            },
            "required": []
        }
    },
    {
        "name": "install_package",
        "description": "Install a package in the specified Python virtual environment.",
        "parameters": {
            "type": "object",
            "properties": {
                "env_name": {"type": "string", "description": "Name of the virtual environment folder."},
                "package_name": {"type": "string", "description": "Package name to install (e.g., 'requests')."}
            },
            "required": ["env_name", "package_name"]
        }
    },
    {
        "name": "run_python_file",
        "description": "Run a Python file inside the specified virtual environment.",
        "parameters": {
            "type": "object",
            "properties": {
                "env_name": {"type": "string", "description": "Name of the virtual environment folder."},
                "file_path": {"type": "string", "description": "Path to the Python file to run."}
            },
            "required": ["env_name", "file_path"]
        }
    }
]

#################################
# 4. TOKEN COUNTING & PRUNING
#################################

def num_tokens_from_messages(messages):
    """Returns the number of tokens used by a list of messages."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0
    for message in messages:
        # Base tokens per message
        num_tokens += 4
        num_tokens += len(encoding.encode(message.get("role", "")))
        if message.get("content"):
            num_tokens += len(encoding.encode(message["content"]))
        if message.get("name"):
            num_tokens += len(encoding.encode(message["name"]))
        if message.get("function_call"):
            num_tokens += len(encoding.encode(str(message["function_call"])))
    num_tokens += 2  # Every reply is primed with <im_start>assistant
    return num_tokens

def prune_messages(messages, max_tokens, model="gpt-4"):
    """
    Prune the messages to keep total tokens under max_tokens.
    This removes older user/assistant messages but keeps the system prompt and the most recent interactions.
    """
    while num_tokens_from_messages(messages) > max_tokens:
        # Check if there are messages to remove (excluding system prompt)
        if len(messages) > 2:
            messages.pop(1)  # Remove the second message (after system prompt)
        else:
            break
    return messages

#################################
# 5. SYSTEM PROMPT
#################################

def get_system_prompt():
    return {
        "role": "system",
        "content": (
            "Develop end-to-end software solutions autonomously using Python. "
            "Focus exclusively on creating/editing project files, creating virtual environments, installing Python packages, "
            "and running Python scripts. Avoid OS-level or admin-level operations. "
            "Always read a file before editing it if you suspect it has content.\n"
            f"Note: {notes}"
        )
    }

#################################
# 6. MAIN
#################################

def main():
    print("Welcome to the Python-Only Manager!")
    print("Type your goal or instructions. Type 'exit', 'quit', or 'q' to quit.")

    messages = []
    max_token_limit = 5000  # Adjust as needed
    model = "o3-mini"

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break

        # Append user message
        messages.append({"role": "user", "content": user_input})
        # Prune if needed
        messages = prune_messages(messages, max_token_limit, model=model)

        # Insert system prompt before the user's message
        system_prompt_index = len(messages) - 1
        messages.insert(system_prompt_index, get_system_prompt())

        # ------------------------------------------------------------------
        # Below is the new call for openai>=1.0.0
        # ------------------------------------------------------------------
        response = openai.chat.completions.create(  # <-- changed for 1.0.0+
            model=model,
            messages=messages,
            functions=functions,
            function_call="auto"
        )

        # The response is a pydantic model, so you can access top-level fields directly:
        # e.g. response.choices, response.usage, etc.
        # Each choice has a "message" attribute.
        assistant_msg = response.choices[0].message  # This is also a pydantic model
        # assistant_msg.content -> raw content from the assistant
        # assistant_msg.function_call -> function call from the assistant (if any)

        # Remove the inserted system prompt from messages
        messages.pop(system_prompt_index)

        # Convert the assistant message to a dictionary if you prefer dictionary logic
        assistant_dict = assistant_msg.model_dump()  # <-- changed for 1.0.0+
        messages.append(assistant_dict)

        # Prune again if needed
        messages = prune_messages(messages, max_token_limit, model=model)

        # Check if there's a function call
        if assistant_msg.function_call:
            func_name = assistant_msg.function_call.name
            # function_call.arguments is a JSON string, so parse it
            func_args = json.loads(assistant_msg.function_call.arguments)

            # Map function call
            function_map = {
                "create_or_edit_file": create_or_edit_file,
                "write_note": write_note,
                "read_file": read_file,
                "create_virtual_env": create_virtual_env,
                "install_package": install_package,
                "run_python_file": run_python_file
            }

            if func_name in function_map:
                try:
                    result = function_map[func_name](**func_args)
                except TypeError as e:
                    result = f"Error: missing or invalid arguments. {str(e)}"
                except Exception as e:
                    result = f"Error during function execution: {str(e)}"
            else:
                result = f"Function '{func_name}' not implemented."

            # Pass the result back to the conversation
            messages.append({"role": "assistant", "content": result})
            print(f"Assistant (function result): {result}")
        else:
            # Otherwise, just print the assistant's response
            print(f"Assistant: {assistant_msg.content}")

if __name__ == "__main__":
    main()
