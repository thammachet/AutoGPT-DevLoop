# tasks_config.py

"""
Example task definitions:
- 5 difficulty levels
- 3 tasks each
- Each task repeated 5 times

In a real scenario, you'd expand these tasks to reflect your actual software dev challenges.
"""

TASKS = {
    1: [
        "Create a simple Python script that prints 'Hello World' and install the requests library.",
        "Create a Python script that reads from a text file and prints its content.",
        "Create a Python script that sums a list of integers."
    ],
    2: [
        "Create two Python files that import each other and demonstrate a simple function call.",
        "Install 'numpy' and write a script that performs a basic array operation.",
        "Create a script to parse a small JSON file and print the parsed data."
    ],
    3: [
        "Integrate a simple external API call (e.g., via requests) and print the response.",
        "Write a Python module that performs data cleaning on a CSV file.",
        "Create a multi-file mini-package and demonstrate importing across modules."
    ],
    4: [
        "Implement concurrency (using threads) to perform two tasks in parallel.",
        "Create a script that interacts with a local SQLite database to store and retrieve data.",
        "Implement a small class-based design with inheritance and demonstrate usage."
    ],
    5: [
        "Implement a more advanced feature (e.g., a small ML model training with scikit-learn).",
        "Set up a mini-web server (Flask or FastAPI) and demonstrate one endpoint.",
        "Write a script that orchestrates multiple modules, each with distinct responsibilities."
    ]
}

NUM_TRIALS_PER_TASK = 5
