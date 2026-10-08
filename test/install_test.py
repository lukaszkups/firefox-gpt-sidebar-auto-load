import configparser
import tempfile
import unittest
import zipfile
from pathlib import Path

import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("install", ROOT / "scripts" / "install.py")
install = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(install)


class InstallTests(unittest.TestCase):
    def test_parse_profiles_prefers_install_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp)
            release = config / "abc.default-release"
            other = config / "abc.default"
            release.mkdir()
            other.mkdir()
            (config / "profiles.ini").write_text(
                "\n".join(
                    [
                        "[Profile0]",
                        "Name=default",
                        "IsRelative=1",
                        "Path=abc.default",
                        "[Profile1]",
                        "Name=default-release",
                        "IsRelative=1",
                        "Path=abc.default-release",
                        "[Install1234]",
                        "Default=abc.default-release",
                        "Locked=1",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            self.assertEqual(install.parse_profiles(config), [release.resolve()])

    def test_user_js_block_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            (profile / "user.js").write_text('user_pref("browser.startup.page", 3);\n', encoding="utf-8")
            install.upsert_user_js(profile)
            install.upsert_user_js(profile)
            text = (profile / "user.js").read_text(encoding="utf-8")
            self.assertEqual(text.count(install.USERJS_BEGIN), 1)
            self.assertIn('user_pref("browser.startup.page", 3);', text)
            self.assertIn('user_pref("xpinstall.signatures.required", false);', text)
            install.remove_user_js_block(profile)
            leftover = (profile / "user.js").read_text(encoding="utf-8")
            self.assertNotIn(install.USERJS_BEGIN, leftover)
            self.assertIn("browser.startup.page", leftover)

    def test_xpi_has_manifest_at_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "addon.xpi"
            install.build_xpi(ROOT, destination)
            with zipfile.ZipFile(destination) as archive:
                names = set(archive.namelist())
            self.assertIn("manifest.json", names)
            self.assertIn("lib/chat-url.js", names)
            self.assertIn("icons/robot-32.png", names)
            self.assertNotIn("README.md", names)
            self.assertNotIn("scripts/install.py", names)

    def test_channel_parser(self):
        self.assertEqual(
            install.parse_channel('pref("app.update.channel", "release");'),
            "release",
        )
        self.assertEqual(
            install.parse_channel('pref("app.update.channel", "aurora");'),
            "aurora",
        )
        self.assertIsNone(install.parse_channel("no channel here"))

    def test_absolute_profile_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "config"
            config.mkdir()
            profile = Path(tmp) / "elsewhere"
            profile.mkdir()
            (config / "profiles.ini").write_text(
                "\n".join(
                    [
                        "[Profile0]",
                        "Name=custom",
                        "IsRelative=0",
                        "Path=" + str(profile),
                        "Default=1",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            self.assertEqual(install.parse_profiles(config), [profile.resolve()])
            parser = configparser.RawConfigParser()
            parser.read(config / "profiles.ini", encoding="utf-8")
            self.assertEqual(parser.get("Profile0", "Name"), "custom")


if __name__ == "__main__":
    unittest.main()
