"""Offline tests that don't require Home Assistant to be installed."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).resolve().parents[1] / "custom_components/qmotion_gen3_fm/position.py"
spec = importlib.util.spec_from_file_location("qmotion_position", PATH)
position = importlib.util.module_from_spec(spec)
spec.loader.exec_module(position)


class PositionTests(unittest.TestCase):
    def test_gateway_stored_command_to_ha(self):
        self.assertEqual(position.qsync_to_ha(0), 100)
        self.assertEqual(position.qsync_to_ha(40), 60)
        self.assertEqual(position.qsync_to_ha(100), 0)

    def test_unknown_gateway_values(self):
        self.assertIsNone(position.qsync_to_ha(250))
        self.assertIsNone(position.qsync_to_ha(255))

    def test_ha_outbound_position(self):
        self.assertEqual(position.ha_to_qsync(0), 100)
        self.assertEqual(position.ha_to_qsync(60), 40)
        self.assertEqual(position.ha_to_qsync(100), 0)
        with self.assertRaises(ValueError):
            position.ha_to_qsync(101)


if __name__ == "__main__":
    unittest.main()
