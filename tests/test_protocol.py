import unittest
from qmotion_gen3_fm.protocol import (
    SYNC, decode_frames, move, prepare_pairing, complete_pairing, ProtocolError
)
from qmotion_gen3_fm.gateway import Group

class ProtocolTests(unittest.TestCase):
    def test_packets_observed_on_working_gateway(self):
        self.assertEqual(SYNC.hex(" "), "16 00")
        self.assertEqual(move(9, 100).hex(" "), "38 02 09 64")
        self.assertEqual(move(9, 0).hex(" "), "38 02 09 00")
        self.assertEqual(prepare_pairing(9).hex(" "), "38 02 09 fa")
        self.assertEqual(complete_pairing(9, bytes.fromhex("00 02")).hex(" "),
                         "34 03 02 00 09")

    def test_sync_empty(self):
        raw = bytes.fromhex("16 06 00 00 00 00 00 00")
        frames = decode_frames(raw)
        self.assertEqual(frames[0].payload[-1], 0)

    def test_group_record(self):
        record = bytearray(60)
        record[8] = 9
        record[22:24] = bytes.fromhex("00 02")
        record[32:45] = b"homeassistant"
        group = Group.from_record(bytes(record))
        self.assertEqual((group.name, group.channel, group.page),
                         ("homeassistant", 9, bytes.fromhex("00 02")))

    def test_invalid_packet(self):
        with self.assertRaises(ProtocolError):
            decode_frames(bytes.fromhex("16 3c 00"))
        with self.assertRaises(ValueError):
            move(9, 250)

if __name__ == "__main__":
    unittest.main()
