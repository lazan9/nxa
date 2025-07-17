# nxa

Simple command line email reply assistant using OpenAI. Paste an email or pass a text file and the tool will summarise the message, propose short replies and generate a full answer.

## Usage

1. Install the required packages (optional if you only want to see dummy responses):
   ```bash
   pip install -r requirements.txt
   ```
   Set your OpenAI API key in the `OPENAI_API_KEY` environment variable if you want real completions.

2. Run the assistant:
   ```bash
   python -m nxa_app.cli path/to/email.txt
   ```
   If no path is given, the script will ask for the email content via standard input.
