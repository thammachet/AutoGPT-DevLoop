import os
import subprocess

from Utils import Logger as ExperimentLogger
from knowledge_base import update_knowledge_base

# ------------------------------
# 1) Define the function schemas
# ------------------------------
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
                    "description": "A nested dictionary representing the project structure"
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

# ----------------------------------
# 2) Implementation of each function
# ----------------------------------

def create_project_folder(project_name):
    """
    Create a new project folder if it does not exist.
    """
    try:
        if not os.path.isdir(project_name):
            os.makedirs(project_name)
            msg = f"Project folder '{project_name}' created successfully."
        else:
            msg = f"Project folder '{project_name}' already exists."
        # Log
        ExperimentLogger.log_event("FUNCTION_CALL", msg, success=True)
        return msg
    except Exception as e:
        err = f"Error creating project folder '{project_name}': {e}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def create_virtual_environment(env_name, project_name):
    """
    Create a Python venv inside the project folder if not already present.
    """
    try:
        env_path = os.path.join(project_name, env_name)
        if not os.path.isdir(env_path):
            result = subprocess.run(['python', '-m', 'venv', env_path], capture_output=True, text=True)
            if result.returncode == 0:
                msg = f"Virtual environment '{env_name}' created in '{project_name}'."
            else:
                msg = f"Error creating venv '{env_name}': {result.stderr}"
        else:
            msg = f"Virtual environment '{env_name}' already exists in '{project_name}'."
        ExperimentLogger.log_event("FUNCTION_CALL", msg, success="Error" not in msg)
        return msg
    except Exception as e:
        err = f"Error: {str(e)}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def install_library(library_name, env_name, project_name):
    """
    Installs a library in the specified environment using pip.
    """
    try:
        env_path = os.path.join(project_name, env_name)
        pip_executable = (
            os.path.join(env_path, 'Scripts', 'pip.exe')
            if os.name == 'nt'
            else os.path.join(env_path, 'bin', 'pip')
        )
        command = [pip_executable, 'install', library_name]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            msg = f"Library '{library_name}' installed successfully in '{env_name}'."
        else:
            msg = f"Error installing '{library_name}': {result.stderr}"
        ExperimentLogger.log_event("FUNCTION_CALL", msg, success="Error" not in msg)
        return msg
    except Exception as e:
        err = f"Error: {str(e)}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def create_python_file(project_name, file_path, content):
    """
    Create a new Python file within the project, optionally in subdirs.
    """
    try:
        full_path = os.path.join(project_name, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        msg = f"File '{file_path}' created successfully in '{project_name}'."
        # Optionally update knowledge base
        update_knowledge_base(project_name)
        ExperimentLogger.log_event("FUNCTION_CALL", msg, success=True)
        return msg
    except Exception as e:
        err = f"Error creating file '{file_path}': {e}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def edit_python_file(project_name, file_path, content):
    """
    Overwrite the content of an existing Python file.
    """
    try:
        full_path = os.path.join(project_name, file_path)
        if os.path.isfile(full_path):
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            msg = f"File '{file_path}' edited successfully."
            # Update knowledge base
            update_knowledge_base(project_name)
            ExperimentLogger.log_event("FUNCTION_CALL", msg, success=True)
        else:
            msg = f"File '{file_path}' not found in '{project_name}'."
        return msg
    except Exception as e:
        err = f"Error editing file '{file_path}': {e}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def execute_python_file(file_path, env_name, project_name):
    """
    Execute a Python file inside the specified environment.
    """
    try:
        env_path = os.path.join(project_name, env_name)
        full_file_path = os.path.join(project_name, file_path)
        # Figure out python path
        python_executable = (
            os.path.join(env_path, 'Scripts', 'python.exe')
            if os.name == 'nt'
            else os.path.join(env_path, 'bin', 'python')
        )
        # Run the script
        result = subprocess.run([python_executable, full_file_path], capture_output=True, text=True)
        if result.returncode == 0:
            msg = f"Execution output:\n{result.stdout}"
        else:
            msg = f"Execution failed (code {result.returncode}):\n{result.stderr}"
        ExperimentLogger.log_event("FUNCTION_CALL", msg, success=(result.returncode==0))
        return msg
    except Exception as e:
        err = f"Error executing '{file_path}': {e}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def read_file(project_name, file_path):
    """
    Return the content of a file in the project.
    """
    try:
        full_path = os.path.join(project_name, file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        msg = f"Content of '{file_path}':\n{content}"
        ExperimentLogger.log_event("FUNCTION_CALL", f"Read file {file_path}", success=True)
        return msg
    except Exception as e:
        err = f"Error reading '{file_path}': {e}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def list_files_and_folders(project_name, additional_path=""):
    """
    Lists the contents of a project folder (recursive).
    """
    try:
        path = os.path.join(project_name, additional_path)
        if not os.path.isdir(path):
            msg = f"'{path}' is not a valid directory."
            return msg
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                items.append(f"{item}/")
            else:
                items.append(item)
        msg = "Contents of '{}':\n{}".format(path, "\n".join(items))
        ExperimentLogger.log_event("FUNCTION_CALL", msg, success=True)
        return msg
    except Exception as e:
        err = f"Error listing dir '{project_name}': {str(e)}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def generate_project_structure(project_name, structure):
    """
    Recursively create files/folders from a dictionary blueprint.
    """
    def create_structure(base_path, struct_dict):
        for name, content in struct_dict.items():
            path = os.path.join(base_path, name)
            if isinstance(content, dict):
                os.makedirs(path, exist_ok=True)
                create_structure(path, content)
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
    try:
        create_structure(project_name, structure)
        update_knowledge_base(project_name)
        msg = f"Project '{project_name}' created with the specified structure."
        ExperimentLogger.log_event("FUNCTION_CALL", msg, success=True)
        return msg
    except Exception as e:
        err = f"Error generating project structure: {e}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

def summarize_project(project_name):
    """
    Summarize the project structure, skipping env or pycache folders.
    """
    try:
        summary = []
        for root, dirs, files in os.walk(project_name):
            # Exclude certain directories
            dirs[:] = [d for d in dirs if "env" not in d.lower() and "pycache" not in d.lower()]
            level = root.replace(project_name, '').count(os.sep)
            indent = ' ' * 4 * level
            summary.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                summary.append(f"{subindent}{f}")
        msg = "Project '{}' structure:\n{}".format(project_name, "\n".join(summary))
        ExperimentLogger.log_event("FUNCTION_CALL", msg, success=True)
        return msg
    except Exception as e:
        err = f"Error summarizing project '{project_name}': {e}"
        ExperimentLogger.log_event("ERROR", err, success=False)
        return err

# -----------------------------------------------------
# 3) Map the function schemas to actual Python functions
# -----------------------------------------------------
function_map = {
    "create_project_folder": create_project_folder,
    "create_virtual_environment": create_virtual_environment,
    "install_library": install_library,
    "create_python_file": create_python_file,
    "edit_python_file": edit_python_file,
    "execute_python_file": execute_python_file,
    "read_file": read_file,
    "list_files_and_folders": list_files_and_folders,
    "generate_project_structure": generate_project_structure,
    "summarize_project": summarize_project,
}
