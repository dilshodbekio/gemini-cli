"""
test_stream_tools.py — streaming + function calling, to'liq sikl (agent loop).

Oqim:
  1. So'rovni stream qilamiz
  2. Matn kelsa — darhol chiqaramiz
     Function call kelsa — nomi, id va argumentlarini YIG'AMIZ
  3. Stream tugagach status'ga qaraymiz:
       completed       -> javob tayyor, tugadi
       requires_action -> funksiyalarni bajaramiz, natijani qaytaramiz,
                          va YANA stream qilamiz (2-qadamga qaytamiz)
"""

import json

from dotenv import load_dotenv
from google import genai

from tools import TOOLS, TOOLS_functions

load_dotenv()
client = genai.Client()

MODEL = "gemini-3.5-flash-lite"
MAX_ROUNDS = 5  # model cheksiz function chaqirib qolmasligi uchun


def stream_bir_raund(input_data, previous_id=None):
    """
    Bitta stream'ni o'qiydi.
    Qaytaradi: (interaction_id, status, function_calls)
    function_calls: [{"id":..., "name":..., "args_str":...}, ...]
    """
    kwargs = {
        "model": MODEL,
        "input": input_data,
        "tools": TOOLS,
        "stream": True,
    }
    if previous_id:
        kwargs["previous_interaction_id"] = previous_id

    interaction_id = None
    status = None
    # Bir javobda bir nechta function call bo'lishi mumkin,
    # shuning uchun ularni step index bo'yicha saqlaymiz
    calls = {}

    for event in client.interactions.create(**kwargs):
        et = event.event_type

        if et == "interaction.created":
            interaction_id = event.interaction.id

        elif et == "step.start":
            step = event.step
            if step.type == "function_call":
                calls[event.index] = {
                    "id": step.id,
                    "name": step.name,
                    "args_str": "",  # argument bo'laklari shu yerga qo'shiladi
                }

        elif et == "step.delta":
            d = event.delta
            if d.type == "text":
                print(d.text, end="", flush=True)
            elif d.type == "arguments_delta":
                calls[event.index]["args_str"] += d.arguments
            # boshqa delta turlari (thought_signature va h.k.) — e'tiborsiz

        elif et == "interaction.completed":
            status = event.interaction.status
            # ID'ni shu yerdan ham olsa bo'ladi
            interaction_id = interaction_id or event.interaction.id

        # notanish event'lar — jim o'tkazib yuboramiz

    return interaction_id, status, list(calls.values())


def funksiyani_bajar(call):
    """Bitta function call'ni bajaradi va function_result blokini qaytaradi."""
    name = call["name"]
    
    # Argumentlar: bo'sh bo'lsa {} — argumentsiz funksiya
    try:
        args = json.loads(call["args_str"]) if call["args_str"] else {}
    except json.JSONDecodeError:
        args = {}

    func = TOOLS_functions.get(name)
    if func is None:
        natija = f"Xato: '{name}' nomli funksiya topilmadi"
    else:
        try:
            natija = func(**args)
        except Exception as e:
            natija = f"Xato: {e}"

    print(f"\n  [tool] {name}({args}) -> {natija}")

    return {
        "type": "function_result",
        "name": name,
        "call_id": call["id"],
        "result": {"content": [{"type": "text", "text": str(natija)}]},
    }


def javob_ol(prompt, previous_id=None):
    """
    Foydalanuvchi xabariga to'liq javob oladi (kerak bo'lsa tool'larni ham bajaradi).
    Qaytaradi: OXIRGI interaction ID — keyingi xabarda xotira uchun shu kerak.
    """
    input_data = prompt

    for raund in range(MAX_ROUNDS):
        interaction_id, status, calls = stream_bir_raund(input_data, previous_id)
        previous_id = interaction_id  # zanjirni davom ettiramiz

        if status != "requires_action" or not calls:
            print()
            return previous_id

        # Model funksiya so'radi — hammasini bajarib, natijalarni qaytaramiz
        input_data = [funksiyani_bajar(c) for c in calls]

    print("\n[ogohlantirish] Maksimal raundlar soniga yetildi")
    return previous_id


if __name__ == "__main__":
    # Xotira ishlayotganini ko'rish uchun ikkita bog'liq savol
    oxirgi_id = None

    print("Siz: Hozir soat nechi?")
    print("Bot: ", end="")
    oxirgi_id = javob_ol("Hozir soat nechi?", oxirgi_id)

    print("\nSiz: Men hozir nima so'radim?")
    print("Bot: ", end="")
    oxirgi_id = javob_ol("Men hozir nima so'radim?", oxirgi_id)