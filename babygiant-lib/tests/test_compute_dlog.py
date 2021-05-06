import unittest

import babygiant


def to_le_32_hex_bytes(num):
    hx = "{0:0{1}x}".format(num, 32)
    b = "".join(reversed(["".join(x) for x in zip(*[iter(hx)] * 2)]))
    return b


class TestComputeDlog(unittest.TestCase):

    def test_compute_dlog(self):
        x = 11904062828411472290643689191857696496057424932476499415469791423656658550213
        y = 9356450144216313082194365820021861619676443907964402770398322487858544118183
        self.assertEqual(1, babygiant.compute_dlog(to_le_32_hex_bytes(x), to_le_32_hex_bytes(y)))
