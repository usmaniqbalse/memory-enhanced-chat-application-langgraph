"""Long-term memory storage using PostgreSQL."""
import uuid
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from src.database.connection import get_db_connection


@dataclass
class Memory:
    """Represents a user memory."""
    id: str
    user_id: str
    memory_text: str
    created_at: datetime


class MemoryStore:
    """Manages long-term memory storage in PostgreSQL."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def add_memory(self, memory_text: str) -> Optional[str]:
        """Add a new memory. Returns memory ID if successful, None if duplicate."""
        memory_id = str(uuid.uuid4())
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                try:
                    cur.execute(
                        """
                        INSERT INTO user_memories (id, user_id, memory_text)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (user_id, memory_text) DO NOTHING
                        RETURNING id
                        """,
                        (memory_id, self.user_id, memory_text.strip())
                    )
                    result = cur.fetchone()
                    conn.commit()
                    return str(result[0]) if result else None
                except Exception:
                    conn.rollback()
                    return None
    
    def get_all_memories(self) -> List[Memory]:
        """Get all memories for the user."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, memory_text, created_at
                    FROM user_memories
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    """,
                    (self.user_id,)
                )
                rows = cur.fetchall()
                return [
                    Memory(
                        id=str(row[0]),
                        user_id=row[1],
                        memory_text=row[2],
                        created_at=row[3]
                    )
                    for row in rows
                ]
    
    def get_memories_as_string(self) -> str:
        """Get all memories formatted as a string for prompts."""
        memories = self.get_all_memories()
        if not memories:
            return "(No memories stored yet)"
        return "\n".join(f"- {mem.memory_text}" for mem in memories)
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM user_memories
                    WHERE id = %s AND user_id = %s
                    """,
                    (memory_id, self.user_id)
                )
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted
    
    def clear_all_memories(self):
        """Clear all memories for the user."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM user_memories
                    WHERE user_id = %s
                    """,
                    (self.user_id,)
                )
                conn.commit()
    
    def search_memories(self, query: str, limit: int = 5) -> List[Memory]:
        """Search memories using simple text matching."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, user_id, memory_text, created_at
                    FROM user_memories
                    WHERE user_id = %s 
                    AND LOWER(memory_text) LIKE LOWER(%s)
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (self.user_id, f"%{query}%", limit)
                )
                rows = cur.fetchall()
                return [
                    Memory(
                        id=str(row[0]),
                        user_id=row[1],
                        memory_text=row[2],
                        created_at=row[3]
                    )
                    for row in rows
                ]
