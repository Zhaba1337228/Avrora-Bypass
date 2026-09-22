import unittest

from code_typing_utility.domain.models import TypingSettings
from code_typing_utility.domain.planner import KeystrokePlanner


class KeystrokePlannerTests(unittest.TestCase):
    def test_seed_makes_delay_sequence_reproducible(self) -> None:
        settings = TypingSettings(220, 0, 18, seed=42)
        first = KeystrokePlanner(settings)
        second = KeystrokePlanner(settings)
        pairs = [("a", "b"), ("b", " "), (" ", "c"), ("c", "\n")]

        self.assertEqual(
            [first.delay_after(*pair) for pair in pairs],
            [second.delay_after(*pair) for pair in pairs],
        )

    def test_delays_are_never_below_minimum(self) -> None:
        planner = KeystrokePlanner(TypingSettings(600, 0, 45, seed=1))

        self.assertGreaterEqual(planner.delay_after("a", "b"), 0.018)

    def test_invalid_settings_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            KeystrokePlanner(TypingSettings(1, 0, 0))
