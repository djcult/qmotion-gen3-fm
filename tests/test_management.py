import unittest
from qmotion_gen3_fm.management import (
    create_group_packet, delete_group_packet, next_channel, parse_mac, ERASE_PACKET
)

class ManagementTests(unittest.TestCase):
    def test_create_matches_app_layout(self):
        packet = create_group_packet("test", parse_mac("00:04:a3:00:00:7a"), 10, now=1)
        self.assertEqual(len(packet), 63)
        self.assertEqual(packet[:3], bytes.fromhex("37 3d 01"))
        raw = packet[3:]
        self.assertEqual(raw[0], 3)
        self.assertEqual(raw[8], 10)
        self.assertEqual(raw[9:15], bytes.fromhex("00 04 a3 00 00 7a"))
        self.assertEqual(raw[15:19], bytes.fromhex("00 00 00 01"))
        self.assertEqual(raw[21], 1)
        self.assertEqual(raw[24:32], bytes.fromhex("19 7f 32 7f 4b 7f 00 7f"))
        self.assertEqual(raw[32:36], b"test")
        self.assertEqual(raw[22:24], b"\0\0")

    def test_delete_and_erase(self):
        self.assertEqual(delete_group_packet(bytes.fromhex("00 02")), bytes.fromhex("32 02 02 00"))
        self.assertEqual(ERASE_PACKET, bytes.fromhex("02 00"))

    def test_channel_allocation(self):
        self.assertEqual(next_channel({9}), 10)
        self.assertEqual(next_channel(set(range(9,16))), 17)

    def test_validation(self):
        for name in ("", "a" * 17):
            with self.assertRaises(ValueError):
                create_group_packet(name, bytes(6), 10)
        with self.assertRaises(ValueError):
            delete_group_packet(b"\0\0")
