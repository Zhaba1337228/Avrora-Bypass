import unittest

from code_typing_utility.services.text_loader import leading_spaces_to_tabs


class LeadingSpacesToTabsTests(unittest.TestCase):
    def test_groups_remainder_and_content(self):
        source = "    first\n        second\n      third\n   short\n    print(\"a  b\")\n"
        expected = "\tfirst\n\t\tsecond\n\t  third\n   short\n\tprint(\"a  b\")\n"
        self.assertEqual(leading_spaces_to_tabs(source, 4), expected)

    def test_existing_tabs_mixed_spaces_crlf_and_blank_lines(self):
        source = "  \t    a\r\n    \r\n\tb\r\n"
        self.assertEqual(leading_spaces_to_tabs(source, 4), "  \t\ta\r\n\t\r\n\tb\r\n")
        self.assertEqual(leading_spaces_to_tabs("  x\n    y", 2), "\tx\n\t\ty")

    def test_invalid_width(self):
        for width in (0, 17):
            with self.assertRaises(ValueError):
                leading_spaces_to_tabs("    x", width)
