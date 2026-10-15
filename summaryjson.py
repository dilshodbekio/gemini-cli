from pydantic import BaseModel, Field

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