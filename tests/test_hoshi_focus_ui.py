"""Contract for a minimal, CSS-animated default home with preserved tools."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FocusUITests(unittest.TestCase):
    def test_focus_is_default_and_can_be_switched_off(self):
        html = (ROOT / "index.html").read_text("utf-8")
        css = (ROOT / "hoshi-focus.css").read_text("utf-8")
        self.assertIn('class="nightroom focus-mode"', html)
        self.assertIn('id="focusModeToggle"', html)
        self.assertIn("localStorage.getItem('hoshiFocusModeV1')!=='false'", html)
        self.assertIn("localStorage.setItem('hoshiFocusModeV1',String(focusMode))", html)
        self.assertIn("background-image:radial-gradient", css)
        self.assertIn("background-image:radial-gradient", css)
        self.assertIn("!important", css)
        self.assertIn("@media(prefers-reduced-motion:reduce)", css)

    def test_core_and_interrupt_have_real_handlers(self):
        html = (ROOT / "index.html").read_text("utf-8")
        self.assertIn('id="hoshiEnergy" class="core focus-core"', html)
        self.assertEqual(html.count('id="hoshiEnergy"'), 1)
        self.assertIn('<script type="module" src="./hoshi-core-ui.mjs"></script>', html)
        self.assertIn('id="focusStop"', html)
        self.assertIn("$('focusStop').onclick=()=>interruptHoshi()", html)
        self.assertIn("shell.classList.add('responding')", html)
        self.assertIn("shell.classList.remove('responding')", html)
        self.assertIn('data-tab="settings"', html)
        self.assertIn("showTab('trading')", html)
        self.assertIn('<link rel="stylesheet" href="./hoshi-focus.css">', html)

    def test_service_worker_precaches_focus_style(self):
        sw = (ROOT / "sw.js").read_text("utf-8")
        self.assertIn("./hoshi-focus.css", sw)


if __name__ == "__main__":
    unittest.main()
