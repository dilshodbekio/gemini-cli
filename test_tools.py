from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Get the current weather in a given location",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city and state, e.g. San Francisco, CA"
            }
        },
        "required": ["location"]
    }
}

# Turn 1: Request function call
stream = client.interactions.create(
    model="gemini-3.8-flash",
    tools=[weather_tool],
    input="What is the weather in Paris right now?",
    stream=True,
)

first_interaction_id = None
func_call_id = None
func_call_name = None
func_args_accumulated = ""

for event in stream:
    if event.event_type == "interaction.created":
        first_interaction_id = event.interaction.id
    elif event.event_type == "step.start":
        step = event.step
        if step.type == "function_call":
            func_call_id = step.id
            func_call_name = step.name
    elif event.event_type == "step.delta":
        if event.delta.type == "arguments_delta":
            func_args_accumulated += event.delta.arguments

# Turn 2: Execute tool and send the result back to resume stream
if func_call_id:
    # Execute weather_tool using accumulated arguments
    dummy_result = {
        "content": [{"type": "text", "text": '{"weather": "Sunny and 22°C"}'}]
    }

    stream2 = client.interactions.create(
        model="gemini-3.8-flash",
        previous_interaction_id=first_interaction_id,
        input=[{
            "type": "function_result",
            "name": func_call_name,
            "call_id": func_call_id,
            "result": dummy_result
        }],
        stream=True,
    )

    for event in stream2:
        if event.event_type == "step.delta":
            if event.delta.type == "text":
                print(event.delta.text, end="", flush=True)