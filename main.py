import openai  # <-- same import, but the usage below changes
import os
import subprocess
import json
import Utils.Token as TokenUtils
import Utils.EnvironmentManagement as EnvUtils
import sys

#################################
# 1. HELPER: Load API Key
#################################

# Set your OpenAI API key from file
openai.api_key = EnvUtils.load_api_key()

#################################
# 2. GLOBALS & FUNCTION DEFINITIONS
#################################

notes = ""  # Global note variable

# Track which projects already have virtual envs
created_envs = set()

def write_note(note):
    """
    Overwrites any existing note used in the system prompt.
    """
    global notes
    notes = note
    return "Note written."

def create_virtual_env(env_name="venv"):
    """
    Creates a Python virtual environment with the given name.
    """
    try:
        # If the folder already exists, skip creation
        if os.path.isdir(env_name):
            return f"Virtual environment '{env_name}' already exists. Skipping creation."

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

def create_or_edit_file(project_name, file_path, content):
    """
    Creates a new file if it doesn't exist, or edits it if it already exists.
    Automatically creates a virtual environment for the project if one doesn't exist,
    then runs the file if it ends with .py.
    """
    global created_envs

    # Ensure a venv is created for this project
    if project_name not in created_envs:
        create_venv_result = create_virtual_env(project_name)
        print(create_venv_result)  # For logging
        created_envs.add(project_name)

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

        msg = f"File '{file_path}' {action} successfully in project '{project_name}'."
        print(msg)

        # If it's a python file, run it
        if file_path.endswith(".py"):
            run_result = run_python_file(project_name, full_path)
            msg += f"\n---\nAttempted to run '{file_path}' in '{project_name}':\n{run_result}"

        return msg
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

#################################
# 3. OPENAI FUNCTION SCHEMA
#################################

functions = [
    {
        "name": "create_or_edit_file",
        "description": "Create or edit a file within the project folder. Automatically ensures a virtual environment exists and runs the file if it ends in '.py'.",
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
        "description": "Create a Python virtual environment in the current directory. If it already exists, do nothing.",
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
# 5. SYSTEM PROMPT
#################################

def get_system_prompt():
    """
    Updated system prompt to ensure the AI first creates a virtual environment
    for every project, then creates/edits files, and runs the Python file after success.
    """
    return {
        "role": "system",
        "content": (
            "Develop end-to-end software solutions autonomously using Python. "
            "Whenever you create or edit a file for a project, you must first ensure "
            "a virtual environment for that project is created. Then you create/edit "
            "the file, and if the file is a Python file, you automatically run it. "
            "Focus exclusively on creating/editing project files, creating virtual environments, "
            "installing Python packages, and running Python scripts. Avoid OS-level or "
            "admin-level operations. "
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
    max_retries = 3  # how many times we retry if there's an error

    # A dictionary to map function calls to actual Python functions
    function_map = {
        "create_or_edit_file": create_or_edit_file,
        "write_note": write_note,
        "read_file": read_file,
        "create_virtual_env": create_virtual_env,
        "install_package": install_package,
        "run_python_file": run_python_file
    }

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break

        # Append user message
        messages.append({"role": "user", "content": user_input})
        # Prune if needed
        messages = TokenUtils.prune_messages(messages, max_token_limit, model=model)

        # Insert system prompt before the user's message (just before the last index)
        system_prompt_index = len(messages) - 1
        messages.insert(system_prompt_index, get_system_prompt())

        # We'll allow multiple retries if we keep hitting errors
        for attempt in range(max_retries):
            # 1. Call the model
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                functions=functions,
                function_call="auto"
            )

            # 2. Remove the inserted system prompt (so we don’t keep duplicating it)
            messages.pop(system_prompt_index)

            # 3. Extract the assistant message
            assistant_msg = response.choices[0].message
            assistant_dict = assistant_msg.model_dump()
            # Save it to the conversation
            messages.append(assistant_dict)

            # 4. Prune if needed
            messages = TokenUtils.prune_messages(messages, max_token_limit, model=model)

            # 5. Check if there's a function call
            if assistant_msg.function_call:
                func_name = assistant_msg.function_call.name
                # function_call.arguments is a JSON string, so parse it
                func_args = json.loads(assistant_msg.function_call.arguments)

                if func_name in function_map:
                    try:
                        result = function_map[func_name](**func_args)
                    except TypeError as e:
                        result = f"Error: missing or invalid arguments. {str(e)}"
                    except Exception as e:
                        result = f"Error during function execution: {str(e)}"
                else:
                    result = f"Error: Function '{func_name}' not implemented."

                # 6. If the result is an error, feed it back as an assistant message so the model can fix it
                if result.lower().startswith("error"):
                    error_message = {
                        "role": "assistant",
                        "content": f"I encountered an error:\n{result}\nWhat should I do next?"
                    }
                    messages.append(error_message)
                    # Insert system prompt again before we call next time
                    system_prompt_index = len(messages) - 1
                    messages.insert(system_prompt_index, get_system_prompt())
                    # Let the loop continue, model tries to fix the error
                else:
                    # No error; just print the result and break out of retry loop
                    print(f"Assistant (function result): {result}")
                    break
            else:
                # 7. Otherwise, the model responded with plain text
                print(f"Assistant: {assistant_msg.content}")
                break  # No function call to handle, so break

        else:
            # If we exit the for-loop via exhaustion (no break),
            # we might want to say we ran out of retries.
            print("Reached max retries without resolving errors. Stopping here.")

if __name__ == "__main__":
    main()
