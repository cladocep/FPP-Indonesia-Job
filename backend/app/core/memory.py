"""
core/memory.py

Simple chat memory management.
Stores conversation history per session so agents can reference previous messages.

Usage:
    from backend.app.core.memory import ChatMemory

    memory = ChatMemory()
    memory.add_message("user", "Cari lowongan data scientist")
    memory.add_message("assistant", "Berikut lowongan yang ditemukan...")
    history = memory.get_history()
"""


class ChatMemory:
    """
    Simple in-memory chat history.

    Stores messages as list of dicts:
    [
        {"role": "user", "content": "..."},
        {"role": "assistant", "content": "..."},
    ]
    """

    def __init__(self, max_messages: int = 20):
        """
        Args:
            max_messages: maximum messages to keep (oldest get removed)
        """
        self.messages: list[dict] = []
        self.max_messages = max_messages

    def add_message(self, role: str, content: str):
        """
        Add a message to history.

        Args:
            role: "user" or "assistant"
            content: the message text
        """
        self.messages.append({
            "role": role,
            "content": content,
        })

        # Trim if exceeds max
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def get_history(self) -> list[dict]:
        """Return full chat history."""
        return self.messages.copy()

    def get_last_n(self, n: int = 5) -> list[dict]:
        """Return last N messages."""
        return self.messages[-n:]

    def clear(self):
        """Clear all history."""
        self.messages = []

    def get_context_string(self) -> str:
        """
        Format history as a readable string for LLM context.

        Returns:
            "User: ...\nAssistant: ...\nUser: ..."
        """
        parts = []
        for msg in self.messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            parts.append(f"{role}: {msg['content']}")
        return "\n".join(parts)

    def __len__(self) -> int:
        return len(self.messages)
