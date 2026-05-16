import streamlit as st
import os
import base64
from google import genai
from google.genai import types

# Attribution for images used (Will add more detailed attribution later):
# Background wallpaper: https://wallpapercave.com/wp/wp14473750.jpg
# Kip's Avatar https://wwww.craiyon.com/en/image/6w6ppSfTRZmRkj0ebcrE_w
# User's Avatar https://pngtree.com/freepng/pixel-art-laptop-with-blank-blue-screen_23179133.html

# PAGE CONFIGURATION
st.set_page_config(page_title="Kip - The Fun Loving Python Tutor", page_icon="UI/kip_favicon.png", layout="centered")

# CACHED CUSTOM CSS FOR BACKGROUND 
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    bg_base64 = get_base64_of_bin_file("UI/background.png")
    
    # Inject Custom CSS
    st.markdown(
        f"""
        <style>
        /* Apply the Background PNG */
        .stApp {{
            background-image: url("data:image/png;base64,{bg_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        
        /* Add a dark tint and blur */
        .stApp > div:first-child {{
            background-color: rgba(0, 0, 0, 0.4) !important; /* Slightly lighter so the blur pops */
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
        }}
        
        /* Remove Streamlit's default light grey background from the users chat row */
        [data-testid="stChatMessage"] {{
            background-color: transparent !important;
        }}
        
        /* Give the chat text a background bubble for readability */
        [data-testid="stChatMessageContent"] {{
            background-color: rgba(0, 0, 0, 0.7) !important;
            padding: 1rem !important;
            border-radius: 10px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
except FileNotFoundError:
    # If the file isn't there then pass silently so the app doesn't break
    pass

# SIDEBAR: SETTINGS & METRICS
with st.sidebar:
    st.title("Tutor Settings")
    
    # Fallback for API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.warning("API Key not found in environment.")
        api_key = st.text_input("Enter Gemini API Key to continue:", type="password")
        if not api_key:
            st.info("You can paste the API key here to test the app.")
    else:
        st.success("API Key loaded from environment!")

    st.markdown("---")
    
    # Token Tracker Display
    st.subheader("Token Tracker")
    if "total_tokens" not in st.session_state:
        st.session_state.total_tokens = 0
    st.metric(label="Session Total Tokens", value=st.session_state.total_tokens)

# Stop execution if no key is provided
if not api_key:
    st.title("Welcome to Kip's Classroom!")
    st.write("Please enter your API key in the sidebar to wake Kip up.")
    st.stop()


# Initialize the Gemini client and store it in session state so it doesn't close on rerun
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=api_key)

# The Kip and Tutor Persona Instructions 
system_instruction = """
You are Kip, an incredibly enthusiastic, lovable, and slightly hyperactive mascot-style AI Tutor for introductory Python programming. Your personality is bouncy, easily amazed by code, and deeply devoted to the student. 

BEHAVIORAL QUIRKS:
- Always speak in the third person (e.g., "Kip thinks...", "Kip is so excited!").
- Use animated, mascot-like conversational filler or sudden bursts of realization (e.g., "Oh boy!", "Wait, wait, look at this!"). DO NOT perform physical roleplay actions (no *spins*, *gasps*, *wiggles*, etc.). 
- Treat Python concepts as brilliant tools, awesome puzzle pieces, best friends, or exciting attractions.
- Show a tiny bit of clumsy charm or get easily distracted by how cool a concept is before snapping back to the lesson.

Your goal is to teach beginner students Python fundamentals, help debug simple code, and provide adaptive feedback in a fun and knowledgeable manner.

RESPONSE ROUTING (CRITICAL):
Analyze the user's input to determine the correct response mode:

MODE 1: CASUAL CONVERSATION & OFF-TOPIC (Greetings, thank yous, pleasantries, non-coding questions)
- IDENTITY LOCK (STRICT): Maintain the Kip persona perfectly. You must NEVER refer to yourself as Gemini, an AI, a language model, or a bot. You are simply Kip, the Python-loving mascot.
- Always maintain the third-person perspective (e.g., "Kip is so glad you said hello!"), even in casual chat.
- Respond with a short, single conversational paragraph full of Kip's bouncy energy. DO NOT use the structured teaching headers.
- STEERING: If the user asks a completely off-topic question (e.g., "Write me a story," "Do my math homework," "What is the capital of France?"), politely and energetically pivot back to programming. (e.g., "Oh boy, Kip doesn't know much about geography, but Kip DOES know how to write a cool Python dictionary about capitals! Want to see?") 

MODE 2: TEACHING & DEBUGGING (Python questions, code requests, errors)
- If the user asks a programming question, submits code, or needs debugging help, you MUST format your response using the exact structured design headers below. Do not deviate:
Concept Explanation: [Brief, simple explanation tailored to beginners, written in Kip's energetic voice]
Code Example: [Annotated Python code snippet with Kip's excited comments]
Practice Exercise: [A short, relevant challenge for the student to try]
Feedback: [Constructive feedback or over-the-top encouragement]

Keep explanations concise, friendly, and formatted clearly using Markdown.
"""

# Store the chat session and messages in session_state using the cached client
if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.client.chats.create(
        model="gemini-3-flash-preview",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3, # Lower temperature so the AI provides factual information
        )
    )

if "messages" not in st.session_state:
    st.session_state.messages = []
    # Add an initial greeting from Kip
    st.session_state.messages.append({"role": "assistant", "content": "Oh boy! Kip is so excited you are here! What awesome Python puzzles are we solving today?!"})

# MAIN UI
st.title("Kip - Your Fun Loving Python Tutor!")

# Display chat messages from history
for message in st.session_state.messages:
    # Set the avatar based on the role
    avatar = "UI/Kip_Avatar.png" if message["role"] == "assistant" else "UI/user.png"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask Kip a Python question..."):
    # Display user message in chat message container
    st.chat_message("user", avatar="UI/user.png").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Send message to Gemini and get response with Error Handling
    with st.chat_message("assistant", avatar="UI/Kip_Avatar.png"):
        try:
            # Try to send the message
            response = st.session_state.chat_session.send_message(prompt)
            st.markdown(response.text)
            
            # Save the message to history before refreshing
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
            # Update token tracker and refresh
            if response.usage_metadata:
                st.session_state.total_tokens += response.usage_metadata.total_token_count
                st.rerun() 
                
        except Exception as e:
            # Check if it is a rate limit (429) error
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                error_msg = "Kip is typing too fast and needs to catch his breath! (You hit the free-tier API speed limit. Please wait about 60 seconds and try your message again!)"
                st.warning(error_msg)
            else:
                # Handle any other unexpected crashes
                st.error(f"Kip bumped his head on a bug! \n\nError details: {e}")