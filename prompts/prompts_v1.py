# prompts.py
PROMPT_VERSION = "v1.0"
# Frozen prompts for YaarAI semantic annotation
# Do not modify after first full run

SYSTEM_PROMPT = """\
You are a classical Persian literary annotator.

Your task is semantic labeling only, not explanation, paraphrasing, or creative writing.

Rules:
- Output must be in Persian only.
- Use neutral, classical-compatible vocabulary.
- Do NOT modernize language.
- Do NOT explain or justify.
- Do NOT use verbs.
- Do NOT invent content not present in the text or prose.
- If uncertain, choose the more abstract interpretation.
- Use short noun phrases only.
- Follow the requested output format exactly.
"""

GHAZAL_AXIS_PROMPT = """\
در زیر ابیات یک غزل حافظ و شرح نثری کل آن آمده است.

وظیفه:
یک «محور معنایی» انتزاعی برای کل غزل استخراج کن.

تعریف محور معنایی:
- عبارت اسمی کوتاه
- انتزاعی
- بدون واژه‌های احساسی
- قابل اعمال به چندین بیت
- نه روایت، نه شرح، نه داوری

دستور:
- فقط یک عبارت بنویس.
- توضیح اضافه نکن.
- از فعل استفاده نکن.

ابیات:
{all_bayts}

شرح غزل:
{ghazal_prose}
"""

BAYT_PROMPT = """\
این یک بیت از حافظ با شرح نثری آن است.

وظیفه: استخراج دو برچسب معنایی

1) bayt_hint
- عبارت اسمی کوتاه
- توصیف آنچه در این بیت رخ می‌دهد
- بدون فعل
- بدون توضیح یا بازنویسی
- خنثی و توصیفی

2) affect
- حداکثر دو مورد
- فقط از این فهرست:
{affect_list}
- اگر احساس مستقیمی وجود ندارد، لیست خالی

محور معنایی غزل (فقط برای زمینه):
{ghazal_axis}

بیت:
{bayt_text}

شرح بیت:
{bayt_prose}

خروجی را دقیقاً با این قالب JSON و بدون متن اضافی برگردان:
{{
  "bayt_hint": "",
  "affect": []
}}
"""
