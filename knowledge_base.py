import os
import openai
import chromadb
from chromadb.config import Settings
import tiktoken

# Initialize local Chroma DB
CHROMA_DB_DIR = ".chroma_db"
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
code_collection = client.get_or_create_collection(name="project_code")

TOKEN_LIMIT_PER_CHUNK = 800

def embed_texts(text_list):
    """
    Embed each text string in text_list, returning a list of embeddings.
    """
    # Switch to new v3 model
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text_list
    )
    embeddings = [item.embedding for item in response.data]
    return embeddings

def chunk_text(text, max_tokens=TOKEN_LIMIT_PER_CHUNK):
    """
    Splits `text` into multiple chunks of ~max_tokens tokens each.
    Returns a list of text chunks.
    """
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")  # or try "cl100k_base"
    tokens = enc.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        chunk = tokens[start:end]
        chunks.append(enc.decode(chunk))
        start = end
    return chunks

def update_knowledge_base(project_root):
    """
    Walk the project directory, read each .py file, chunk it, embed it,
    and upsert into the vector database.
    """
    for root, dirs, files in os.walk(project_root):
        # Skip environment or system folders
        if any(skip in root for skip in (".venv", "venv", "site-packages", ".git", "__pycache__")):
            continue
        
        for file_name in files:
            if file_name.endswith(".py"):
                full_path = os.path.join(root, file_name)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        file_text = f.read()
                        
                    # Skip if the file is basically empty
                    if not file_text.strip():
                        continue

                    chunks = chunk_text(file_text)
                    # Filter out empty chunks
                    chunks = [c for c in chunks if c.strip()]
                    if not chunks:
                        continue

                    embeddings = embed_texts(chunks)

                    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        doc_id = f"{full_path}::chunk_{idx}"
                        code_collection.upsert(
                            documents=[chunk],
                            embeddings=[embedding],
                            ids=[doc_id],
                            metadatas=[{"file_path": full_path}]
                        )

                except Exception as e:
                    print(f"Error reading/embedding {full_path}: {e}")

    client.persist()
    print("Knowledge base updated/persisted.")

def retrieve_relevant_code(query, top_k=3):
    """
    Given a user query, return the top_k relevant code chunks from the vector DB.
    """
    embedding = embed_texts([query])[0]
    results = code_collection.query(query_embeddings=[embedding], n_results=top_k)

    relevant_chunks = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        chunk_str = f"File: {meta['file_path']}\nChunk:\n{doc}"
        relevant_chunks.append(chunk_str)
    return relevant_chunks
