"""Local, bounded pronunciation substitutions for Urdu TTS.

This is *not* a translation service, voice clone, gender classifier, or
guaranteed accent improvement. It replaces only well-known Latin tokens
inside already Urdu-script speech_text without changing the displayed reply.
"""
import re

_PRONUNCIATIONS = {
    "BTCUSDT": "بی ٹی سی یو ایس ڈی ٹی",
    "ETHUSDT": "ای ٹی ایچ یو ایس ڈی ٹی",
    "USDT": "یو ایس ڈی ٹی",
    "BTC": "بی ٹی سی",
    "ETH": "ای ٹی ایچ",
    "AI": "اے آئی",
    "API": "اے پی آئی",
    "APK": "اے پی کے",
    "SL": "ایس ایل",
    "TP": "ٹی پی",
    "HOSHI": "ہوشی",
    "JARVIS": "جاروس",
    "YOUTUBE": "یوٹیوب",
    "WHATSAPP": "واٹس ایپ",
    "TRADINGVIEW": "ٹریڈنگ ویو",
}
_WORDS = re.compile(
    r"(?<![A-Za-z])(?:" +
    "|".join(re.escape(word) for word in sorted(_PRONUNCIATIONS, key=len, reverse=True)) +
    r")(?![A-Za-z])",
    re.IGNORECASE,
)


def normalize_urdu_speech(text: str) -> str:
    """TTS-only pronunciation hints; never mutate chat replies or user input."""
    value = str(text or "")
    if not re.search(r"[\u0600-\u06ff]", value):
        return value
    return _WORDS.sub(lambda m: _PRONUNCIATIONS[m.group(0).upper()], value)
