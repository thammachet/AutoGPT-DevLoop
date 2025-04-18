import openai
import os
import subprocess
import json
import sys
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
# No changes except we keep them as is. 
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
        return f"File '{file_path}' created successfully in project '{project_name}'. Should we run it now? (call the excute funtion, if yes)"
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

        # Use subprocess.run with capture_output to capture both stdout and stderr directly
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


def main():
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

        # Append user message
        messages.append({"role": "user", "content": user_input})

        # ---------------------------------------------------------------------
        # 1. Retrieve relevant code from knowledge base before each completion
        # ---------------------------------------------------------------------
        # This query uses the user's entire prompt. 
        relevant_snippets = kb.retrieve_relevant_code(query=user_input, top_k=3)
        if relevant_snippets:
            snippet_text = "\n\n".join(relevant_snippets)
            # Insert as a system message so the model can draw upon it
            print("Snippets from knowledge base:\n", snippet_text)
            knowledge_system_msg = {
                "role": "system",
                "content": (
                    "Relevant code snippets from knowledge base:\n\n"
                    f"{snippet_text}"
                )
            }
            # Insert this before the user message (just after last system prompt if any)
            # We'll place it at the second to last position, so it doesn't override the final user message.
            messages.insert(len(messages) - 1, knowledge_system_msg)

        max_iterations = 30
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

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
                function_args = json.loads(assistant_message.function_call.arguments)

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
                    try:
                        output = function_to_call(**function_args)
                        print(f"Function '{function_name}' executed successfully.")
                    except Exception as e:
                        output = f"An error occurred: {str(e)}"
                else:
                    output = f"Function '{function_name}' is not implemented."

                # ----------------------------------------------------
                # 2. Auto-update knowledge base if we changed code
                # ----------------------------------------------------
                # We'll update the knowledge base if the function modifies Python files 
                # or the project structure.
                if function_name in [
                    "create_python_file",
                    "edit_python_file",
                    "generate_project_structure",
                ]:
                    project_name = function_args.get("project_name", "")
                    if project_name:
                        print("Updating knowledge base with new or changed files...")
                        kb.update_knowledge_base(project_name)

                # Handle execution errors
                if 'Execution failed' in output or 'Error' in output:
                    messages.append({
                        "role": "assistant",
                        "content": f"I encountered an error:\n{output}"
                    })
                else:
                    messages.append({
                        "role": "assistant",
                        "content": output
                    })
            else:
                # No function call, just a message
                print(f"Assistant: {assistant_message.content}")
                break  # exit the iteration loop

if __name__ == "__main__":
    main()
