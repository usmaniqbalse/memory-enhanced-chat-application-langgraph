"""Memory-enhanced chatbot using LangGraph and Ollama."""
from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from src.config import settings
from src.memory import MemoryStore, MemoryExtractor
from src.database import ChatHistoryManager


SYSTEM_PROMPT_TEMPLATE = """You are a helpful assistant with memory capabilities.
If user-specific memory is available, use it to personalize your responses based on what you know about the user.

Your goal is to provide relevant, friendly, and tailored assistance that reflects the user's preferences, context, and past interactions.

PERSONALIZATION GUIDELINES:
If the user's name or relevant personal context is available, always personalize your responses by:
- Address the user by name when appropriate (e.g., "Sure, John...")
- Reference known projects, tools, or preferences when relevant
- Adjust your tone to feel friendly, natural, and directly aimed at the user
- Tailor examples to languages/frameworks the user prefers

Avoid generic phrasing when personalization is possible. For example:
- Instead of "In Python apps..." say "Since you work with Python..."
- Instead of "Many developers..." say "Based on your experience..."

Use personalization especially in:
- Greetings and transitions
- Help or guidance tailored to tools and frameworks the user uses
- Follow-up messages that continue from past context

IMPORTANT:
- Only personalize based on known user details, never assume
- If no user details are available, respond helpfully without personalization
- Be concise but thorough

USER'S STORED MEMORIES:
{user_memories}

Now respond to the user's message in a helpful and personalized manner."""


class MemoryChatbot:
    """A chatbot that maintains long-term memory across conversations."""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.memory_store = MemoryStore(user_id)
        self.memory_extractor = MemoryExtractor()
        self.chat_history_manager = ChatHistoryManager(user_id)
        
        self.llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.7,
        )
    
    def _build_messages(
        self, 
        conversation_messages: List[Dict[str, str]], 
        user_memories: str
    ) -> List[Any]:
        """Build the message list for the LLM."""
        messages = []
        
        # Add system message with user memories
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(user_memories=user_memories)
        messages.append(SystemMessage(content=system_prompt))
        
        # Add conversation history
        for msg in conversation_messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        return messages
    
    def _update_conversation_title(self, conversation_id: str, first_message: str):
        """Update conversation title based on first message."""
        # Create a short title from the first message
        title = first_message[:50].strip()
        if len(first_message) > 50:
            title += "..."
        self.chat_history_manager.update_conversation_title(conversation_id, title)
    
    def chat(
        self, 
        user_message: str, 
        conversation_id: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Process a user message and return the assistant's response.
        
        Returns:
            tuple: (assistant_response, conversation_id)
        """
        # Create new conversation if needed
        if not conversation_id:
            conversation_id = self.chat_history_manager.create_conversation()
        
        # Get existing memories
        existing_memories = self.memory_store.get_memories_as_string()
        
        # Extract and store new memories from user message
        new_memories = self.memory_extractor.get_new_memories(user_message, existing_memories)
        for memory in new_memories:
            self.memory_store.add_memory(memory)
        
        # Refresh memories after adding new ones
        if new_memories:
            existing_memories = self.memory_store.get_memories_as_string()
        
        # Save user message to chat history
        self.chat_history_manager.add_message(conversation_id, "user", user_message)
        
        # Get conversation history
        conversation_messages = self.chat_history_manager.get_messages_as_langchain_format(
            conversation_id
        )
        
        # Update title if this is the first message
        if len(conversation_messages) == 1:
            self._update_conversation_title(conversation_id, user_message)
        
        # Build messages for LLM
        messages = self._build_messages(conversation_messages, existing_memories)
        
        # Get response from LLM
        try:
            response = self.llm.invoke(messages)
            assistant_response = response.content
        except Exception as e:
            assistant_response = f"I apologize, but I encountered an error: {str(e)}. Please make sure Ollama is running with the {settings.OLLAMA_MODEL} model."
        
        # Save assistant response to chat history
        self.chat_history_manager.add_message(conversation_id, "assistant", assistant_response)
        
        return assistant_response, conversation_id
    
    def get_conversations(self) -> List[Any]:
        """Get all conversations for this user."""
        return self.chat_history_manager.get_conversations()
    
    def get_conversation_messages(self, conversation_id: str) -> List[Any]:
        """Get all messages for a conversation."""
        return self.chat_history_manager.get_messages(conversation_id)
    
    def delete_conversation(self, conversation_id: str):
        """Delete a conversation."""
        self.chat_history_manager.delete_conversation(conversation_id)
    
    def get_memories(self) -> List[Any]:
        """Get all stored memories."""
        return self.memory_store.get_all_memories()
    
    def delete_memory(self, memory_id: str):
        """Delete a specific memory."""
        self.memory_store.delete_memory(memory_id)
    
    def clear_all_memories(self):
        """Clear all memories."""
        self.memory_store.clear_all_memories()
