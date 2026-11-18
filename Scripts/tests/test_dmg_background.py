"""The installer background is a rendered PNG, so a rename in the generator script does not
change it until someone re-runs the script. The script embeds the strings it draws as the PNG's
XMP description; these tests fail when the committed images are stale."""
import re
import struct
import unittest
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "Scripts/make-dmg-background.swift"
IMAGES = [ROOT / "packaging/dmg/background.png", ROOT / "packaging/dmg/background@2x.png"]
FORMER_NAME = "keyweave"
DC = "{http://purl.org/dc/elements/1.1/}"
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"


def xmp_description(path):
    """The dc:description from the PNG's XMP packet (an iTXt chunk), or None."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", f"{path} is not a PNG"
    offset = 8
    while offset < len(data):
        length, kind = struct.unpack(">I4s", data[offset:offset + 8])
        body = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind != b"iTXt":
            continue
        keyword, _, rest = body.partition(b"\0")
        if keyword != b"XML:com.adobe.xmp":
            continue
        compressed = rest[0]
        _language, _, rest = rest[2:].partition(b"\0")
        _translated, _, text = rest.partition(b"\0")
        packet = zlib.decompress(text) if compressed else text
        item = ET.fromstring(packet).find(f".//{DC}description/{RDF}Alt/{RDF}li")
        return item.text if item is not None else None
    return None


def drawn_strings():
    """The script's `title` and `instruction` constants, which it both draws and embeds."""
    source = SCRIPT.read_text(encoding="utf-8")
    return [re.search(rf'^let {name} = "([^"]+)"', source, re.MULTILINE).group(1) for name in ("title", "instruction")]


class DmgBackgroundTests(unittest.TestCase):
    def test_script_draws_the_constants_it_embeds(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertTrue(all(drawn_strings()))
        self.assertIn("text(title,", source)
        self.assertIn("text(instruction,", source)

    def test_committed_backgrounds_match_the_strings_the_script_draws(self):
        expected = " | ".join(drawn_strings())
        for image in IMAGES:
            with self.subTest(image=image.name):
                self.assertEqual(xmp_description(image), expected,
                                 "Stale background: run `swift Scripts/make-dmg-background.swift packaging/dmg`")

    def test_backgrounds_never_carry_the_former_product_name(self):
        for image in IMAGES:
            with self.subTest(image=image.name):
                self.assertNotIn(FORMER_NAME, (xmp_description(image) or "").lower())


if __name__ == "__main__":
    unittest.main()
