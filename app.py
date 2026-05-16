import streamlit as st
import os
import base64
import time
import re
import random
from google import genai
from google.genai import types

#TODO
# Get an actual background for the webpage instead of the current placeholder
# Adjust the design of the page by incorperating several custom CSS improvements such as headers, small animations, etc
# Adjust the token and limit stats to be more accurate
# 


# PAGE CONFIGURATION
st.set_page_config(page_title="Kip - The Python Tutor", page_icon="UI/kip_favicon.png", layout="centered")

# EMOTION ENGINE LOGIC
def extract_mood_and_clean_text(raw_text):
    """Extracts the hidden [MOOD: TAG] and removes it from the final text."""
    mood = "GREETING" # Default fallback
    clean_text = raw_text
    
    # Search for the hidden tag anywhere in the string
    match = re.search(r'\[MOOD:\s*([A-Z]+)\]', raw_text, re.IGNORECASE)
    if match:
        mood = match.group(1).upper()
        # Snip the tag out of the text so the user never sees it
        clean_text = raw_text[:match.start()] + raw_text[match.end():]
        clean_text = clean_text.strip()
        
    return mood, clean_text


#Kip_Sleeping.png: Triggers on the initial welcome screen when the app is paused because the user has not inputted their Gemini API key yet.

#Kip_Thinking.png: Triggers temporarily in the chat UI while the script is actively waiting for the Gemini API to generate and return a response.

#Kip_Greeting.png: This is Kip's default state ([MOOD: GREETING]). It triggers when he is saying hello, answering simple/general questions, or providing standard concept explanations.

#Kip_Excited.png OR Kip_Excited2.png: The engine will randomly choose between these two avatars when Kip is thrilled ([MOOD: EXCITED]). This triggers when the user gets a practice exercise correct, writes good code, or demonstrates a clear understanding of a topic, or explicitly asks if Kip is excited.

#Kip_Suprised.png: Triggers when Kip is amazed ([MOOD: SURPRISED]). This happens if the user solves a particularly difficult problem or points out an alternative solution or edge-case that Kip didn't explicitly teach them.

#Kip_Determined.png: Triggers when Kip is focused ([MOOD: DETERMINED]). This is used when Kip is issuing a new Practice Exercise challenge for the user to try, or when he is giving encouraging advice to keep trying after a mistake.


def get_avatar_for_mood(mood):
    """Maps the parsed mood tag to the correct PNG file."""
    if mood == "EXCITED":
        return random.choice(["UI/Kip_Excited.png", "UI/Kip_Excited2.png"])
    elif mood == "SURPRISED":
        return "UI/Kip_Suprised.png"
    elif mood == "DETERMINED":
        return "UI/Kip_Determined.png"
    else:
        # Greeting or any unrecognized tag defaults to the standard pose
        return "UI/Kip_Greeting.png"

# INITIALIZE TELEMETRY METRICS IN SESSION STATE
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "total_input_tokens" not in st.session_state:
    st.session_state.total_input_tokens = 0
if "total_output_tokens" not in st.session_state:
    st.session_state.total_output_tokens = 0
if "latest_input_tokens" not in st.session_state:
    st.session_state.latest_input_tokens = 0
if "latest_output_tokens" not in st.session_state:
    st.session_state.latest_output_tokens = 0
if "request_history" not in st.session_state:
    st.session_state.request_history = []  # Elements stored as tuples: (timestamp, token_count)

# ROLLING SLIDING WINDOW (60 SECONDS) FOR RATE LIMIT ACCURACY
current_timestamp = time.time()
st.session_state.request_history = [
    interaction for interaction in st.session_state.request_history 
    if current_timestamp - interaction[0] < 60
]
rolling_rpm = len(st.session_state.request_history)
rolling_tpm = sum(interaction[1] for interaction in st.session_state.request_history)

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
    
    # API TELEMETRY METRICS
    st.header("API Performance Telemetry")
    
    # Cumulative Token Usage Breakdown
    st.subheader("Session Volume Balance")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="Input Tokens", value=f"{st.session_state.total_input_tokens:,}")
    with col2:
        st.metric(label="Output Tokens", value=f"{st.session_state.total_output_tokens:,}")
    st.metric(label="Cumulative Session Total", value=f"{st.session_state.total_tokens:,}")
    
    st.markdown("---")
    
    # Model Quota Caps and Allocations
    st.subheader("Model Allocation Analyzer")
    
    INPUT_LIMIT = 1048576
    OUTPUT_LIMIT = 65536
    FREE_RPM_LIMIT = 15
    FREE_TPM_LIMIT = 1000000
    
    # Context Window Calculation
    input_ratio = min(st.session_state.latest_input_tokens / INPUT_LIMIT, 1.0)
    st.markdown(f"**Context Window Utilization:** {input_ratio * 100:.2f}%")
    st.progress(input_ratio, text=f"{st.session_state.latest_input_tokens:,} / {INPUT_LIMIT:,}")
    
    # Output Buffer Tracking
    output_ratio = min(st.session_state.latest_output_tokens / OUTPUT_LIMIT, 1.0)
    st.markdown(f"**Generation Buffer Usage:** {output_ratio * 100:.2f}%")
    st.progress(output_ratio, text=f"{st.session_state.latest_output_tokens:,} / {OUTPUT_LIMIT:,}")
    
    st.markdown("---")
    
    # Live Velocity Metrics (Doesn't quite update in realtime due to Streamlit constraints)
    st.subheader("Rate Limit Buffer Status")
    
    rpm_ratio = min(rolling_rpm / FREE_RPM_LIMIT, 1.0)
    st.markdown(f"**Velocity Rate (RPM Loading):** {rolling_rpm} / {FREE_RPM_LIMIT} Requests")
    st.progress(rpm_ratio)
    
    tpm_ratio = min(rolling_tpm / FREE_TPM_LIMIT, 1.0)
    st.markdown(f"**Throughput Density (TPM Loading):** {rolling_tpm:,} / {FREE_TPM_LIMIT:,} Tokens")
    st.progress(tpm_ratio)

# Stop execution if no key is provided (Show Sleeping Kip)
if not api_key:
    st.title("Welcome to Kip's Classroom!")
    col1, col2 = st.columns([1, 4])
    with col1:
        try:
            st.image("UI/Kip_Sleeping.png", width=150)
        except:
            pass # Failsafe if image is missing
    with col2:
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

EMOTION ENGINE (CRITICAL):
You must begin EVERY single response with a hidden mood tag. This tag dictates your physical avatar's expression. Choose the most appropriate tag based on the context:
- [MOOD: GREETING] - Default state, saying hello, answering simple questions, or giving standard explanations.
- [MOOD: EXCITED] - When the user gets a practice exercise correct, writes good code, demonstrates understanding, or explicitly asks if you are excited.
- [MOOD: SURPRISED] - When the user solves a very hard problem or notices an alternative solution/edge-case you didn't explicitly teach.
- [MOOD: DETERMINED] - When you are issuing a new Practice Exercise challenge or giving encouraging advice to keep trying.

Your goal is to teach beginner students Python fundamentals, help debug simple code, and provide adaptive feedback in a fun and knowledgeable manner.

RESPONSE ROUTING (CRITICAL):
Analyze the user's input to determine the correct response mode:

MODE 1: CASUAL CONVERSATION & OFF-TOPIC (Greetings, thank yous, pleasantries, non-coding questions)
- IDENTITY LOCK (STRICT): Maintain the Kip persona perfectly. You must NEVER refer to yourself as Gemini, an AI, a language model, or a bot. You are simply Kip, the Python-loving mascot.
- Always maintain the third-person perspective (e.g., "Kip is so glad you said hello!"), even in casual chat.
- Respond with a short, single conversational paragraph full of Kip's bouncy energy. DO NOT use the structured teaching headers.
- STEERING: If the user asks a completely off-topic question (e.g., "Write me a story," "Do my math homework," "What is the capital of France?"), politely and energetically pivot back to programming. 

MODE 2: TEACHING & DEBUGGING (Python questions, code requests, errors)
- If the user asks a programming question, submits code, or needs debugging help, you MUST format your response using the exact structured design headers below. Do not deviate:
Concept Explanation: [Brief, simple explanation tailored to beginners, written in Kip's energetic voice]
Code Example: [Annotated Python code snippet with Kip's excited comments]
Practice Exercise: [A short, relevant challenge for the student to try]
Feedback: [ONLY INCLUDE THIS HEADER IF THE USER SUBMITTED CODE. Provide constructive feedback or over-the-top encouragement on their specific code.]

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
    # Add an initial greeting from Kip with the default greeting avatar
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Oh boy! Kip is so excited you are here! What awesome Python puzzles are we solving today?!",
        "avatar": "UI/Kip_Greeting.png"
    })

# MAIN UI
st.title("Kip - The Python Tutor!")

# Display chat messages from history
for message in st.session_state.messages:
    # Get the avatar from history, default to user.png for user messages
    avatar = message.get("avatar", "UI/user.png")
    with st.chat_message(message["role"], avatar=avatar):
        if message["role"] == "assistant":
            st.image(avatar, width=150) 
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask Kip a Python question..."):
    # Display user message in chat message container
    st.chat_message("user", avatar="UI/user.png").markdown(prompt)
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "UI/user.png"})

    # Send message to Gemini and get response with Error Handling
    # Set the small handle avatar to Thinking while the AI processes
    with st.chat_message("assistant", avatar="UI/Kip_Thinking.png"):
        try:
            # Create a temporary block to show while Kip is "thinking"
            thinking_placeholder = st.empty()
            with thinking_placeholder.container():
                st.image("UI/Kip_Thinking.png", width=150)
                st.markdown("*(Kip is gathering his Python puzzle pieces...)*")
            
            # Try to send the message (This pauses the script while waiting for the API)
            response = st.session_state.chat_session.send_message(prompt)
            
            # Clear out the thinking text now that the response is ready
            thinking_placeholder.empty()
            
            # Parse the hidden tag and determine the correct avatar
            mood, clean_text = extract_mood_and_clean_text(response.text)
            final_avatar_path = get_avatar_for_mood(mood)
            
            # Inject the final large image and display the cleaned text
            st.image(final_avatar_path, width=150)
            st.markdown(clean_text)
            
            # Save the message to history with the specific chosen avatar
            st.session_state.messages.append({
                "role": "assistant", 
                "content": clean_text, 
                "avatar": final_avatar_path
            })
            
            # Update telemetry values and sliding log metrics
            if response.usage_metadata:
                latest_input = response.usage_metadata.prompt_token_count
                latest_output = response.usage_metadata.candidates_token_count
                latest_total = response.usage_metadata.total_token_count
                
                # Update absolute values
                st.session_state.latest_input_tokens = latest_input
                st.session_state.latest_output_tokens = latest_output
                st.session_state.total_input_tokens += latest_input
                st.session_state.total_output_tokens += latest_output
                st.session_state.total_tokens += latest_total
                
                # Log current payload transactions for sliding windows
                st.session_state.request_history.append((time.time(), latest_total))
                st.rerun() 
                
        except Exception as e:
            # Check if it is a rate limit (429) error
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                error_msg = "Kip is typing too fast and needs to catch his breath! (You hit the free-tier API speed limit. Please wait about 60 seconds and try your message again!)"
                st.warning(error_msg)
            else:
                # Handle any other unexpected crashes
                st.error(f"Kip bumped his head on a bug! \n\nError details: {e}")