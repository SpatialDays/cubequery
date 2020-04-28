import unittest

from cubequery.ipaddress_matching import match


class TestIPAddressMatching(unittest.TestCase):
    def test_valid_matches(self):
        self.assertTrue(match('', 'anything'))
        self.assertTrue(match('192.168.0.1', '192.168.0.1'))
        self.assertTrue(match('192.168.0.*', '192.168.0.1'))
        self.assertTrue(match('192.168.0.*', '192.168.0.34'))
        self.assertTrue(match('192.168.0.*', '192.168.0.255'))  # this is not a valid address I know.
