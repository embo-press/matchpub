import unittest

from src.utils import time_diff


class TestTimeDiff(unittest.TestCase):
    def test_europe_dot(self):
        start = "1.12.2019"
        end = "2.12.2019"
        diff = time_diff(start, end, dayfirst=True)
        self.assertEqual(diff, 1)

        start = "1.12.2019"
        end = "1.1.2020"
        diff = time_diff(start, end, dayfirst=True)
        self.assertEqual(diff, 31)

        start = "1.12.2018"
        end = "1.12.2019"
        diff = time_diff(start, end, dayfirst=True)
        self.assertEqual(diff, 365)

        start = "1.12.2019"
        end = "1.12.2020"
        diff = time_diff(start, end, dayfirst=True)
        self.assertEqual(diff, 366)

    def test_europe_month(self):
        start = "1 Dec 2019"
        end = "2 Jan 2021"
        diff = time_diff(start, end, dayfirst=True)
        self.assertEqual(diff, 366 + 31 + 1)

    def test_us_dot(self):
        start = "12.1.2019"
        end = "1.2.2021"
        diff = time_diff(start, end, dayfirst=False)
        self.assertEqual(diff, 366 + 31 + 1)

    def test_messy(self):
        start = "December 1st, 2019"
        end = "2nd Jan 2021"
        diff = time_diff(start, end, dayfirst=False)
        self.assertEqual(diff, 366 + 31 + 1)


if __name__ == '__main__':
    unittest.main()
