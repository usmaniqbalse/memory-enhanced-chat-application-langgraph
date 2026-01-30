"""Main Streamlit application for the Memory-Enhanced Chatbot."""
import streamlit as st
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import MemoryChatbot
from src.database.connection import init_database

# Page configuration
st.set_page_config(
    page_title="Memory Chat",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background-color: #0e1117;
    }
    
    /* Chat message styling */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 10px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
        color: #e2e8f0;
        padding: 15px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 10px 0;
        max-width: 80%;
        border: 1px solid #4a5568;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Conversation item styling */
    .conversation-item {
        background: #1e293b;
        padding: 12px 16px;
        border-radius: 12px;
        margin: 8px 0;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid #334155;
    }
    
    .conversation-item:hover {
        background: #334155;
        transform: translateX(5px);
        border-color: #667eea;
    }
    
    .conversation-item.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-color: transparent;
    }
    
    /* Memory card styling */
    .memory-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d2137 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 4px solid #38bdf8;
        transition: all 0.3s ease;
    }
    
    .memory-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(56, 189, 248, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background: #1e293b;
        border: 2px solid #334155;
        border-radius: 12px;
        color: white;
        padding: 15px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5em;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.8);
        margin: 10px 0 0 0;
    }
    
    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #1e3a5f 0%, #0d2137 100%);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        border: 1px solid #334155;
    }
    
    .stat-number {
        font-size: 2em;
        font-weight: bold;
        color: #38bdf8;
    }
    
    .stat-label {
        color: #94a3b8;
        font-size: 0.9em;
    }
    
    /* Divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 20px 0;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1e293b;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 4px;
    }
    
    /* Animation for new messages */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .new-message {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = "default_user"
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = None
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "db_initialized" not in st.session_state:
        st.session_state.db_initialized = False


def initialize_database():
    """Initialize the database if not already done."""
    if not st.session_state.db_initialized:
        try:
            init_database()
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"Failed to connect to database: {e}")
            st.info("Make sure PostgreSQL is running. Run: docker-compose up -d")
            return False
    return True


def get_chatbot() -> MemoryChatbot:
    """Get or create the chatbot instance."""
    if st.session_state.chatbot is None:
        st.session_state.chatbot = MemoryChatbot(st.session_state.user_id)
    return st.session_state.chatbot


def load_conversation(conversation_id: str):
    """Load a conversation into the current session."""
    chatbot = get_chatbot()
    messages = chatbot.get_conversation_messages(conversation_id)
    st.session_state.current_conversation_id = conversation_id
    st.session_state.messages = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


def render_sidebar():
    """Render the sidebar with conversation history and memories."""
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="color: #667eea; margin: 0;">🧠</h1>
            <h2 style="color: white; margin: 5px 0;">Memory Chat</h2>
            <p style="color: #94a3b8; font-size: 0.9em;">Powered by Llama 3.2</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        
        # New Chat button
        if st.button("➕ New Chat", use_container_width=True, key="new_chat"):
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
            st.rerun()
        
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        
        # Conversation History
        st.markdown("### 💬 Chat History")
        
        chatbot = get_chatbot()
        conversations = chatbot.get_conversations()
        
        if conversations:
            for conv in conversations:
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    is_active = st.session_state.current_conversation_id == conv.id
                    button_style = "primary" if is_active else "secondary"
                    
                    if st.button(
                        f"{'📍 ' if is_active else '💭 '}{conv.title[:30]}...",
                        key=f"conv_{conv.id}",
                        use_container_width=True,
                        type=button_style
                    ):
                        load_conversation(conv.id)
                        st.rerun()
                
                with col2:
                    if st.button("🗑️", key=f"del_{conv.id}", help="Delete conversation"):
                        chatbot.delete_conversation(conv.id)
                        if st.session_state.current_conversation_id == conv.id:
                            st.session_state.current_conversation_id = None
                            st.session_state.messages = []
                        st.rerun()
        else:
            st.info("No conversations yet. Start chatting!")
        
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        
        # Memories Section
        with st.expander("🧠 Stored Memories", expanded=False):
            memories = chatbot.get_memories()
            
            if memories:
                for memory in memories:
                    st.markdown(f"""
                    <div class="memory-card">
                        <p style="margin: 0; color: #e2e8f0;">{memory.memory_text}</p>
                        <small style="color: #64748b;">
                            {memory.created_at.strftime('%Y-%m-%d %H:%M')}
                        </small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("Delete", key=f"del_mem_{memory.id}", type="secondary"):
                        chatbot.delete_memory(memory.id)
                        st.rerun()
                
                st.markdown("---")
                if st.button("🗑️ Clear All Memories", type="secondary", use_container_width=True):
                    chatbot.clear_all_memories()
                    st.rerun()
            else:
                st.info("No memories stored yet. The AI will learn about you as you chat!")
        
        # Stats
        st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
        st.markdown("### 📊 Stats")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Conversations", len(conversations))
        with col2:
            st.metric("Memories", len(chatbot.get_memories()))


def render_chat_messages():
    """Render the chat messages."""
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message new-message">
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="assistant-message new-message">
                {message["content"]}
            </div>
            """, unsafe_allow_html=True)


def main():
    """Main application entry point."""
    init_session_state()
    
    # Initialize database
    if not initialize_database():
        return
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    st.markdown("""
    <div class="main-header">
        <h1>🧠 Memory-Enhanced Chat</h1>
        <p>Powered by Llama 3.2 with Long-Term Memory</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create chat container
    chat_container = st.container()
    
    with chat_container:
        render_chat_messages()
    
    # Chat input
    st.markdown("---")
    
    # Use a form for better UX
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        
        with col1:
            user_input = st.text_input(
                "Message",
                placeholder="Type your message here...",
                label_visibility="collapsed"
            )
        
        with col2:
            submit_button = st.form_submit_button("Send 🚀", use_container_width=True)
    
    # Process user input
    if submit_button and user_input:
        chatbot = get_chatbot()
        
        # Add user message to display
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Get response from chatbot
        with st.spinner("🤔 Thinking..."):
            response, conversation_id = chatbot.chat(
                user_input,
                st.session_state.current_conversation_id
            )
        
        # Update session state
        st.session_state.current_conversation_id = conversation_id
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Rerun to display new messages
        st.rerun()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 30px; color: #64748b;">
        <p>Built with ❤️ using LangGraph, Streamlit, and Ollama</p>
        <p style="font-size: 0.8em;">Your conversations are stored locally in PostgreSQL</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
