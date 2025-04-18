import tiktoken
from collections.abc import Mapping

#################################
# 4. TOKEN COUNTING & PRUNING
#################################

def _msg_to_dict(msg):
    """
    Accept dicts **or** Pydantic objects like ChatCompletionMessage,
    returning a uniform {role, content, name, function_call} dict.
    """
    if isinstance(msg, Mapping):
        return msg
    # Pydantic BaseModel (ChatCompletionMessage) ─ get attrs safely
    return {
        "role":          getattr(msg, "role", ""),
        "content":       getattr(msg, "content", ""),
        "name":          getattr(msg, "name", ""),
        "function_call": getattr(msg, "function_call", None),
    }

def num_tokens_from_messages(messages):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = 0
    for raw in messages:
        m = _msg_to_dict(raw)
        tokens += 4                                   # per‑message overhead
        tokens += len(enc.encode(m["role"]))
        tokens += len(enc.encode(m.get("content", "") or ""))
        if m.get("name"):
            tokens += len(enc.encode(m["name"]))
        if m.get("function_call"):
            tokens += len(enc.encode(str(m["function_call"])))
    return tokens + 2                                 # <im_start>assistant

def prune_messages(messages, max_tokens):
    """
    Drop the oldest non‑system messages until the total token
    count is ≤ max_tokens. Keeps the first message (system/developer)
    and the most recent ones.
    """
    while num_tokens_from_messages(messages) > max_tokens:
        if len(messages) > 2:
            messages.pop(1)          # remove second element (oldest user/assistant)
        else:
            break
    return messages
