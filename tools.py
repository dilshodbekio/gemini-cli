from datetime import datetime


def get_current_datetime():
    """Bu funksiya ayni vaqt da soat nechchi ekanligini va sanani 
    'YYYY-MM-DD HH:MM' ko'rinishida qaytaradi"""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


TOOLS=[
    {"type": "function",
     "name": "get_current_datetime",
     "description": "Bu funksiya ayni vaqt da soat nechchi ekanligini va sanani 'YYYY-MM-DD HH:MM' ko'rinishida qaytaradi, foydalanuvchi hozirgi sana vaqt haqida so'raganda ishlat",
     "parameters": {
         "type": "object",
         "properties": {},
     },}
]

TOOLS_functions={
    "get_current_datetime": get_current_datetime
}