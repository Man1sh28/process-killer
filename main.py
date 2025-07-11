import tkinter as tk
from tkinter import scrolledtext, messagebox
import requests
import json
import os
import psutil
from dotenv import load_dotenv

# Load .env API key
load_dotenv()
API_KEY = os.getenv("API_KEY")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Ask Gemini with system prompt and running process info
def ask_gemini(prompt, process_list):
    system_prompt = f"""You are a macOS task assistant. You can only act on the following processes:

{process_list}

When asked to kill apps, respond ONLY in this JSON format:
```json
{{ "kill": ["AppName1", "AppName2"] }}
```"""

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": system_prompt}]},
            {"role": "user", "parts": [{"text": prompt}]}
        ]
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post(f"{ENDPOINT}?key={API_KEY}", headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    return response.json()["candidates"][0]["content"]["parts"][0]["text"]

# Get top 30 processes by memory (and ignore broken entries)
def get_running_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            p = proc.info
            if p['memory_percent'] is not None:
                processes.append(p)
        except:
            pass
    processes = sorted(processes, key=lambda x: x['memory_percent'], reverse=True)[:30]
    return processes

# Format processes for Gemini prompt
def format_process_list(processes):
    return "\n".join(f"{p['name']} (PID: {p['pid']}, {p['memory_percent']:.2f}%)" for p in processes)

# Kill matching processes safely
def kill_by_names(names):
    protected = ['launchd', 'kernel', 'system', 'windowserver', 'finder', 'dock']
    killed = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            name = proc.info['name'].lower()
            if any(n.lower() in name for n in names):
                if not any(p in name for p in protected):
                    proc.kill()
                    killed.append(proc.info['name'])
        except:
            pass
    return killed

# When user sends a message
def send_message(event=None):
    prompt = input_field.get()
    if not prompt.strip():
        return

    input_field.delete(0, tk.END)
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"You: {prompt}\n", "user")
    chat_box.see(tk.END)
    root.update()

    procs = get_running_processes()
    formatted_list = format_process_list(procs)
    
    try:
        response = ask_gemini(prompt, formatted_list)

        # Try to parse JSON from Gemini response
        cleaned = response.replace("```json", "").replace("```", "").strip()
        kill_list = json.loads(cleaned)["kill"]

        # Ask for confirmation before killing
        proc_names = "\n".join(kill_list)
        confirm = messagebox.askyesno("Confirm Kill", f"Gemini wants to kill these:\n\n{proc_names}\n\nDo you want to proceed?")
        if confirm:
            killed = kill_by_names(kill_list)
            reply = f"🔪 Killed: {', '.join(killed)}" if killed else "❌ No processes killed."
        else:
            reply = "🛑 Kill request cancelled."

    except Exception:
        
        reply = response

    chat_box.insert(tk.END, f"Gemini: {reply}\n", "gemini")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)

# GUI setup
root = tk.Tk()
root.title("TaskAI - Gemini Process Manager")
root.geometry("650x500")
root.resizable(False, False)

chat_box = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Segoe UI", 12))
chat_box.pack(padx=10, pady=(10, 0), fill=tk.BOTH, expand=True)
chat_box.tag_config("user", foreground="blue")
chat_box.tag_config("gemini", foreground="green")
chat_box.config(state=tk.DISABLED)

bottom_frame = tk.Frame(root)
bottom_frame.pack(fill=tk.X, padx=10, pady=10)

input_field = tk.Entry(bottom_frame, font=("Segoe UI", 12))
input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
input_field.bind("<Return>", send_message)

send_button = tk.Button(bottom_frame, text="Send", command=send_message, width=10)
send_button.pack(side=tk.RIGHT)

input_field.focus()
root.mainloop()

