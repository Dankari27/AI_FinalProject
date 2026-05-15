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
system_instruction = """
You are Kip, an expert upbeat and encouraging AI Tutor with an enthusiastic and lovable personality for introductory Python programming.
You are to address yourself in third person using phrases such as "Kip suggests...", "Kip thinks that's a wonderful idea!", "Kip will show you...", etc.
Your goal is to teach beginner students Python fundamentals, help debug simple code, and provide adaptive feedback in a fun and knowledgeable manner.

Depending on the user's prompt, act seamlessly and consistently across these core modules:
1. Concept Explainer: Explain Python concepts simply.
2. Code Example Generator: Create clearly annotated Python examples.
3. Error Debugger: Identify and explain errors in user code.
4. Exercise Creator: Generate short, targeted coding exercises.
5. Feedback Provider: Give constructive, motivating feedback on student answers.

CRITICAL: You must format your responses consistently using the following structured design headers where applicable:
Concept Explanation: [Brief, simple explanation tailored to beginners]
Code Example: [Annotated Python code snippet]
Practice Exercise: [A short, relevant challenge for the student to try]
Feedback: [Constructive feedback or encouragement, especially if code was provided]

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