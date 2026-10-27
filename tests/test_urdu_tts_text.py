"""Urdu voice quality regression tests with mocked TTS network."""
import asyncio
import unittest
from unittest.mock import patch, AsyncMock

from cloud_backend.urdu_tts_text import normalize_urdu_speech
from cloud_backend import main


class FakeEdgeAudio:
    def __init__(self,*args,**kwargs):
        self.args=args
        self.kwargs=kwargs
    async def stream(self):
        yield {"type":"audio","data":b"ID3sample"}


class UrduPronunciationTests(unittest.TestCase):
    def setUp(self):
        main.speech_cache.clear()

    def test_common_technical_names_are_spoken_in_urdu(self):
        spoken=normalize_urdu_speech("ہوشی BTC اور USDT پر AI API سمجھاؤ۔")
        self.assertIn("بی ٹی سی",spoken)
        self.assertIn("یو ایس ڈی ٹی",spoken)
        self.assertIn("اے آئی",spoken)
        self.assertIn("اے پی آئی",spoken)

    def test_no_english_only_translation_or_arbitrary_word_mutation(self):
        self.assertEqual(normalize_urdu_speech("Plain English BTC API"),"Plain English BTC API")
        self.assertEqual(normalize_urdu_speech("میں نے youtube پر دیکھا۔"),
                         "میں نے یوٹیوب پر دیکھا۔")
        self.assertEqual(normalize_urdu_speech("مجھے BATCH نام کا لفظ بتاؤ"),
                         "مجھے BATCH نام کا لفظ بتاؤ")
        self.assertIn("جاروس",normalize_urdu_speech("میں JARVIS بنانا چاہتا ہوں"))

    def test_urdu_speech_endpoint_normalizes_only_after_script_validation(self):
        with patch("cloud_backend.main.synthesize_urdu",new=AsyncMock(return_value=b"ID3audio")) as mocked:
            response=asyncio.run(main.speech(main.SpeechRequest(text="BTC کے بارے میں بتاؤ۔",style="soft")))
        self.assertEqual(response.body,b"ID3audio")
        mocked.assert_awaited_once_with("بی ٹی سی کے بارے میں بتاؤ۔","soft")

    def test_neural_voice_uses_calm_female_urdu_locale_and_moderate_pitch(self):
        with patch("edge_tts.Communicate",side_effect=lambda *a,**kw: FakeEdgeAudio(*a,**kw)) as mocked:
            audio=asyncio.run(main.synthesize_urdu("مجھے سنو۔","soft"))
        self.assertEqual(audio,b"ID3sample")
        args=mocked.call_args
        self.assertEqual(args.args[1],"ur-PK-UzmaNeural")
        self.assertEqual(args.kwargs["pitch"],"+2Hz")
        self.assertEqual(args.kwargs["rate"],"-2%")

    def test_soft_and_playful_styles_do_not_require_paid_voice_model(self):
        with patch("edge_tts.Communicate",side_effect=lambda *a,**kw: FakeEdgeAudio(*a,**kw)) as mocked:
            asyncio.run(main.synthesize_urdu("خوش ہوشی۔","playful"))
        self.assertEqual(mocked.call_args.kwargs["pitch"],"+7Hz")


if __name__=="__main__":
    unittest.main()
