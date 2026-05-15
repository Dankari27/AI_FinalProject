import os
from google import genai
from google.genai import types

# 1. Try to get the key from the environment first
api_key = os.environ.get("GEMINI_API_KEY")

# 2. If it's not found, prompt the user to input it directly
if not api_key:
    print("\nGEMINI_API_KEY environment variable not found.")
    api_key = input("Please paste your Gemini API key to continue: ").strip()

# Initialize the Gemini client 
client = genai.Client(api_key=api_key)

# Prompt Instructions
# I'm aiming for a fun lovable personality cause standard AI personalities are boring
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

# Create a chat session with memory enabled
chat = client.chats.create(
    model="gemini-3-flash-preview",
    config=types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.3, # Low temperature for factual, consistent outputs
    )
)

def send_message_to_tutor(user_input: str):
    print(f"\nUser: {user_input}")
    
    # Send message to the model
    response = chat.send_message(user_input)
    
    print(f"\nTutor:\n{response.text}")
    
    # Extract token usage for cost analysis
    if response.usage_metadata:
        input_tokens = response.usage_metadata.prompt_token_count
        output_tokens = response.usage_metadata.candidates_token_count
        total_tokens = response.usage_metadata.total_token_count
        print("-" * 40)
        print(f"Token Tracker -> Input: {input_tokens} | Output: {output_tokens} | Total: {total_tokens}")
        print("-" * 40)

# Interactive Terminal Chat
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Welcome to the Python AI Tutor!")
    print("Type your questions below. Type 'quit' or 'exit' to end.")
    print("="*50 + "\n")
    
    while True:
        # Get input from the user
        user_message = input("You: ")
        
        # Check if the user wants to exit
        if user_message.lower() in ['quit', 'exit']:
            print("\nEnding tutoring session.\n")
            break
            
        # Skip sending empty messages
        if not user_message.strip():
            continue
            
        # Send the message and get the response
        send_message_to_tutor(user_message)