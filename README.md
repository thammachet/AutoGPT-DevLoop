# AutoGPT Development Loop

This repository contains an experimental automation tool for driving small Python projects with OpenAI's function-calling API.  The entry point `main.py` exposes a simple command-line interface that can create project folders, manage virtual environments, install packages and execute Python files based on natural‑language instructions.

---

## 🚀 Features

- **Automated Project Management**
  - Create or edit Python files on demand.
  - Generate and activate virtual environments inside each project folder.
  - Install required libraries before running your code.
  - Execute scripts and capture the output automatically.

- **Conversational Interface**
  - Control everything in plain English; the assistant chooses which functions to call.

- **Knowledge Base Updates**
  - Whenever files are created or edited, summaries are stored in a Chroma-based knowledge base.

- **Security Best Practices**
  - The OpenAI API key is stored in `api_key.txt`, which is excluded from version control.

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

### Step 2: Set up a Virtual Environment

```bash
python -m venv env
```

Activate the environment:

- **Windows:**
```bash
.\env\Scripts\activate
```

- **macOS/Linux:**
```bash
source env/bin/activate
```

### Step 3: Install required dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Add Your OpenAI API Key

- Create a file named `api_key.txt` in the project's root directory.
- Paste your OpenAI API key into the file:
```
sk-your_openai_api_key_here
```

**Note:** This file is ignored by `.gitignore` to protect your sensitive information.

---

## 🎮 Usage

Start the automation script:

```bash
python main.py
```

After launching you will be asked for a difficulty level, task number and trial number.  These values are used to name the resulting log file.

Once the prompt appears you can interact in plain language, for example:

```text
You: Create a new Python file named hello.py that prints "Hello, World!" in a folder called MyProject.
```

The assistant will choose the appropriate functions to create files, run them and record the conversation in a CSV log.

---

## ⚠️ Important Notes

- Always keep your API keys private. Never commit them to version control.
- Ensure `api_key.txt` remains excluded from Git (already handled in `.gitignore`).

---

## 🛠️ Project Structure

```
project-root/
│
├── env/                # Virtual environment (ignored)
├── api_key.txt         # OpenAI API key (ignored)
├── main.py             # CLI entry point
├── project_functions.py
├── task_config.py
├── Utils/              # Helper modules
├── Results/            # Experiment logs
├── .gitignore          # Git ignore configuration
└── README.md           # This file
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
