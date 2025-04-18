import os
import ast
import openai
import chromadb
import tiktoken
from chromadb.config import Settings

# Path for local Chroma database
CHROMA_DB_DIR = ".chroma_db"
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
code_collection = client.get_or_create_collection(name="project_code")

# Adjust if needed
TOKEN_LIMIT_PER_CHUNK = 800

def embed_texts(text_list):
    """
    Embed each text string in text_list, returning a list of embeddings.
    """
    # Use the model that your code supports
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text_list
    )
    embeddings = [item.embedding for item in response.data]
    return embeddings

def chunk_text_by_tokens(text, max_tokens=TOKEN_LIMIT_PER_CHUNK):
    """
    Splits `text` into multiple chunks of ~max_tokens tokens each.
    Returns a list of text chunks.
    """
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")  # or whichever model you use
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        start = end
    return chunks

def parse_python_file(file_path):
    """
    Parse a Python file into an AST, then extract top-level classes/functions.
    Returns a list of (symbol_name, code_string) pairs.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source, file_path)
    except SyntaxError:
        # If there's a syntax error, we can't parse, so return entire file as one chunk
        return [("entire_file", source)]

    chunks = []
    for node in tree.body:
        # For top-level functions/classes
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            name = node.name
            code_lines = source.split("\n")
            start_line = node.lineno - 1  # ast lines are 1-based
            end_line = node.end_lineno    # end_lineno is inclusive
            node_code = "\n".join(code_lines[start_line:end_line])
            chunks.append((name, node_code))

    # If no classes/functions at top level, treat entire file as a single chunk
    if not chunks:
        return [("entire_file", source)]
    else:
        return chunks

def update_knowledge_base(project_root):
    """
    Walk the project directory, read each .py file, parse them into top-level
    symbols (classes/functions), then upsert into the vector DB.
    """
    for root, dirs, files in os.walk(project_root):
        # Skip environment or system folders
        if any(skip in root for skip in (".venv", "venv", "site-packages", ".git", "__pycache__")):
            continue
        
        for file_name in files:
            if file_name.endswith(".py"):
                full_path = os.path.join(root, file_name)
                try:
                    parsed_chunks = parse_python_file(full_path)
                    
                    for idx, (symbol_name, code_snippet) in enumerate(parsed_chunks):
                        # If snippet is large, break it into smaller token-based chunks
                        small_chunks = chunk_text_by_tokens(code_snippet, max_tokens=TOKEN_LIMIT_PER_CHUNK)
                        
                        for sub_idx, scode in enumerate(small_chunks):
                            doc_id = f"{full_path}::{symbol_name}::{sub_idx}"
                            embedding = embed_texts([scode])[0]

                            code_collection.upsert(
                                documents=[scode],
                                embeddings=[embedding],
                                ids=[doc_id],
                                metadatas=[
                                    {
                                        "file_path": full_path,
                                        "symbol_name": symbol_name,
                                        "chunk_index": sub_idx
                                    }
                                ],
                            )
                except Exception as e:
                    print(f"Error reading/embedding {full_path}: {e}")

    client.persist()
    print("Knowledge base updated/persisted.")

def retrieve_relevant_code(query, top_k=3):
    """
    Given a user query, return the top_k relevant code chunks from the vector DB.
    """
    # Create an embedding for the query
    query_embedding = embed_texts([query])[0]

    # Search in the vector DB
    results = code_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    if not results.get("documents"):
        return []

    # Return the top code chunks
    relevant_chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        file_path = meta["file_path"]
        symbol_name = meta.get("symbol_name", "")
        chunk_index = meta.get("chunk_index", 0)
        
        chunk_str = (
            f"File: {file_path}\n"
            f"Symbol: {symbol_name}\n"
            f"Chunk index: {chunk_index}\n"
            f"Code:\n{doc}"
        )
        relevant_chunks.append(chunk_str)

    return relevant_chunks

