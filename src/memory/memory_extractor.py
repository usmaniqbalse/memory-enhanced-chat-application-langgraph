"""Memory extraction from conversations using LLM."""
from typing import List
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage

from src.config import settings


class MemoryItem(BaseModel):
    """Represents an extracted memory item."""
    text: str = Field(description="Atomic user memory as a short sentence")
    is_new: bool = Field(description="True if this memory is NEW and should be stored")


class MemoryDecision(BaseModel):
    """Decision about what memories to extract and store."""
    should_write: bool = Field(description="Whether to store any memories")
    memories: List[MemoryItem] = Field(default_factory=list, description="List of memories to potentially store")


MEMORY_EXTRACTION_PROMPT = """You are responsible for updating and maintaining accurate user memory.

CURRENT USER MEMORIES (existing):
{existing_memories}

TASK:
- Review the user's latest message carefully.
- Extract user-specific information worth storing long-term:
  * Identity (name, profession, location)
  * Stable preferences (coding style, tools, frameworks)
  * Ongoing projects and goals
  * Important facts stated by the user
  
- For each extracted item, set is_new=true ONLY if it adds NEW information compared to CURRENT USER MEMORIES.
- If it's basically the same meaning as something already present, set is_new=false.
- Keep each memory as a short atomic sentence.
- No speculation; only extract facts explicitly stated by the user.
- If there is nothing memory-worthy, return should_write=false and an empty list.

Respond with a JSON object in this exact format:
{{"should_write": true/false, "memories": [{{"text": "memory text", "is_new": true/false}}]}}
"""


class MemoryExtractor:
    """Extracts memories from user messages using LLM."""
    
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1,
        )
    
    def extract_memories(self, user_message: str, existing_memories: str) -> MemoryDecision:
        """Extract potential memories from a user message."""
        prompt = MEMORY_EXTRACTION_PROMPT.format(existing_memories=existing_memories)
        
        try:
            response = self.llm.invoke([
                SystemMessage(content=prompt),
                {"role": "user", "content": f"USER MESSAGE:\n{user_message}"}
            ])
            
            # Parse the response as JSON
            content = response.content.strip()
            
            # Try to extract JSON from the response
            import json
            import re
            
            # Find JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return MemoryDecision(
                    should_write=data.get("should_write", False),
                    memories=[
                        MemoryItem(
                            text=m.get("text", ""),
                            is_new=m.get("is_new", False)
                        )
                        for m in data.get("memories", [])
                    ]
                )
            
            return MemoryDecision(should_write=False, memories=[])
            
        except Exception as e:
            print(f"Error extracting memories: {e}")
            return MemoryDecision(should_write=False, memories=[])
    
    def get_new_memories(self, user_message: str, existing_memories: str) -> List[str]:
        """Get list of new memories to store (filters out duplicates)."""
        decision = self.extract_memories(user_message, existing_memories)
        
        if not decision.should_write:
            return []
        
        return [
            mem.text.strip()
            for mem in decision.memories
            if mem.is_new and mem.text.strip()
        ]
