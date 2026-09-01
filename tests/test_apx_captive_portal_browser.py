from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BROWSER = ROOT / "scripts/physical-pilot/apx-captive-portal-browser-v1.py"


class CaptivePortalBrowserTests(unittest.TestCase):
    def test_browser_is_ephemeral_single_purpose_and_receives_no_url_argument(self):
        source = BROWSER.read_text()
        compile(source, str(BROWSER), "exec")
        for required in ("portal_from_stdin()", "WebsiteDataManager.new_ephemeral()",
                         "TemporaryDirectory", "set_enable_developer_extras(False)",
                         "set_enable_page_cache(False)", "download.cancel()",
                         'CHECK_CLIENT, "wifi-connectivity-check"', "LOCK_EX | fcntl.LOCK_NB"):
            self.assertIn(required, source)
        for forbidden in ("sys.argv[1]", "ssl._create_unverified_context", "ignore_tls_errors",
                          "shell=True", "NamedTemporaryFile"):
            self.assertNotIn(forbidden, source)

    def test_only_http_https_without_userinfo_are_admitted(self):
        namespace = {"__name__": "apx_browser_test"}
        exec(compile(BROWSER.read_text(), str(BROWSER), "exec"), namespace)
        validate = namespace["validated_url"]
        self.assertEqual(validate("https://portal.example/login?token=x"),
                         "https://portal.example/login?token=x")
        for value in ("file:///tmp/x", "data:text/html,x", "javascript:alert(1)",
                      "https://user:secret@portal.example/"):
            with self.assertRaises(ValueError):
                validate(value)


if __name__ == "__main__":
    unittest.main()
