"""Chat history management for conversations."""
import uuid
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass

from .connection import get_db_connection


@dataclass
class Message:
    """Represents a chat message."""
    id: str
    conversation_id: str
    role: str
    content: str
    created_at: datetime


@dataclass
class Conversation:
    """Represents a conversation."""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatHistoryManager:
    """Manages chat history and conversations."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def create_conversation(self, title: Optional[str] = None) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        if not title:
            title = f"New Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversations (id, user_id, title)
                    VALUES (%s, %s, %s)
                    """,
                    (conversation_id, self.user_id, title)
                )
                conn.commit()
        
        return conversation_id
    
    def update_conversation_title(self, conversation_id: str, title: str):
        """Update conversation title."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE conversations 
                    SET title = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s AND user_id = %s
                    """,
                    (title[:100], conversation_id, self.user_id)
                )
                conn.commit()
    
    def get_conversations(self, limit: int = 50) -> List[Conversation]:
        """Get all conversations for the user."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, title, created_at, updated_at
                    FROM conversations
                    WHERE user_id = %s
                    ORDER BY updated_at DESC
                    LIMIT %s
                    """,
                    (self.user_id, limit)
                )
                rows = cur.fetchall()
                return [
                    Conversation(
                        id=str(row[0]),
                        user_id=row[1],
                        title=row[2],
                        created_at=row[3],
                        updated_at=row[4]
                    )
                    for row in rows
                ]
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a specific conversation."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, title, created_at, updated_at
                    FROM conversations
                    WHERE id = %s AND user_id = %s
                    """,
                    (conversation_id, self.user_id)
                )
                row = cur.fetchone()
                if row:
                    return Conversation(
                        id=str(row[0]),
                        user_id=row[1],
                        title=row[2],
                        created_at=row[3],
                        updated_at=row[4]
                    )
                return None
    
    def add_message(self, conversation_id: str, role: str, content: str) -> str:
        """Add a message to a conversation."""
        message_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (message_id, conversation_id, role, content)
                )
                # Update conversation timestamp
                cur.execute(
                    """
                    UPDATE conversations 
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (conversation_id,)
                )
                conn.commit()
        
        return message_id
    
    def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, conversation_id, role, content, created_at
                    FROM messages
                    WHERE conversation_id = %s
                    ORDER BY created_at ASC
                    """,
                    (conversation_id,)
                )
                rows = cur.fetchall()
                return [
                    Message(
                        id=str(row[0]),
                        conversation_id=str(row[1]),
                        role=row[2],
                        content=row[3],
                        created_at=row[4]
                    )
                    for row in rows
                ]
    
    def delete_conversation(self, conversation_id: str):
        """Delete a conversation and all its messages."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM conversations
                    WHERE id = %s AND user_id = %s
                    """,
                    (conversation_id, self.user_id)
                )
                conn.commit()
    
    def get_messages_as_langchain_format(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get messages in LangChain format."""
        messages = self.get_messages(conversation_id)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
