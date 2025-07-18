# PROCESS-KILLER - Gemini Process Manager

This is a simple macOS task manager that uses Google's Gemini API to help you manage running processes. You can ask it to kill applications by name, and it will ask for your confirmation before proceeding.

## Features

- **List running processes:** The application fetches and displays the top 30 most memory-intensive processes.
- **Kill processes with natural language:** You can ask Gemini to kill one or more applications (e.g., "kill Chrome and Spotify").
- **Confirmation before killing:** To prevent accidental termination of important processes, the application will always ask for your confirmation.
- **General conversation:** You can also have a general conversation with the assistant.

## Requirements

- Python 3
- `tkinter` (usually included with Python)
- `psutil`
- `requests`
- `python-dotenv`

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/taskai.git
    cd taskai
    ```

2.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your API Key:**
    - Get your API key from Google AI Studio.
    - Create a file named `.env` in the project's root directory.
    - Add your API key to the `.env` file:
        ```
        API_KEY=your_google_api_key
        ```

## Usage

Run the application with the following command:

```bash
python main.py
