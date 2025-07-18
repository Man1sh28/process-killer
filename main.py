import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import requests
import json
import os
import psutil
from dotenv import load_dotenv
import subprocess
import time


load_dotenv()
API_KEY = os.getenv("API_KEY")
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

import os

def get_installed_apps():
    app_dirs = ["/Applications", "/System/Applications"]
    apps = []

    for app_dir in app_dirs:
        try:
            for item in os.listdir(app_dir):
                if item.endswith(".app"):
                    apps.append(item.replace(".app", ""))
        except Exception:
            continue

    return sorted(list(set(apps)))

installed_apps = ", ".join(get_installed_apps())
def ask_gemini(prompt, process_list):
    system_prompt = f"""
You are a chatbot assistant that tells me the general knowledge data helps me in daily processes that can also help in opening and killing in macoos

Here is a list of installed apps:
{installed_apps}

Here is a list of currently running processes:
{process_list}

When asked to **open** or **kill** apps, respond ONLY in this format:


{{ "open": ["AppName1", "AppName2"], "kill": ["AppName3", "AppName4"] }}


"""

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

def open_apps(app_names):
    opened = []
    app_dirs = ["/Applications", "/System/Applications"]

    for app_name in app_names:
        found = False
        for dir in app_dirs:
            for item in os.listdir(dir):
                if item.lower().endswith(".app") and app_name.lower() in item.lower():
                    app_path = os.path.join(dir, item)
                    try:
                        subprocess.run(["open", app_path])
                        opened.append(item.replace(".app", ""))
                        found = True
                        break
                    except Exception:
                        pass
            if found:
                break
    return opened

def show_kill_dialog(kill_list):
    """Show a dialog with checkboxes for each process to kill"""
    kill_dialog = tk.Toplevel(root)
    kill_dialog.title("Select Processes to Kill")
    kill_dialog.geometry("450x400")
    kill_dialog.resizable(False, False)
    kill_dialog.grab_set()  # Make it modal
    
    # Center the dialog
    kill_dialog.transient(root)
    kill_dialog.geometry("+%d+%d" % (root.winfo_rootx() + 50, root.winfo_rooty() + 50))
    
    # Main frame
    main_frame = ttk.Frame(kill_dialog, padding="10")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Title
    title_label = ttk.Label(main_frame, text="Select processes to kill:", font=("Segoe UI", 12, "bold"))
    title_label.pack(anchor=tk.W, pady=(0, 10))
    
    # Scrollable frame for checkboxes
    canvas = tk.Canvas(main_frame, height=250)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Store checkbox variables
    checkbox_vars = {}
    
    # Get current processes for detailed info
    current_processes = get_running_processes()
    process_info = {p['name']: p for p in current_processes}
    
    # Create checkboxes for each process
    for i, process_name in enumerate(kill_list):
        var = tk.BooleanVar()
        checkbox_vars[process_name] = var
        
        # Get process info if available
        info = process_info.get(process_name, {})
        memory_info = f" ({info.get('memory_percent', 0):.1f}% RAM)" if info else ""
        
        # Check if process is protected
        protected = ['launchd', 'kernel', 'system', 'windowserver', 'finder', 'dock']
        is_protected = any(p in process_name.lower() for p in protected)
        
        checkbox_frame = ttk.Frame(scrollable_frame)
        checkbox_frame.pack(fill=tk.X, pady=2)
        
        cb = ttk.Checkbutton(
            checkbox_frame,
            text=f"{process_name}{memory_info}",
            variable=var,
            state="disabled" if is_protected else "normal"
        )
        cb.pack(side=tk.LEFT)
        
        if is_protected:
            warning_label = ttk.Label(checkbox_frame, text="(Protected)", foreground="red", font=("Segoe UI", 9))
            warning_label.pack(side=tk.LEFT, padx=(5, 0))
        else:
            # Pre-check non-protected processes
            var.set(True)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Button frames - separate for better layout
    select_frame = ttk.Frame(main_frame)
    select_frame.pack(fill=tk.X, pady=(10, 5))
    
    action_frame = ttk.Frame(main_frame)
    action_frame.pack(fill=tk.X, pady=(5, 0))
    
    # Select All/None buttons
    def select_all():
        for name, var in checkbox_vars.items():
            protected = ['launchd', 'kernel', 'system', 'windowserver', 'finder', 'dock']
            is_protected = any(p in name.lower() for p in protected)
            if not is_protected:
                var.set(True)
    
    def select_none():
        for var in checkbox_vars.values():
            var.set(False)
    
    ttk.Button(select_frame, text="Select All", command=select_all).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(select_frame, text="Select None", command=select_none).pack(side=tk.LEFT)
    
    # Result variable
    result = {"confirmed": False, "selected": []}
    
    def confirm_kill():
        selected = [name for name, var in checkbox_vars.items() if var.get()]
        result["confirmed"] = True
        result["selected"] = selected
        kill_dialog.destroy()
    
    def cancel_kill():
        result["confirmed"] = False
        result["selected"] = []
        kill_dialog.destroy()
    
    # Action buttons - more prominent
    cancel_btn = ttk.Button(action_frame, text="Cancel", command=cancel_kill)
    cancel_btn.pack(side=tk.RIGHT, padx=(5, 0))
    
    kill_btn = ttk.Button(action_frame, text="🔪 Kill Selected", command=confirm_kill)
    kill_btn.pack(side=tk.RIGHT, padx=(5, 0))
    
    # Make kill button more prominent
    kill_btn.configure(style="Accent.TButton")
    
    # Wait for dialog to close
    kill_dialog.wait_window()
    
    return result


def activate_siri():
    """Activate Siri using Spotlight search"""
    try:
        # Press Cmd+G to open Spotlight (or use Cmd+Space)
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "g" using command down'])
        
        # Wait a moment for Spotlight to open
        import time
        time.sleep(0.5)
        
        # Type "siri" and press Enter
        subprocess.run(["osascript", "-e", 'tell application "System Events" to keystroke "siri"'])
        time.sleep(0.3)
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 36'])  # Enter key
        
        return True
    except Exception as e:
        print(f"Error activating Siri: {e}")
        return False

def send_message(event=None):
    prompt = input_field.get()
    if not prompt.strip():
        return

    # Check if user wants to activate Siri
    if prompt.lower().strip() == "siri":
        input_field.delete(0, tk.END)
        chat_box.config(state=tk.NORMAL)
        chat_box.insert(tk.END, f"You: {prompt}\n", "user")
        chat_box.see(tk.END)
        
        if activate_siri():
            chat_box.insert(tk.END, "🎙️ Siri activated!\n", "gemini")
        else:
            chat_box.insert(tk.END, "❌ Failed to activate Siri\n", "gemini")
        
        chat_box.config(state=tk.DISABLED)
        chat_box.see(tk.END)
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

        # Parse the JSON response
        cleaned = response.replace("```json", "").replace("```", "").strip()
        parsed_response = json.loads(cleaned)
        kill_list = parsed_response.get("kill", [])
        open_list = parsed_response.get("open", [])
        reply_parts = []

        # 👉 Open apps
        if open_list:
            opened = open_apps(open_list)
            reply_parts.append(f"🚀 Opened: {', '.join(opened)}" if opened else "❌ No apps opened.")

        # 👉 Kill apps (only if there are apps to kill)
        if kill_list:
            kill_result = show_kill_dialog(kill_list)
            
            if kill_result["confirmed"] and kill_result["selected"]:
                killed = kill_by_names(kill_result["selected"])
                reply_parts.append(f"🔪 Killed: {', '.join(killed)}" if killed else "❌ No processes killed.")
            elif kill_result["confirmed"] and not kill_result["selected"]:
                reply_parts.append("ℹ️ No processes selected to kill.")
            else:
                reply_parts.append("🛑 Kill request cancelled.")

        reply = "\n".join(reply_parts) if reply_parts else "✅ No action taken."

    except Exception:
        # If JSON parsing fails, just show the raw response
        reply = response

    chat_box.insert(tk.END, f"Gemini: {reply}\n", "gemini")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)


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