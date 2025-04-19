import os
import hashlib
import openai
import chromadb
import tiktoken

from chromadb.config import Settings

"""
Utility functions for maintaining a Chroma-based knowledge base with
AI-generated summaries of Python files. Also stores a folder-structure
summary for high-level project context.

Changes vs. the minimal approach:
1. Incorporates an LLM-based summarization method (summarize_python_file_llm)
   that can handle large files by chunking them into smaller parts.
2. Uses tiktoken for more precise token counting, to avoid exceeding model limits.
3. Only the final summary for each file is stored in Chroma, not the raw code.
4. A separate top-level folder structure summary is also stored.

IMPORTANT:
 - This code references 'gpt-4o' and a hypothetical embedding model 
   'text-embedding-3-small'; change them to the actual models you have access to.
 - Ensure openai.api_key is set, e.g., openai.api_key = "sk-..."
"""

# --------------------------------------------
# Configuration
# --------------------------------------------
CHROMA_DB_DIR = ".chroma_db"

# By default, PersistentClient will auto-persist all writes
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)

# We'll store everything in a single collection:
code_collection = client.get_or_create_collection(name="project_code")


# --------------------------------------------
# Token/embedding utilities
# --------------------------------------------

def get_token_count(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Return the number of tokens in *text*, using tiktoken's approximate encoding logic.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback if the model is unknown to tiktoken
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def chunk_text(text: str, max_tokens: int = 2000, model: str = "gpt-3.5-turbo"):
    """
    Split *text* into multiple segments of up to *max_tokens* tokens each.
    Uses tiktoken to precisely count tokens.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)

    # Generate slices up to max_tokens in length
    chunks = []
    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk = tokens[start:end]
        chunks.append(encoding.decode(chunk))
        start = end
    return chunks


def embed_texts(text_list):
    """
    Return an embedding for each text string in *text_list*, using an OpenAI model.
    Change 'text-embedding-3-small' to the actual embedding model you have access to.
    """
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text_list,
    )
    return [item.embedding for item in response.data]


# --------------------------------------------
# Summarization logic
# --------------------------------------------
def summarize_folder_structure(project_root: str) -> str:
    """
    Walk *project_root* and create a textual summary of the folder structure,
    including only Python (*.py) files. Ignores typical unwanted directories
    like .venv, .git, __pycache__, etc.
    """
    lines = [f"Folder structure for '{project_root}':\n"]
    for root, dirs, files in os.walk(project_root):
        # Skip typical unwanted directories
        dirs[:] = [
            d for d in dirs
            if d not in ("site-packages", ".git", "__pycache__")
            and not d.startswith(".")
        ]
        level = root.replace(project_root, "").count(os.sep)
        indent = " " * 4 * level
        folder_name = os.path.basename(root)
        lines.append(f"{indent}{folder_name}/")
        sub_indent = " " * 4 * (level + 1)
        for filename in files:
            if filename.endswith(".py") or filename.endswith(".html") or filename.endswith(".css"):
                lines.append(f"{sub_indent}{filename}")

    return "\n".join(lines)

def summarize_python_file_llm(file_path: str, model: str = "gpt-4o", max_tokens: int = 2000) -> str:
    """
    Summarize a Python file by sending its content to an LLM (e.g. gpt-3.5-turbo or gpt-4).
    If the file is large, chunk it to avoid exceeding the model's context limit,
    then combine partial summaries into one final summary.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    # 1) Break the file into tokens that fit the model's context window
    chunks = chunk_text(source, max_tokens=max_tokens, model=model)

    partial_summaries = []
    for idx, chunk_text_part in enumerate(chunks):
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant specialized in analyzing Python code. "
                    "Please summarize the overall purpose and functionality of the "
                    "following code snippet in concise bullet points. Include any "
                    "notable classes, functions, or logic."
                )
            },
            {
                "role": "user",
                "content": chunk_text_part
            }
        ]
        response = openai.chat.completions.create(
            model=model,
            messages=prompt,
            temperature=0.0,  # keep it deterministic
        )
        partial_summary = response.choices[0].message.content.strip()
        partial_summaries.append(partial_summary)

    # 2) If there's only one chunk, that's our entire summary
    if len(partial_summaries) == 1:
        return partial_summaries[0]

    # 3) Otherwise, combine partial summaries into a final summary
    combo_prompt = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant. Combine the following partial summaries "
                "into a single concise summary of the file's overall functionality."
            )
        },
        {
            "role": "user",
            "content": "\n\n".join(partial_summaries)
        }
    ]
    final_response = openai.chat.completions.create(
        model=model,
        messages=combo_prompt,
        temperature=0.0
    )
    return final_response.choices[0].message.content.strip()


# --------------------------------------------
# File checksum utility
# --------------------------------------------

def file_checksum(file_path: str) -> str:
    """
    Return an SHA-256 hex digest for the given file.
    """
    hash_sha = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


# --------------------------------------------
# Knowledge-base update & query
# --------------------------------------------

def update_knowledge_base(project_root: str):
    """
    1) Upserts a single folder-structure summary for the entire project.
    2) For each *.py file, checks if it has changed (via SHA-256 hash).
       Only re-summarizes and upserts if the file is new or modified.
    """

    # 1) Upsert folder-structure summary
    folder_structure_text = summarize_folder_structure(project_root)
    folder_embedding = embed_texts([folder_structure_text])[0]
    folder_doc_id = f"{project_root}_folder_structure"

    code_collection.upsert(
        documents=[folder_structure_text],
        embeddings=[folder_embedding],
        ids=[folder_doc_id],
        metadatas=[{"type": "folder_summary", "root": project_root}],
    )

    # 2) Upsert each file's summary (only if changed)
    for root, dirs, files in os.walk(project_root):
        # Skip typical unwanted directories
        if any(skipped in root for skipped in (".venv", "venv", "site-packages", ".git", "__pycache__")):
            continue

        for file_name in files:
            if file_name.endswith(".py"):
                full_path = os.path.join(root, file_name)
                try:
                    # Get the current file checksum
                    current_checksum = file_checksum(full_path)

                    # Retrieve the doc (if any) by its ID = full_path
                    existing_docs = code_collection.get(ids=[full_path])
                    already_saved = (len(existing_docs["documents"]) == 1)

                    if already_saved:
                        saved_meta = existing_docs["metadatas"][0]
                        saved_checksum = saved_meta.get("checksum")

                        # Skip summarizing if checksums match
                        if saved_checksum == current_checksum:
                            print(f"No changes in {full_path}. Skipping re-summarization.")
                            continue

                    # If new or changed, re-summarize
                    print(f"Summarizing {full_path} ...")
                    summary_text = summarize_python_file_llm(full_path)
                    embedding = embed_texts([summary_text])[0]

                    # Store the new summary and checksum
                    code_collection.upsert(
                        documents=[summary_text],
                        embeddings=[embedding],
                        ids=[full_path],
                        metadatas=[
                            {
                                "file_path": full_path,
                                "type": "file_summary",
                                "checksum": current_checksum
                            }
                        ],
                    )

                except Exception as exc:
                    print(f"Error processing {full_path}: {exc}")

    print("Knowledge base update complete. Only changed/new files were re-summarized.")


def retrieve_relevant_code(query: str, top_k: int = 3):
    """
    Return the top_k most similar summaries for *query* from ChromaDB.
    Because each 'document' is a short summary, it provides a broad
    overview of the file's purpose. You might then open specific files
    to see details if needed.
    """
    # 1) Get embedding for the query
    query_embedding = embed_texts([query])[0]

    # 2) Query the code_collection for relevant docs
    results = code_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    if not results.get("documents"):
        return []

    # 3) Format the results
    summaries = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        path_text = meta.get('file_path', '(No file path)')
        doc_type = meta.get('type', 'unknown')
        summaries.append(
            f"Document Type: {doc_type}\n"
            f"Path or Root: {path_text}\n"
            f"Summary:\n{doc}\n"
        )
    return summaries
