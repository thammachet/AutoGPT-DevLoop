import tiktoken  # For token counting
import time

#################################
# 4. TOKEN COUNTING & PRUNING
#################################

def num_tokens_from_messages(messages):
    """Returns the number of tokens used by a list of messages."""
    encoding = tiktoken.get_encoding("cl100k_base")
    num_tokens = 0
    for message in messages:
        # Base tokens per message
        num_tokens += 4
        num_tokens += len(encoding.encode(message.get("role", "")))
        if message.get("content"):
            num_tokens += len(encoding.encode(message["content"]))
        if message.get("name"):
            num_tokens += len(encoding.encode(message["name"]))
        if message.get("function_call"):
            num_tokens += len(encoding.encode(str(message["function_call"])))
    num_tokens += 2  # Every reply is primed with <im_start>assistant
    return num_tokens

def prune_messages(messages, max_tokens, model="gpt-4"):
    """
    Prune the messages to keep total tokens under max_tokens.
    This removes older user/assistant messages but keeps the system prompt and the most recent interactions.
    """
    while num_tokens_from_messages(messages) > max_tokens:
        # Check if there are messages to remove (excluding system prompt)
        if len(messages) > 2:
            messages.pop(1)  # Remove the second message (after system prompt)
        else:
            break
    return messages
