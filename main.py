import json

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, Field

from tools import TOOLS, TOOLS_functions

load_dotenv()
MODEL_ID = "gemini-3.5-flash-lite"
SYSTEM_INSTRUCTION = "Sen o'zbek tilida javob beradigan, qisqa va aniq gapiradigan yordamchisan"
SUMMARY_PROMPT = "Shu paytgacha bo'lgan suhbatimizni tahlil qilib, xulosa tuz. Bu xulosa so'rovining o'zini suhbatning bir qismi deb hisoblama."

client = genai.Client()
last_interaction_id = None


class Summary(BaseModel):
    mavzu: str = Field(description="Suhbatning umumiy mavzusi, 2-6 so'zdan iborat qisqa sarlavha "
                    "ko'rinishida, o'zbek tilida. To'liq gap emas. "
                    "Masalan: 'Python'da virtual environment yaratish'.")

    asosiy_fikrlar: list[str] = Field(description="Suhbatda muhokama qilingan eng muhim fikrlar, 3-5 ta, "
                    "har biri bitta qisqa gap, o'zbek tilida. Foydalanuvchi "
                    "so'ragan va javobda aytilgan asosiy ma'lumotlarni qamrab olsin. "
                    "Suhbat juda qisqa bo'lsa, kamroq bo'lishi mumkin.")

    savollar_soni: int = Field(description="Foydalanuvchi suhbat davomida bergan savollar soni. "
                    "Faqat foydalanuvchi xabarlarini sana, yordamchining "
                    "savollarini hisobga olma. Savol bo'lmasa 0 qaytar.")


def stream_turn(input_data, previous_id):
    """Bitta so'rovni stream qiladi.

    Matnni kelishi bilan chop etadi, function call'larni yig'adi.
    Qaytaradi: (interaction_id, calls) — calls: {index: {"id", "name", "args"}}
    """
    stream = client.interactions.create(
        model=MODEL_ID,
        input=input_data,
        previous_interaction_id=previous_id,
        system_instruction=SYSTEM_INSTRUCTION,
        tools=TOOLS,
        stream=True,
    )

    interaction_id = None
    calls = {}  # har turda yangidan — eski call'lar qayta ishlamaydi

    for event in stream:
        if event.event_type == "interaction.created":
            interaction_id = event.interaction.id

        elif event.event_type == "step.start":
            step = event.step
            if step.type == "function_call":
                # Shu step uchun yozuv ochamiz, argumentlar delta bo'lib keladi
                calls[event.index] = {"id": step.id, "name": step.name, "args": ""}

        elif event.event_type == "step.delta":
            if event.delta.type == "text":
                print(event.delta.text, end="", flush=True)
            elif event.delta.type == "arguments_delta":
                calls[event.index]["args"] += event.delta.arguments

        elif event.event_type == "interaction.completed":
            interaction_id = event.interaction.id

    return interaction_id, calls


def run_function(call):
    """Bitta function call'ni bajarib, function_result qaytaradi."""
    name = call["name"]
    funksiya = TOOLS_functions.get(name)

    if funksiya is None:
        raw_result = f"Xato: '{name}' degan funksiya yo'q"
    else:
        try:
            args = json.loads(call["args"]) if call["args"] else {}
            raw_result = funksiya(**args)
        except Exception as e:
            raw_result = f"Xato: {e}"

    if not isinstance(raw_result, str):
        raw_result = json.dumps(raw_result, ensure_ascii=False)

    return {
        "type": "function_result",
        "name": name,
        "call_id": call["id"],
        "result": [{"type": "text", "text": raw_result}],
    }


while True:
    prompt = input("Sen: ").strip()
    if prompt.lower() == "quit":
        break
    elif not prompt:
        continue
    elif prompt.lower() == "/summary":
        if last_interaction_id is None:
            print("Hali suhbat yo'q")
            continue
        interaction = client.interactions.create(
            model=MODEL_ID,
            input=SUMMARY_PROMPT,
            previous_interaction_id=last_interaction_id,
            system_instruction=SYSTEM_INSTRUCTION,
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": Summary.model_json_schema(),
            },
        )
        summary = Summary.model_validate_json(interaction.output_text)
        print(summary)
        continue  # last_interaction_id yangilanmaydi — summary zanjirga qo'shilmaydi

    print("AI: ", end="", flush=True)
    last_interaction_id, calls = stream_turn(prompt, last_interaction_id)

    # Model funksiya so'rasa — natijani qaytaramiz. Javobda yana call bo'lishi
    # mumkin, shuning uchun call qolmaguncha davom etamiz.
    while calls:
        results = [run_function(call) for call in calls.values()]
        last_interaction_id, calls = stream_turn(results, last_interaction_id)

    print()
