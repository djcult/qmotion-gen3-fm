import unittest
from dataclasses import dataclass
from qmotion_gen3_fm.cli import run_pairing

@dataclass
class FakeGroup:
    name: str = "homeassistant"
    channel: int = 9
    page: bytes = bytes.fromhex("00 02")

class FakeGateway:
    def __init__(self):
        self.calls = []
    def prepare_pairing(self, channel):
        self.calls.append(("prepare", channel))
    def complete_pairing(self, group):
        self.calls.append(("complete", group.name, group.page))

def responses(*answers):
    iterator = iter(answers)
    return lambda prompt: next(iterator)

class PairingWorkflowTests(unittest.TestCase):
    def test_happy_path(self):
        gw = FakeGateway()
        messages = []
        ok = run_pairing(gw, FakeGroup(), responses("READY", "SEND", "JOG", "PAIR"), messages.append, dry_run=False)
        self.assertTrue(ok)
        self.assertEqual(gw.calls, [("prepare", 9), ("complete", "homeassistant", bytes.fromhex("00 02"))])
        self.assertTrue(any("34 03 02 00 09" in line for line in messages))

    def test_dry_run_never_transmits(self):
        gw = FakeGateway()
        messages = []
        ok = run_pairing(gw, FakeGroup(),
                         responses("READY", "SEND", "JOG", "PAIR"),
                         messages.append)
        self.assertTrue(ok)
        self.assertEqual(gw.calls, [])
        self.assertTrue(any("DRY RUN" in message for message in messages))
        self.assertTrue(any("NOT transmitted" in message for message in messages))

    def test_default_is_dry_run(self):
        gw = FakeGateway()
        self.assertTrue(run_pairing(gw, FakeGroup(), responses("READY", "SEND", "JOG", "PAIR"), lambda _: None))
        self.assertEqual(gw.calls, [])

    def test_cancel_before_transmission(self):
        for replies in [("NO",), ("READY", "NO")]:
            with self.subTest(replies=replies):
                gw = FakeGateway()
                self.assertFalse(run_pairing(gw, FakeGroup(), responses(*replies), lambda _: None, dry_run=False))
                self.assertEqual(gw.calls, [])

    def test_no_jog_never_completes(self):
        gw = FakeGateway()
        self.assertFalse(run_pairing(gw, FakeGroup(), responses("READY", "SEND", "NO"), lambda _: None, dry_run=False))
        self.assertEqual(gw.calls, [("prepare", 9)])

    def test_final_confirmation_required(self):
        gw = FakeGateway()
        self.assertFalse(run_pairing(gw, FakeGroup(), responses("READY", "SEND", "JOG", "NO"), lambda _: None, dry_run=False))
        self.assertEqual(gw.calls, [("prepare", 9)])

if __name__ == "__main__":
    unittest.main()
