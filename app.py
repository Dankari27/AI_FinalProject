import streamlit as st
import os
import base64
import time
import re
import random
from google import genai
from google.genai import types


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

# ROLLING SLIDING WINDOW BASE PRUNE
current_timestamp = time.time()
st.session_state.request_history = [
    interaction for interaction in st.session_state.request_history 
    if current_timestamp - interaction[0] < 60
]

# CACHED CUSTOM CSS FOR BACKGROUND 
@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    bg_base64 = get_base64_of_bin_file("UI/background.gif")
    
    # Inject Custom CSS
    st.markdown(
        f"""
        <style>
        /* Define Camera Pan */
        @keyframes cinematicPan {{
            0%   {{ background-position: 0% 0%; }}
            25%  {{ background-position: 100% 15%; }}
            50%  {{ background-position: 85% 100%; }}
            75%  {{ background-position: 15% 85%; }}
            100% {{ background-position: 0% 0%; }}
        }}
        
        /* GIF and Camera Animation */
        .stApp {{
            background-image: url("data:image/gif;base64,{bg_base64}");
            
            /* Work Around For Image Stretching */
            background-size: max(115vw, 204.4vh) auto; 
            background-repeat: no-repeat;
            background-attachment: fixed;
            
            /* Trigger the pan: 60 seconds total, smooth easing, infinite loop */
            animation: cinematicPan 60s ease-in-out infinite;
        }}
        
        /* FROSTED GLASS EFFECT */
        .stApp > div:first-child {{
            background-color: rgba(10, 15, 25, 0.35) !important; 
            
            background-image: 
                radial-gradient(circle at 15% 25%, rgba(255, 255, 255, 0.2) 0%, transparent 40%),
                radial-gradient(circle at 85% 75%, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 50% 50%, rgba(0, 0, 0, 0.3) 0%, transparent 80%),
                url("data:image/svg+xml,%3Csvg viewBox='0 0 500 500' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='frost'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' result='noise'/%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.01' numOctaves='2' result='clouds'/%3E%3CfeDisplacementMap in='noise' in2='clouds' scale='30' xChannelSelector='R' yChannelSelector='G'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23frost)' opacity='0.04'/%3E%3C/svg%3E") !important;
            
            backdrop-filter: blur(5px) contrast(1.15) brightness(0.9) !important;
            -webkit-backdrop-filter: blur(5px) contrast(1.15) brightness(0.9) !important;
        }}
        
        /* Make Top Header Transparent to match background */
        [data-testid="stHeader"] {{
            background-color: transparent !important;
        }}

        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background-color: rgba(10, 15, 25, 0.45) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        [data-testid="stSidebarHeader"] {{
            background-color: transparent !important;
        }}

        /* MAKE BOTTOM CONTAINER FULLY TRANSPARENT */
        /* This lets the animated GIF reach to the bottom edge */
        [data-testid="stBottom"],
        [data-testid="stBottom"] > div,
        [data-testid="stBottomBlockContainer"] {{
            background-color: transparent !important;
            background: transparent !important;
        }}

        /* Style the Chat Input Box */
        [data-testid="stChatInput"] {{
            background-color: rgba(0, 0, 0, 0.7) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 10px !important;
        }}
        
        /* Strip the default grey background from all of Streamlit's layers */
        [data-testid="stChatInput"] div,
        [data-testid="stChatInput"] textarea {{
            background-color: transparent !important;
        }}
        
        /* OVERRIDE THE RED FOCUS OUTLINE WITH ORANGE (Inner Elements Only) */
        [data-testid="stChatInput"] > div:focus-within,
        [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {{
            border-color: #ff8c00 !important;
            border-width: 1px !important; 
            box-shadow: none !important; 
        }}
        
        /* Fixes cursor area spawning an extra ghost outline */
        [data-testid="stChatInput"] textarea:focus,
        [data-testid="stTextInput"] input:focus {{
            outline: none !important;
            box-shadow: none !important;
            border-color: transparent !important;
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
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
except FileNotFoundError:
    # If the file isn't there then pass silently so the app doesn't break
    pass


# This runs in an isolated loop every 2 seconds to keep the sliding window accurate without refreshing the chat
@st.fragment(run_every="2s")
def render_telemetry(selected_tier):
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
    
    # Context Window Calculation
    input_ratio = min(st.session_state.latest_input_tokens / INPUT_LIMIT, 1.0)
    st.markdown(f"**Context Window Utilization:** {input_ratio * 100:.2f}%")
    st.progress(input_ratio, text=f"{st.session_state.latest_input_tokens:,} / {INPUT_LIMIT:,}")
    
    # Output Buffer Tracking
    output_ratio = min(st.session_state.latest_output_tokens / OUTPUT_LIMIT, 1.0)
    st.markdown(f"**Generation Buffer Usage:** {output_ratio * 100:.2f}%")
    st.progress(output_ratio, text=f"{st.session_state.latest_output_tokens:,} / {OUTPUT_LIMIT:,}")
    
    st.markdown("---")
    
    # Live Velocity Metrics
    st.subheader("Rate Limit Buffer Status")
    
    # Adjust caps based on tier selection
    if selected_tier == "Free Tier":
        RPM_LIMIT = 15
        TPM_LIMIT = 1000000
    else:
        RPM_LIMIT = 1000
        TPM_LIMIT = 4000000
        
    # Recalculate sliding window dynamically based on the exact live uptime
    live_time = time.time()
    valid_history = [
        interaction for interaction in st.session_state.request_history 
        if live_time - interaction[0] < 60
    ]
    
    rolling_rpm = len(valid_history)
    rolling_tpm = sum(interaction[1] for interaction in valid_history)
    
    rpm_ratio = min(rolling_rpm / RPM_LIMIT, 1.0)
    st.markdown(f"**Velocity Rate (RPM Loading):** {rolling_rpm} / {RPM_LIMIT} Requests")
    st.progress(rpm_ratio)
    
    tpm_ratio = min(rolling_tpm / TPM_LIMIT, 1.0)
    st.markdown(f"**Throughput Density (TPM Loading):** {rolling_tpm:,} / {TPM_LIMIT:,} Tokens")
    st.progress(tpm_ratio)


# SIDEBAR: SETTINGS & METRICS
with st.sidebar:
    st.title("Tutor Settings")
    
    # Fallback for API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.warning("API Key not found in environment.")
        api_key = st.text_input("Enter Gemini API Key to continue:", type="password")
    else:
        st.success("API Key loaded from environment!")

    st.markdown("---")
    
    # TIER SELECTION 
    api_tier = st.radio("Gemini API Tier", ["Free Tier", "Paid Tier"], horizontal=True)
    
    st.markdown("---")
    
    # Trigger the realtime fragment 
    render_telemetry(api_tier)


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
    # Inject two invisible spaces so markdown works with single newlines
    prompt = prompt.replace('\n', '  \n')
    
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
                
        except Exception as e:
            # Check if it is a rate limit (429) error
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                error_msg = "Kip is typing too fast and needs to catch his breath! (You hit the free-tier API speed limit. Please wait about 60 seconds and try your message again!)"
                st.warning(error_msg)
            else:
                # Handle any other unexpected crashes
                st.error(f"Kip bumped his head on a bug! \n\nError details: {e}")