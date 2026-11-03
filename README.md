e · MD
gemini-cli

A terminal chatbot built on the Gemini Interactions API. It keeps conversation memory, streams responses token by token, calls Python functions as tools, and can produce structured summaries of the conversation.

Built as a hands-on project to learn the Gemini API step by step: REPL loop → memory → system instruction → streaming → structured output → function calling.

Features
Interactive REPL: chat in the terminal, type quit to exit; empty input is ignored
Conversation memory: uses previous_interaction_id, so the server keeps the context and the full history is not resent on every turn
System instruction: the assistant replies in Uzbek by default (easy to change in main.py)
Streaming: responses are printed as they arrive, handling step.start, step.delta and step.stop events
Function calling: the model can request a tool, the program runs it and sends the result back; multi-round tool calls are supported, and a single stream loop handles both text and function calls
/summary command: returns a structured summary (Pydantic model) with the topic, key points and number of questions; it is not added to the conversation chain
Tech stack
Python
google-genai SDK (Interactions API: client.interactions.create)
Model: gemini-3.5-flash-lite
pydantic for structured output
python-dotenv for loading the API key
Project structure
gemini-cli/
├── main.py          # REPL loop, streaming, commands, tool-call loop
├── tools.py         # Tool functions + declarations
├── test_tools.py    # Standalone function-calling test
├── requirements.txt
├── .env             # GEMINI_API_KEY (not committed)
└── .gitignore

In tools.py:

get_current_datetime() returns the current date and time as YYYY-MM-DD HH:MM
TOOLS is the list of tool declarations sent to the model
TOOLS_functions is a name → function dict used to run the requested tool
Setup
Clone the repo:
bash
   git clone https://github.com/dilshodbekio/gemini-cli.git
   cd gemini-cli
Create and activate a virtual environment:
bash
   python -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS / Linux
   source .venv/bin/activate
Install dependencies:
bash
   pip install -r requirements.txt
Get an API key from Google AI Studio and create a .env file in the project root:
   GEMINI_API_KEY=your_api_key_here
Usage
bash
python main.py

Example session:

You: What time is it now?
Assistant: (calls get_current_datetime, then answers with the time)

You: /summary
(prints a structured summary of the conversation)

You: quit
Command	Description
/summary	Structured summary of the conversation so far
quit	Exit the program
How it works
The user's message is sent with client.interactions.create(..., stream=True).
The stream is read event by event. Text deltas are printed immediately; function call arguments arrive in chunks (arguments_delta), are accumulated, then parsed with json.loads.
If the model requested a function, the program runs it from TOOLS_functions and sends back a function_result that includes the matching call_id. This repeats until the model returns a plain text answer.
The interaction ID from interaction.completed is saved and passed as previous_interaction_id on the next turn, which is how memory works.
Adding your own tool
Write the function in tools.py.
Add its declaration to the TOOLS list.
Register it in the TOOLS_functions dict.
Roadmap
 Google Search grounding
 /clear, /save, /load commands
 Better error handling
 RAG over local documents (embeddings + vector search)
License

MIT (or choose your own)
