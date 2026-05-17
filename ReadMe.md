# Kip - The Python Tutor

## Description
<p align="left">
  <img src="UI/kip_favicon.png" alt="Meet Kip!" style="max-width: 150px; width: 100%; height: auto;"><br>
  <em><b>Meet Kip!</b></em>
</p>
This is an interactive web app built for COSC461's final project that teaches Python basics to beginners. It uses Google's Gemini 3 Preview LLM to create a structured and engaging way to learn programming.

---

Instead of making yet another boring AI chatbot that drones on about syntax, I created **Kip**, a bouncy and enthusiastic little mascot who treats every Python concept like it's the coolest puzzle you've ever seen.

### What Makes It Special
* **Smart Response Routing:** Kip knows the difference between you just chatting ("hey what's up?") and actually asking about Python stuff. This keeps the fun personality consistent no matter what you're talking about.
* **Learning Modules That Actually Make Sense:** When you ask about Python concepts, responses automatically get organized into four clear sections: understanding the concept, seeing code examples, trying practice exercises, and getting feedback.
* **Code Feedback That Helps:** Submit your code and the system will check it, catch errors, and give you helpful feedback instead of just telling you "wrong, try again."
* **Token Counter:** There's a live counter in the sidebar that tracks API usage during your session. Super useful for monitoring costs and performance.
* **Doesn't Crash When Things Go Wrong:** Built-in handling for when the API hits rate limits. Instead of breaking, Kip just asks you to wait a bit in character.
* **Custom Look:** I designed the UI using Streamlit with a frosted glass CSS effect and responsive chat layout that actually looks nice.

---

## Prerequisites
Before you can wake Kip up, you need to have Python installed on your computer. 

* **Installing Python:** Download the latest version from [python.org](https://www.python.org/).

**Important: If you are on Windows, make sure to check the box that says "Add Python.exe to PATH" during the installation process.**

Once Python is installed, the application relies on two specific libraries:
* streamlit (runs the web interface)
* google-genai (connects to the Gemini API)

---

## Getting Started

**1. Grab the Project Files**

Ensure you have the complete project folder, including the main Python script and the UI folder containing the visual assets. Your directory should look like this:

    AI_FinalProject/
    │
    ├── app.py                  # Main application script
    ├── README.md               # Project documentation
    └── UI/                     # UI Assets folder
        ├── background.gif      
        ├── Kip_Avatars(7 total)
        ├── kip_favicon.png
        └── user.png            

**2. Install Required Packages**

This single command will install both Streamlit and the Google Gemini SDK. Open your terminal or command prompt, navigate to the project folder, and run:

    pip install streamlit google-genai

**3. Set Up Your API Key**

You'll need a Gemini API key to use the app. I built in two ways to do this:
* **Easy Way (Environment Variable):** [Set an environment variable](https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/) called **GEMINI_API_KEY** and the app will find it automatically.
* **Backup Way (Through the UI):** If you don't have an environment variable set up, the app will pause and show a secure input field in the sidebar where you can paste your [API key](https://aistudio.google.com/api-keys) directly.

**4. Fire It Up**

Run this command in your terminal to start the local web server:

    streamlit run app.py

Your browser should automatically open to http://localhost:8501 with Kip ready to help you learn Python!

---

## Asset Attribution
The visual assets used in this custom UI are credited to the following creators and platforms:

* **User Avatar:** Orange user icon vector by [faizan11](https://www.vectorstock.com/royalty-free-vector/orange-user-icon-vector-42797453) - License: Standard Royalty-Free License