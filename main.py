import openai
import os
import subprocess
import json
import sys

import Utils.Token as TokenUtils
import Utils.EnvironmentManagement as EnvUtils

from knowledge_base import update_knowledge_base, retrieve_relevant_code

#################################
# 1. HELPER: Load API Key
#################################

openai.api_key = EnvUtils.load_api_key()

#################################
# 2. GLOBALS & FUNCTION DEFINITIONS
#################################

notes = ""  # Global note variable
project_blueprint = (
    "High-level blueprint:\n"
    "- Summaries of major modules, classes, design patterns.\n"
    "This blueprint will be updated as the project evolves.\n"
)
created_envs = set()

def write_note(note):
    """
    Overwrites any existing note used in the system prompt.
    """
    global notes
    notes = note
    return "Note written."

def append_to_blueprint(update_text):
    """
    Append new info to the global project blueprint.
    """
    global project_blueprint
    project_blueprint += f"\nUPDATE: {update_text}\n"
    return "Project blueprint updated."

def create_virtual_env(env_name="venv"):
    if env_name == "env":
        return "Error: 'env' is reserved for the main application. Please use a different environment name."

    try:
        if os.path.isdir(env_name):
            return f"Virtual environment '{env_name}' already exists. Skipping creation."
        subprocess.check_call([sys.executable, "-m", "venv", env_name])
        return f"Virtual environment '{env_name}' created successfully."
    except Exception as e:
        return f"Error creating virtual environment: {str(e)}"

def install_package(env_name, package_name):
    if env_name == "env":
        return "Error: 'env' is reserved for the main application. Installation aborted."
    
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
    if env_name == "env":
        return "Error: 'env' is reserved for the main application. Cannot run a file in this env."
    
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
        print(create_venv_result)
        created_envs.add(project_name)

    full_path = os.path.join(project_name, file_path)
    try:
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

        # Update the knowledge base with the new/edited code
        update_knowledge_base(project_name)

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
    },
    {
        "name": "append_to_blueprint",
        "description": "Append new design/structural info to the project's blueprint summary.",
        "parameters": {
            "type": "object",
            "properties": {
                "update_text": {"type": "string", "description": "New info to add to the blueprint."}
            },
            "required": ["update_text"]
        }
    }
]

#################################
# 4. SYSTEM PROMPT
#################################

def get_system_prompt(relevant_code_snippets=None):
    """
    Updated system prompt to:
    - Summarize the current blueprint
    - Show relevant code snippets (retrieved by semantic search)
    - Emphasize the instructions about how to handle file creation/editing/running
    - Emphasize storing code in multiple well-organized files, chunked by function/class in the knowledge base
    """
    snippet_text = ""
    if relevant_code_snippets:
        snippet_text = "\n\nRelevant code snippets:\n\n" + "\n\n---\n\n".join(relevant_code_snippets)

    base_prompt = (
        f"Develop end-to-end software solutions autonomously using Python.\n"
        f"PROJECT BLUEPRINT:\n{project_blueprint}\n"
        f"NOTES:\n{notes}\n"
        f"{snippet_text}\n\n"
        "Whenever you create or edit a file for a project, you must first ensure a virtual environment for that project is created.\n"
        "Then create/edit the file, and if the file is a Python file, automatically run it.\n\n"
        "IMPORTANT: We want the code split into multiple well-organized files where appropriate, each file focusing on a specific class or function group.\n"
        "We also store code in the knowledge base using function/class-based chunking, so we can precisely locate and fix code.\n\n"
        "Focus exclusively on:\n"
        "1. Creating/editing project files.\n"
        "2. Creating virtual environments.\n"
        "3. Installing Python packages.\n"
        "4. Running Python scripts.\n\n"
        "Always read a file before editing it if you suspect it has content.\n"
        "If you have multi-step tasks, plan them out carefully and call multiple functions as needed.\n"
    )
    return {"role": "system", "content": base_prompt}

#################################
# 5. MAIN
#################################

def main():
    print("Welcome to the Autonomofus Software Develop AI!")
    print("Type your goal or instructions. Type 'exit', 'quit', or 'q' to quit.")

    messages = []
    max_token_limit = 20000
    model = "o3-mini"
    # model = "gpt-4.1"
    max_retries = 5

    function_map = {
        "create_or_edit_file": create_or_edit_file,
        "write_note": write_note,
        "read_file": read_file,
        "create_virtual_env": create_virtual_env,
        "install_package": install_package,
        "run_python_file": run_python_file,
        "append_to_blueprint": append_to_blueprint,
    }

    # (Optional) Initialize or update the knowledge base once at startup
    # e.g., update_knowledge_base("my_project")

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break

        # 1. Retrieve relevant code from the knowledge base
        relevant_snippets = retrieve_relevant_code(user_input, top_k=3)

        # 2. Insert system prompt (including relevant code snippets)
        system_prompt = get_system_prompt(relevant_code_snippets=relevant_snippets)
        messages.append(system_prompt)

        # 3. Append the user's message
        messages.append({"role": "user", "content": user_input})

        # Prune if needed
        messages = TokenUtils.prune_messages(messages, max_token_limit, model=model)

        # We'll allow multiple retries if we keep hitting errors
        for attempt in range(max_retries):
            try:
                # 1. Call the model
                response = openai.chat.completions.create(
                    model=model,
                    messages=messages,
                    functions=functions,
                    function_call="auto"
                )
            except Exception as e:
                print(f"Error calling model: {e}")
                break

            # 2. Extract the assistant message
            assistant_msg = response.choices[0].message
            assistant_dict = assistant_msg.model_dump()
            messages.append(assistant_dict)
            # 3. Prune if needed
            messages = TokenUtils.prune_messages(messages, max_token_limit, model=model)

            if assistant_msg.function_call:
                func_name = assistant_msg.function_call.name
                try:
                    func_args = json.loads(assistant_msg.function_call.arguments)
                except json.JSONDecodeError:
                    result = "Error: Could not parse function arguments."
                    print("Assistant (function result):", result)
                    break

                if func_name in function_map:
                    try:
                        result = function_map[func_name](**func_args)
                    except TypeError as e:
                        result = f"Error: missing or invalid arguments. {str(e)}"
                    except Exception as e:
                        result = f"Error during function execution: {str(e)}"
                else:
                    result = f"Error: Function '{func_name}' not implemented."
                print(result)

                if result.lower().startswith("error"):
                    error_message = {
                        "role": "assistant",
                        "content": f"I encountered an error:\n{result}\nWhat should I do next?"
                    }
                    messages.append(error_message)
                    # Remove the system prompt we inserted before repeating
                    messages = [m for m in messages if m != system_prompt]
                    # Insert updated system prompt again
                    system_prompt = get_system_prompt()
                    messages.append(system_prompt)
                else:
                    print("Assistant (function result):", result)
                    # After success, remove the system prompt so it doesn't accumulate
                    messages = [m for m in messages if m != system_prompt]
                    break

            else:
                # The model responded with plain text
                print(f"Assistant: {assistant_msg.content}")
                # Remove the system prompt after a normal text answer
                messages = [m for m in messages if m != system_prompt]
                break

        else:
            print("Reached max retries without resolving errors. Stopping here.")


if __name__ == "__main__":
    main()
