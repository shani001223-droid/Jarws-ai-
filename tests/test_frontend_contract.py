"""Static regression checks for the HOSHI dashboard contract."""
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SERVICE_WORKER = (ROOT / "sw.js").read_text(encoding="utf-8")
MANIFEST = (ROOT / "manifest.json").read_text(encoding="utf-8")
ICON_PATH = ROOT / "assets" / "hoshi-app-icon.svg"
BRIDGE = (ROOT / "android/app/src/main/java/com/valtron/jarvis/JarvisBridge.kt").read_text(encoding="utf-8")
ACCESSIBILITY = (ROOT / "android/app/src/main/java/com/valtron/jarvis/JarvisAccessibilityService.kt").read_text(encoding="utf-8")
MAIN_ACTIVITY = (ROOT / "android/app/src/main/java/com/valtron/jarvis/MainActivity.kt").read_text(encoding="utf-8")
SPRITE_PATH = ROOT / "assets" / "hoshi-expressions.webp"


class IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []

    def handle_starttag(self, tag, attrs):
        self.ids.extend(value for key, value in attrs if key == "id" and value)


class FrontendContractTests(unittest.TestCase):
    def test_html_ids_are_unique_and_script_references_exist(self):
        parser = IdCollector()
        parser.feed(HTML)
        self.assertEqual(len(parser.ids), len(set(parser.ids)), "Duplicate HTML id found")
        known_ids = set(parser.ids)
        scripts = re.findall(r"<script>([\s\S]*?)</script>", HTML, re.IGNORECASE)
        self.assertTrue(scripts, "Dashboard inline script is missing")
        refs = set(re.findall(r"\$\(['\"]([^'\"]+)['\"]\)", scripts[0]))
        self.assertTrue(refs, "Dashboard ID references were not detected")
        self.assertEqual(refs - known_ids, set(), "Script references missing HTML IDs")

    def test_character_expression_sprite_is_a_valid_webp_asset(self):
        self.assertTrue(SPRITE_PATH.is_file(), "HOSHI expression sprite is missing")
        image = SPRITE_PATH.read_bytes()
        self.assertGreater(len(image), 5000, "Expression sprite is unexpectedly small")
        self.assertEqual(image[:4], b"RIFF", "Sprite is not a RIFF image")
        self.assertEqual(image[8:12], b"WEBP", "Sprite is not a WebP image")
        self.assertIn("./assets/hoshi-expressions.webp", SERVICE_WORKER)
        self.assertIn("./memory-privacy.js", SERVICE_WORKER)
        self.assertIn('<script src="./memory-privacy.js"></script>', HTML)
        self.assertIn('CACHE_NAME = "hoshi-shell-v21"', SERVICE_WORKER)
        self.assertIn("./assets/hoshi-hero-background.svg", SERVICE_WORKER)

    def test_hoshi_app_icon_is_wired_for_favicon_pwa_and_offline_shell(self):
        self.assertTrue(ICON_PATH.is_file(), "HOSHI installable app icon is missing")
        icon = ICON_PATH.read_text(encoding="utf-8")
        self.assertIn("<svg", icon)
        self.assertIn('href="./assets/hoshi-app-icon.svg"', HTML)
        self.assertIn('./assets/hoshi-app-icon.svg', MANIFEST)
        self.assertIn('"sizes": "any"', MANIFEST)
        self.assertIn('"type": "image/svg+xml"', MANIFEST)
        self.assertIn('"purpose": "any"', MANIFEST)
        self.assertNotIn('"purpose": "any maskable"', MANIFEST)
        self.assertIn('width="512" height="512"', icon)
        self.assertIn("./assets/hoshi-app-icon.svg", SERVICE_WORKER)

    def test_final_dashboard_hero_art_and_speaking_indicator_are_wired(self):
        hero_asset = ROOT / "assets" / "hoshi-hero-background.svg"
        self.assertTrue(hero_asset.is_file(), "Final-art hero background asset is missing")
        hero_svg = hero_asset.read_text(encoding="utf-8")
        self.assertIn('data:image/webp;base64,', hero_svg)
        self.assertIn('url("./assets/hoshi-hero-background.svg")', HTML)
        self.assertIn('<span class="speech-wave" aria-hidden="true">', HTML)
        self.assertIn(".orb.speaking .speech-wave{opacity:1}", HTML)
        self.assertIn(".orb.speaking .companion-avatar::after", HTML)
        self.assertIn("@keyframes hoshi-mouth-lite", HTML)
        self.assertIn(".orb.speaking .companion-avatar::after{animation:none!important}", HTML)
        self.assertIn("@media(prefers-reduced-motion:reduce)", HTML)

    def test_each_ui_emotion_selects_a_character_expression(self):
        emotions = (
            "happy", "sad", "affectionate", "excited", "shy",
            "concerned", "annoyed", "playful", "thinking", "caring",
        )
        for emotion in emotions:
            selector = rf'\.orb\[data-emotion="{emotion}"\] \.companion-avatar\{{background-position:'
            self.assertRegex(HTML, selector, f"No sprite position for {emotion}")

    def test_new_cloud_request_supersedes_stale_reply(self):
        self.assertIn("let cloudOnline=false, cloudRequestSequence=0, activeCloudController=null;", HTML)
        self.assertIn("if(activeCloudController){try{activeCloudController.abort()}", HTML)
        self.assertIn("if(requestId!==cloudRequestSequence)return;", HTML)
        self.assertIn("if(requestId===cloudRequestSequence)", HTML)

    def test_hoshi_voice_uses_native_engine_without_country_picker(self):
        self.assertNotIn('id="voiceSelect"', HTML)
        self.assertIn("One Hoshi delivery", HTML)

    def test_urdu_speech_never_substitutes_hindi_or_english(self):
        self.assertIn("locale:commandLanguage", HTML)
        self.assertIn("data.speech_text", HTML)
        self.assertIn("playOnlineUrdu(currentSpeech)", HTML)
        self.assertIn("supportsUrduSpeech", HTML)
        self.assertIn('"ur" -> listOf(Locale("ur", "PK"))', MAIN_ACTIVITY)
        self.assertNotIn('engine.setLanguage(Locale.getDefault())', MAIN_ACTIVITY)

    def test_voice_errors_stop_restart_loop_and_keep_actionable_status(self):
        self.assertIn('lastVoiceError=""', HTML)
        for error in ("not-allowed", "audio-capture", "language-not-supported", "network"):
            self.assertIn("'" + error + "'", HTML)
        self.assertIn("instance.continuous=false", HTML)
        self.assertIn("if(sessionEnded||submitted)return", HTML)
        self.assertNotIn("recognition.continuous=true", HTML)
        self.assertIn("MIC STOPPED · TAP TO SPEAK AGAIN", HTML)
        self.assertIn("startNativeListening(commandLanguage)", HTML)
        self.assertIn("SpeechRecognizer.createSpeechRecognizer(this)", MAIN_ACTIVITY)
        self.assertIn("mediaPlaybackRequiresUserGesture = false", MAIN_ACTIVITY)

    def test_phone_and_writing_actions_restored_without_cloud(self):
        for label in ('id="hoshiDraft"', 'id="copyHoshiDraft"', 'id="shareHoshiDraft"',
                      'data-hoshi-command="phone back"', 'data-hoshi-command="phone home"',
                      'data-hoshi-command="open WhatsApp"'):
            self.assertIn(label, HTML)
        for command in ('handlePhoneOrWritingCommand(text)', 'bridge.performAction(action[1])',
                        'bridge.openKnownApp(kind)', 'saveHoshiDraft(write[1])',
                        'window.JarvisBridge.copyUserText', 'window.JarvisBridge.shareUserDraft'):
            self.assertIn(command, HTML)
        self.assertIn("fun openKnownApp(action: String): Boolean", BRIDGE)
        self.assertIn("fun copyUserText(text: String): Boolean", BRIDGE)
        self.assertIn("fun shareUserDraft(text: String): Boolean", BRIDGE)
        self.assertIn("Intent.createChooser(share", MAIN_ACTIVITY)

    def test_spoken_requests_use_fast_ai_mode_but_writing_actions_are_local(self):
        self.assertIn("askCloud(text,source==='voice')", HTML)
        self.assertIn("processCommand(command,'voice')", HTML)
        self.assertIn("AI REPLIED IN ", HTML)
        self.assertIn("fast})", HTML)

    def test_latency_is_measured_by_stage_and_not_faked(self):
        self.assertIn('id="voiceTiming"', HTML)
        self.assertIn("performance.now()", HTML)
        self.assertIn("markVoiceHeard()", HTML)
        self.assertIn("voiceTimes.ai=", HTML)
        self.assertIn("voiceTimes.audio=", HTML)
        self.assertIn("HOSHI SPEAKING · URDU", HTML)
        self.assertIn("Mic '+val(voiceTimes.listen)", HTML)
        self.assertIn("startVoiceTimer()", HTML)

    def test_android_screenshot_is_explicit_and_api_gated(self):
        self.assertIn('id="screenshotQuickBtn"', HTML)
        self.assertIn('data-screen-action="screenshot"', HTML)
        self.assertIn("does not inspect screen text or upload screenshots", HTML)
        self.assertIn('"screenshot"', BRIDGE)
        self.assertIn("Build.VERSION.SDK_INT < Build.VERSION_CODES.P", BRIDGE)
        self.assertIn("GLOBAL_ACTION_TAKE_SCREENSHOT", ACCESSIBILITY)
        self.assertIn("Build.VERSION.SDK_INT >= Build.VERSION_CODES.P", ACCESSIBILITY)

    def test_voice_speaking_state_and_network_timeouts_are_wired(self):
        self.assertIn("window.hoshiSetSpeaking=setSpeaking", HTML)
        self.assertIn("u.onstart=()=>{if(speechId===speechSequence)setSpeaking(true)}", HTML)
        self.assertIn("u.onerror=e=>", HTML)
        self.assertIn("AbortController", HTML)
        self.assertIn("32000", HTML)
        self.assertIn("7000", HTML)
        self.assertIn("setOnUtteranceProgressListener", MAIN_ACTIVITY)
        self.assertIn("window.hoshiSetSpeaking", MAIN_ACTIVITY)
        self.assertIn("window.hoshiVoiceError", MAIN_ACTIVITY)
        self.assertIn('it.locale.language == "ur" && it.locale.country == "PK"', MAIN_ACTIVITY)
        self.assertIn("Pakistani Urdu (ur-PK)", HTML)

    def test_memory_controls_and_local_preferences_are_present(self):
        for element_id in ("chatHistory", "memoryToggle", "clearMemoryBtn", "stopSpeakingBtn",
                           "languageToggle", "speakToggle", "wakeToggle"):
            self.assertIn(f'id="{element_id}"', HTML)
        for feature in ("Delete saved ", "Edit saved ", "hoshiLanguage",
                        "hoshiVoiceReplies", "hoshiWakeWord"):
            self.assertIn(feature, HTML)


if __name__ == "__main__":
    unittest.main()

