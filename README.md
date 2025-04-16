
# Python OpenAI Automation Script

This Python script enables autonomous management of Python development tasks, such as creating and editing files, managing virtual environments, installing packages, and executing Python scripts through natural-language instructions processed by OpenAI's GPT models.

---

## 🚀 Features

- **Autonomous Python Development**
  - Create or edit Python files automatically.
  - Create virtual environments (`venv`) with ease.
  - Install Python packages effortlessly.
  - Execute Python scripts seamlessly.

- **Conversational Interface**
  - Control your project using plain English instructions.
  - Integrated with OpenAI's GPT API to interpret your commands intelligently.

- **Security Best Practices**
  - OpenAI API key stored securely in a separate `api_key.txt` file (excluded from Git).

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

### Step 2: Set up Virtual Environment and Dependencies

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
pip install openai tiktoken
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
python your_script.py
```

Enter your commands in plain language:

```text
You: Create a new Python file named hello.py that prints "Hello, World!" in the "MyProject" folder.
```

GPT interprets and carries out your instructions automatically.

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
├── your_script.py      # Main automation script
├── .gitignore          # Git ignore configuration
└── README.md           # This file
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
