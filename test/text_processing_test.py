import unittest

import unicodedata

from src.utils import normalize, last_name


class TestNormalize(unittest.TestCase):

    def test_unicode(self):
        x = [
            "YOU ARE DEAD1",  # chr(8)
            "☠️YOU ARE DEAD2",
        ]
        y = [normalize(e, do=['ctrl', 'unicode']) for e in x]
        z = [
            "YOU ARE DEAD1",
            "YOU ARE DEAD2"
        ]
        for res, exp in zip(y, z):
            self.assertEqual(res, exp)

    def test_accents(self):
        x = [
            "Álvarez-Fernández",
        ]
        y = [normalize(e.lower(), do_not_remove='-') for e in x]
        z = [
            "Alvarez-Fernandez",
        ]
        for res, expect in zip(y, z):
            self.assertEqual(res, expect.lower())

    def test_html_tags(self):
        x = "the parasite <i>Plasmodium</i> in Ca<sup>2+</sup> was"
        y = normalize(x, do_not_remove='+')
        z = "the parasite plasmodium in ca2+ was"
        self.assertEqual(y, z)
        self.assertNotEqual(x, z)


class TestLastName(unittest.TestCase):

    def test_last_name(self):
        x = [
            "John van der Putten",
            "Silver Peter Mac Mahon",
            "Si McMahon",
            "Ron St John",
        ]
        y = [last_name(e.lower()) for e in x]
        z = [
            "van der putten",
            "Mac Mahon",
            "McMahon",
            "St John",
        ]
        for res, expect in zip(y, z):
            self.assertEqual(res, expect.lower())


if __name__ == '__main__':
    unittest.main()
