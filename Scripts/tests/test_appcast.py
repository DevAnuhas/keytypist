import base64
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIGNATURE = base64.b64encode(bytes(64)).decode()


LEGACY_FEED_SHA256 = "496abc5192e7750e076e8aa0352fc04ae20e9c9a2dc88966020194f309b7b764"


def feed(url=None, version="2.5.0", build="18"):
    url = url or f"https://github.com/DevAnuhas/keytypist/releases/download/v{version}/KeyTypist-{version}-arm64.dmg"
    body = f'''<?xml version="1.0"?><rss xmlns:sparkle="http://www.andymatuschak.org/xml-namespaces/sparkle" version="2.0"><channel><title>KeyTypist</title><item><title>KeyTypist {version}</title><sparkle:version>{build}</sparkle:version><sparkle:shortVersionString>{version}</sparkle:shortVersionString><sparkle:minimumSystemVersion>14.0</sparkle:minimumSystemVersion><enclosure url="{url}" length="12345" type="application/octet-stream" sparkle:edSignature="{SIGNATURE}" /></item></channel></rss>'''
    return body + f'''<!-- sparkle-signatures:
edSignature: {SIGNATURE}
length: {len(body.encode())}
-->'''


class AppcastTests(unittest.TestCase):
    def validate(self, data):
        with tempfile.TemporaryDirectory(prefix="keytypist-appcast-tests-") as d:
            path = Path(d) / "feed.xml"
            path.write_text(data)
            return subprocess.run([sys.executable, str(ROOT / "Scripts/appcast.py"), "--validate-feed", str(path)],
                                  capture_output=True, text=True)

    def test_stable_fork_release_passes_metadata_validation(self):
        result = self.validate(feed())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1 release", result.stdout)

    def test_upstream_or_mismatched_assets_are_rejected(self):
        for url in [
            "https://github.com/nilava/TabType/releases/download/v2.5.0/TabType.dmg",
            "https://github.com/DevAnuhas/keytypist/releases/download/v2.4.0/KeyTypist-2.4.0-arm64.dmg",
            "http://github.com/DevAnuhas/keytypist/releases/download/v2.5.0/KeyTypist-2.5.0-arm64.dmg",
            "https://github.com/DevAnuhas/keytypist/releases/download/v2.5.0/KeyTypist-2.5.0-arm64.dmg?redirect=1",
            # Former-name asset is only legitimate for the one release published under it.
            "https://github.com/DevAnuhas/keyweave/releases/download/v2.5.0/KeyWeave-2.5.0-arm64.dmg",
        ]:
            with self.subTest(url=url):
                result = self.validate(feed(url))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("matching KeyTypist release DMG", result.stderr)

    def test_keytypist_feed_never_lists_former_name_releases(self):
        for version, build in [("2.4.0", "17"), ("2.5.0", "18")]:
            url = f"https://github.com/DevAnuhas/keyweave/releases/download/v{version}/KeyWeave-{version}-arm64.dmg"
            with self.subTest(version=version):
                result = self.validate(feed(url, version=version, build=build))
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("matching KeyTypist release DMG", result.stderr)

    def test_keytypist_uses_its_own_feed_path(self):
        sys.path.insert(0, str(ROOT / "Scripts"))
        try:
            import appcast
        finally:
            sys.path.pop(0)
        self.assertEqual(appcast.FEED,
                         "https://raw.githubusercontent.com/DevAnuhas/keytypist/main/Updates/keytypist-appcast.xml")
        self.assertEqual(appcast.DEFAULT_OUTPUT, ROOT / "Updates/keytypist-appcast.xml")
        self.assertNotEqual(appcast.DEFAULT_OUTPUT, appcast.LEGACY_FEED)

    def test_legacy_keyweave_feed_is_frozen(self):
        # Installed KeyWeave 2.4.0 reads this EdDSA-signed file; any edit breaks its signature.
        digest = hashlib.sha256((ROOT / "Updates/appcast.xml").read_bytes()).hexdigest()
        self.assertEqual(digest, LEGACY_FEED_SHA256)

    def test_generation_refuses_to_write_the_frozen_legacy_feed(self):
        before = (ROOT / "Updates/appcast.xml").read_bytes()
        result = subprocess.run([sys.executable, str(ROOT / "Scripts/appcast.py"),
                                 "--app", "/nonexistent.app", "--output", str(ROOT / "Updates/appcast.xml")],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("frozen KeyWeave feed", result.stderr)
        self.assertEqual((ROOT / "Updates/appcast.xml").read_bytes(), before)

    def test_unsigned_truncated_or_modified_metadata_is_rejected(self):
        for data in [feed().split("<!-- sparkle-signatures:")[0],
                     feed().replace("length: ", "length: 9"),
                     feed() + "unsigned trailing bytes"]:
            with self.subTest(data=data[-80:]):
                self.assertNotEqual(self.validate(data).returncode, 0)

    def test_wrong_identity_leaves_previous_feed_untouched(self):
        import plistlib
        with tempfile.TemporaryDirectory(prefix="keytypist-appcast-tests-") as d:
            root = Path(d)
            app = root / "Other.app"
            (app / "Contents").mkdir(parents=True)
            (app / "Contents/Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "app.tabtype.TabType"}))
            output = root / "appcast.xml"
            output.write_bytes(b"previous feed sentinel")
            result = subprocess.run([sys.executable, str(ROOT / "Scripts/appcast.py"),
                                     "--app", str(app), "--output", str(output)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unexpected application identity", result.stderr)
            self.assertEqual(output.read_bytes(), b"previous feed sentinel")


if __name__ == "__main__":
    unittest.main()
