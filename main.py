import openai
import os
import subprocess
import json
import sys
import csv
import time
import datetime
import Utils.EnvironmentManagement as env_mgmt
import Utils.Token as TokenUtils
import knowledge_base as kb  # <-- We already have the import

# Set your OpenAI API key
openai.api_key = env_mgmt.load_api_key()

MAX_TOKEN_LIMIT = 10000  

# Define the function schemas for function calling
functions = [
    {
        "name": "create_project_folder",
        "description": "Create a new project folder",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The name of the project folder to create"
                }
            },
            "required": ["project_name"]
        }
    },
    {
        "name": "create_virtual_environment",
        "description": "Create or activate a virtual environment within the project folder",
        "parameters": {
            "type": "object",
            "properties": {
                "env_name": {
                    "type": "string",
                    "description": "The name of the virtual environment"
                },
                "project_name": {
                    "type": "string",
                    "description": "The project folder to create the environment in"
                }
            },
            "required": ["env_name", "project_name"]
        }
    },
    {
        "name": "install_library",
        "description": "Install a Python library using pip within the project environment",
        "parameters": {
            "type": "object",
            "properties": {
                "library_name": {
                    "type": "string",
                    "description": "The name of the library to install"
                },
                "env_name": {
                    "type": "string",
                    "description": "The name of the virtual environment"
                },
                "project_name": {
                    "type": "string",
                    "description": "The project folder containing the environment"
                }
            },
            "required": ["library_name", "env_name", "project_name"]
        }
    },
    {
        "name": "create_python_file",
        "description": "Create a new Python file within the project folder, with optional additional path",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The project folder to create the file in"
                },
                "file_path": {
                    "type": "string",
                    "description": "The path to the Python file to create, relative to the project folder"
                },
                "content": {
                    "type": "string",
                    "description": "The content to write into the Python file"
                }
            },
            "required": ["project_name", "file_path", "content"]
        }
    },
    {
        "name": "edit_python_file",
        "description": "Edit an existing Python file within the project folder, with optional additional path",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The project folder containing the file"
                },
                "file_path": {
                    "type": "string",
                    "description": "The path to the Python file to edit, relative to the project folder"
                },
                "content": {
                    "type": "string",
                    "description": "The new content to write into the Python file"
                }
            },
            "required": ["project_name", "file_path", "content"]
        }
    },
    {
        "name": "execute_python_file",
        "description": "Execute a Python file within the project folder and return the output",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the Python file to execute, relative to the project folder"
                },
                "env_name": {
                    "type": "string",
                    "description": "The name of the virtual environment to use for execution"
                },
                "project_name": {
                    "type": "string",
                    "description": "The project folder containing the file and environment"
                }
            },
            "required": ["file_path", "env_name", "project_name"]
        }
    },
    {
        "name": "read_file",
        "description": "Read the content of a file within the project folder, with optional additional path",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The project folder containing the file"
                },
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read, relative to the project folder"
                }
            },
            "required": ["project_name", "file_path"]
        }
    },
    {
        "name": "list_files_and_folders",
        "description": "List the files and folders within the specified project folder, with optional additional path, supporting nested directories",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The project folder to list the contents of"
                },
                "additional_path": {
                    "type": "string",
                    "description": "An additional path within the project folder to list contents of"
                }
            },
            "required": ["project_name"]
        }
    },
    {
        "name": "generate_project_structure",
        "description": "Generate a project folder with a specified structure.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The name of the project folder to create"
                },
                "structure": {
                    "type": "object",
                    "description": "A nested dictionary representing the project structure, where keys are folder or file names, and values are either another dictionary (for folders) or file content (for files)"
                }
            },
            "required": ["project_name", "structure"]
        }
    },
    {
        "name": "summarize_project",
        "description": "Summarize the project structure and provide an overview of the project files.",
        "parameters": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "The project folder to summarize"
                }
            },
            "required": ["project_name"]
        }
    },
]

# --- Existing function definitions (create_project_folder, create_virtual_environment, install_library, etc.) ---
def create_project_folder(project_name):
    try:
        if not os.path.isdir(project_name):
            os.makedirs(project_name)
            return f"Project folder '{project_name}' created successfully."
        else:
            return f"Project folder '{project_name}' already exists."
    except Exception as e:
        return str(e)

def create_virtual_environment(env_name, project_name):
    try:
        env_path = os.path.join(project_name, env_name)
        if not os.path.isdir(env_path):
            result = subprocess.run(['python', '-m', 'venv', env_path], capture_output=True, text=True)
            if result.returncode == 0:
                return f"Virtual environment '{env_name}' created successfully in project '{project_name}'."
            else:
                return f"Error creating virtual environment '{env_name}': {result.stderr}"
        else:
            return f"Virtual environment '{env_name}' already exists in project '{project_name}' and is ready to use."
    except Exception as e:
        return str(e)

def install_library(library_name, env_name, project_name):
    print(f"Installing {library_name} in {env_name} of {project_name}")
    try:
        env_path = os.path.join(project_name, env_name)
        if os.name == 'nt':  # Windows
            pip_executable = os.path.join(env_path, 'Scripts', 'pip.exe')
        else:
            pip_executable = os.path.join(env_path, 'bin', 'pip')
        command = [pip_executable, 'install', library_name]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            return f"Library '{library_name}' installed successfully in environment '{env_name}'."
        else:
            return f"Error installing library '{library_name}': {result.stderr}"
    except Exception as e:
        return str(e)

def create_python_file(project_name, file_path, content):
    try:
        full_path = os.path.join(project_name, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write(content)
        return f"File '{file_path}' created successfully in project '{project_name}'. Should we run it now? (call the execute function, if yes)"
    except Exception as e:
        return str(e)

def edit_python_file(project_name, file_path, content):
    try:
        full_path = os.path.join(project_name, file_path)
        if os.path.isfile(full_path):
            with open(full_path, 'w') as f:
                f.write(content)
            return f"File '{file_path}' edited successfully in project '{project_name}'."
        else:
            return f"File '{file_path}' does not exist in project '{project_name}'."
    except Exception as e:
        return str(e)
    
def execute_python_file(file_path, env_name, project_name):
    print(f"Executing {file_path} in {env_name} of {project_name}")
    try:
        env_path = os.path.join(project_name, env_name)
        full_file_path = os.path.join(project_name, file_path)
        
        if env_name:
            if os.name == 'nt':  # Windows
                python_executable = os.path.join(env_path, 'Scripts', 'python.exe')
            else:
                python_executable = os.path.join(env_path, 'bin', 'python')
        else:
            python_executable = 'python'

        result = subprocess.run(
            [python_executable, full_file_path],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return f"Execution successful.\n**Output**:\n{result.stdout}"
        else:
            return (
                f"Execution failed with exit code {result.returncode}.\n"
                f"**Stdout**:\n{result.stdout}\n"
                f"**Stderr**:\n{result.stderr}"
            )
    except Exception as e:
        return str(e)

def read_file(project_name, file_path):
    try:
        full_path = os.path.join(project_name, file_path)
        with open(full_path, 'r') as f:
            content = f.read()
        return f"Content of '{file_path}':\n{content}"
    except Exception as e:
        return str(e)

def list_files_and_folders(project_name, additional_path=""):
    try:
        path = os.path.join(project_name, additional_path)
        if os.path.isdir(path):
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"{item}/")
                else:
                    items.append(item)
            return f"Contents of '{path}':\n" + '\n'.join(items)
        else:
            return f"'{path}' is not a valid directory."
    except Exception as e:
        return str(e)

##############################################################################
#                         MAIN APPLICATION WITH LOGGER                       #
##############################################################################

def main():
    """
    Main function that starts an interactive loop:
    1. Asks for difficulty, task, trial numbers to form a log file.
    2. Iteratively accepts user input, calls OpenAI with function usage.
    3. Logs each step to a CSV file (calls, messages, etc.).
    """
    # Ask user for experiment identifiers
    difficulty = input("Enter difficulty level (e.g., 1,2,3,4,5): ").strip()
    task = input("Enter task number (e.g., 1,2,3): ").strip()
    trial = input("Enter trial number (e.g., 1,2,3,4,5): ").strip()

    # Create CSV filename
    log_filename = f"log_d{difficulty}_t{task}_tr{trial}.csv"

    # Open CSV in append mode (or create if not exists)
    # We'll write a header if file doesn't exist yet
    file_exists = os.path.isfile(log_filename)
    log_file = open(log_filename, mode='a', newline='', encoding='utf-8')
    csv_writer = csv.writer(log_file)

    if not file_exists:
        csv_writer.writerow([
            "timestamp",
            "event_type",
            "user_input",
            "function_name",
            "function_args",
            "assistant_response",
            "success",
            "error",
            "time_elapsed_seconds"
        ])

    # Helper function to log a row in the CSV
    def log_event(event_type, user_input="", function_name="", function_args="",
                  assistant_response="", success="", error="", time_elapsed=0.0):
        """
        Write a single row to the CSV log.
        """
        timestamp = datetime.datetime.now().isoformat()
        csv_writer.writerow([
            timestamp,
            event_type,
            user_input,
            function_name,
            function_args,
            assistant_response,
            success,
            error,
            f"{time_elapsed:.3f}"
        ])
        log_file.flush()  # ensure immediate write

    system_prompt = {
        "role": "system",
        "content": (
            "You are an AI assistant that can perform tasks in the command prompt using Python functions.\n"
            "Follow these steps for each user request:\n"
            "1. If the user wants to create a Python file, create it using 'create_python_file', then *always* call "
            "'execute_python_file' to run it (unless there's a clear reason not to).\n"
            "2. If the user wants to edit a Python file, use 'edit_python_file', then call 'execute_python_file'.\n"
            "3. All virtual environments and files must be created within the project folder.\n"
            "If an error occurs, fix it by editing or re-running as needed.\n"
            "Do not mention the function names in the user-facing message.\n"
            "For bigger projects, plan out the steps, create or edit multiple files, and run them when appropriate.\n"
            "Always respond succinctly.\n"
        )
    }

    print("Welcome to the ChatGPT Command Prompt Controller!")
    print("Type your high-level goals below. Type 'exit', 'quit', or 'q' to quit.")

    messages = []

    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break

        # Mark the start time for measuring speed
        start_time = time.time()

        # Append user message
        messages.append({"role": "user", "content": user_input})

        # Log the user input
        log_event(
            event_type="user_input",
            user_input=user_input,
            time_elapsed=0.0
        )

        # ---------------------------------------------------------------------
        # 1. Retrieve relevant code from knowledge base before each completion
        # ---------------------------------------------------------------------
        relevant_snippets = kb.retrieve_relevant_code(query=user_input, top_k=3)
        if relevant_snippets:
            snippet_text = "\n\n".join(relevant_snippets)
            knowledge_system_msg = {
                "role": "system",
                "content": (
                    "Relevant code snippets from knowledge base:\n\n"
                    f"{snippet_text}"
                )
            }
            # Insert this message so the model can use it
            messages.insert(len(messages) - 1, knowledge_system_msg)

        max_iterations = 30
        iteration = 0

        # We will continue until the model produces a non-function call response or we exhaust iterations
        while iteration < max_iterations:
            iteration += 1

            # Make sure we're not exceeding token limit
            messages = TokenUtils.prune_messages(messages, MAX_TOKEN_LIMIT)

            # Insert system prompt just before the last user or system context
            system_prompt_index = len(messages) - 1
            messages.insert(system_prompt_index, system_prompt)

            response = openai.chat.completions.create(
                model="o4-mini",
                messages=messages,
                functions=functions,
                function_call="auto",
                reasoning_effort="high",
            )
            assistant_message = response.choices[0].message

            # Remove the system prompt from messages
            messages.pop(system_prompt_index)

            messages.append(assistant_message)

            if assistant_message.function_call:
                function_name = assistant_message.function_call.name
                function_args_json = assistant_message.function_call.arguments
                function_args_str = json.dumps(function_args_json)
                function_args = json.loads(function_args_json)

                function_map = {
                    "create_project_folder": create_project_folder,
                    "create_virtual_environment": create_virtual_environment,
                    "install_library": install_library,
                    "create_python_file": create_python_file,
                    "edit_python_file": edit_python_file,
                    "execute_python_file": execute_python_file,
                    "read_file": read_file,
                    "list_files_and_folders": list_files_and_folders,
                }

                function_to_call = function_map.get(function_name)

                if function_to_call:
                    # Attempt to run the function
                    try:
                        output = function_to_call(**function_args)
                        print(f"[System] Called function: {function_name}")
                        print(f"[System] Output:\n{output}")
                    except Exception as e:
                        output = f"An error occurred: {str(e)}"
                else:
                    output = f"Function '{function_name}' is not implemented."

                # Decide success or failure heuristically
                success_flag = "False"
                error_msg = ""
                # Basic heuristic: if 'Error' or 'failed' in output, it's a failure
                # Otherwise, success.
                lower_output = output.lower()
                if "error" in lower_output or "failed" in lower_output or "traceback" in lower_output:
                    success_flag = "False"
                    error_msg = output
                else:
                    success_flag = "True"

                # Log function call
                elapsed_time = time.time() - start_time
                log_event(
                    event_type="function_call",
                    user_input=user_input,
                    function_name=function_name,
                    function_args=function_args_str,
                    assistant_response=output,
                    success=success_flag,
                    error=error_msg,
                    time_elapsed=elapsed_time
                )

                # If we changed or created files, update knowledge base
                if function_name in [
                    "create_python_file",
                    "edit_python_file",
                    "generate_project_structure",
                ]:
                    project_name = function_args.get("project_name", "")
                    if project_name:
                        print("Updating knowledge base with new or changed files...")
                        kb.update_knowledge_base(project_name)

                # Add assistant's function response to the conversation
                messages.append({
                    "role": "assistant",
                    "content": output
                })

            else:
                # This is a final textual message from the assistant
                assistant_text = assistant_message.content
                print(f"Assistant: {assistant_text}")

                # Log the assistant's final textual response
                elapsed_time = time.time() - start_time
                # Determine success if no keywords "error" or "failed"
                success_flag = "False"
                error_msg = ""
                if assistant_text and not any(k in assistant_text.lower() for k in ["error", "failed", "traceback"]):
                    success_flag = "True"

                log_event(
                    event_type="assistant_message",
                    user_input=user_input,
                    assistant_response=assistant_text,
                    success=success_flag,
                    error=error_msg,
                    time_elapsed=elapsed_time
                )
                break  # we've reached a final textual answer for this user input

    # Close the log file when the session ends
    log_file.close()

if __name__ == "__main__":
    main()
