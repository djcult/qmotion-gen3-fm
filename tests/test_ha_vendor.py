"""HACS must bundle the project's own protocol code byte-for-byte."""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class VendorTests(unittest.TestCase):
    def test_vendor_matches_source(self):
        for name in ("gateway.py", "protocol.py"):
            self.assertEqual(
                (ROOT / "src" / "qmotion_gen3_fm" / name).read_bytes(),
                (ROOT / "custom_components" / "qmotion_gen3_fm" / "vendor" / name).read_bytes(),
            )

if __name__ == "__main__":
    unittest.main()
