# Utils/Logger.py

import csv
import os
import time
from datetime import datetime

# Global variables to track the current experimental context:
EXPERIMENT_CONTEXT = {
    "difficulty_level": None,
    "task_number": None,
    "trial_number": None
}

# In-memory list of log events
LOG_EVENTS = []

def set_experiment_context(difficulty_level, task_number, trial_number):
    """
    Set the experiment context as per the methodology:
    - difficulty_level: 1..5
    - task_number: 1..3
    - trial_number: 1..5
    """
    EXPERIMENT_CONTEXT["difficulty_level"] = difficulty_level
    EXPERIMENT_CONTEXT["task_number"] = task_number
    EXPERIMENT_CONTEXT["trial_number"] = trial_number

def log_event(event_type, event_details, success=None, start_time=None):
    """
    Log a single event with the following fields:
    - timestamp
    - difficulty_level
    - task_number
    - trial_number
    - event_type
    - event_details
    - success (True/False/None)
    - time_to_completion (if start_time is provided)

    event_type can be:
        'USER_INPUT', 'SYSTEM_PROMPT', 'AI_RESPONSE', 'FUNCTION_CALL',
        'ERROR', 'COMPLETION', etc.
    """
    difficulty_level = EXPERIMENT_CONTEXT.get("difficulty_level")
    task_number = EXPERIMENT_CONTEXT.get("task_number")
    trial_number = EXPERIMENT_CONTEXT.get("trial_number")
    
    time_stamp = datetime.now().isoformat(timespec='seconds')

    # Calculate time_to_completion if start_time is given
    time_to_completion = None
    if start_time is not None:
        time_to_completion = round(time.time() - start_time, 3)

    log_entry = {
        "timestamp": time_stamp,
        "difficulty_level": difficulty_level,
        "task_number": task_number,
        "trial_number": trial_number,
        "event_type": event_type,
        "event_details": event_details,
        "success": success,
        "time_to_completion": time_to_completion
    }
    LOG_EVENTS.append(log_entry)

def write_logs_to_csv(log_filename=None):
    """
    Write all recorded events to a CSV file. The filename can follow
    the naming convention in the thesis, e.g., L2_T1_Trial4.csv
    """
    if not log_filename:
        # Construct a filename if none provided
        dl = EXPERIMENT_CONTEXT.get("difficulty_level")
        tn = EXPERIMENT_CONTEXT.get("task_number")
        tr = EXPERIMENT_CONTEXT.get("trial_number")
        log_filename = f"L{dl}_T{tn}_Trial{tr}.csv"

    # Ensure directory exists
    os.makedirs("logs", exist_ok=True)
    full_path = os.path.join("logs", log_filename)

    fieldnames = [
        "timestamp",
        "difficulty_level",
        "task_number",
        "trial_number",
        "event_type",
        "event_details",
        "success",
        "time_to_completion"
    ]
    
    # Write or append
    write_header = not os.path.isfile(full_path)
    with open(full_path, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(LOG_EVENTS)

    # Clear in-memory logs after writing
    LOG_EVENTS.clear()
