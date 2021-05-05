# modification of sapling_jubjub.py frrom https://github.com/zcash-hackworks/zcash-test-vectors
# changed JubJub parameters to BabyJubJub parameters

"""
The MIT License (MIT)

Copyright (c) 2018-2019 Electric Coin Company

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

BASE_ORDER = 21888242871839275222246405745257275088548364400416034343698204186575808495617

CURVE_ORDER = 21888242871839275222246405745257275088614511777268538073601725287587578984328


class FieldElement(object):
    def __init__(self, t, s, modulus, strict=False):
        if strict and not (0 <= s and s < modulus):
            raise ValueError
        self.t = t
        self.s = s % modulus
        self.m = modulus

    def __neg__(self):
        return self.t(-self.s)

    def __add__(self, a):
        return self.t(self.s + a.s)

    def __sub__(self, a):
        return self.t(self.s - a.s)

    def __mul__(self, a):
        return self.t(self.s * a.s)

    def __truediv__(self, a):
        assert a.s != 0
        return self * a.inv()

    def exp(self, e):
        e = format(e, '0256b')
        ret = self.t(1)
        for c in e:
            ret = ret * ret
            if int(c):
                ret = ret * self
        return ret

    def inv(self):
        return self.exp(self.m - 2)

    def __eq__(self, a):
        return self.s == a.s


class Fq(FieldElement):

    def __init__(self, s, strict=False):
        FieldElement.__init__(self, Fq, s, BASE_ORDER, strict=strict)

    def __str__(self):
        return 'Fq(%s)' % self.s


class Fr(FieldElement):
    def __init__(self, s, strict=False):
        FieldElement.__init__(self, Fr, s, CURVE_ORDER, strict=strict)

    def __str__(self):
        return 'Fr(%s)' % self.s


Fq.ZERO = Fq(0)
Fq.ONE = Fq(1)
Fq.MINUS_ONE = Fq(-1)

assert Fq.ZERO + Fq.ZERO == Fq.ZERO
assert Fq.ZERO + Fq.ONE == Fq.ONE
assert Fq.ONE + Fq.ZERO == Fq.ONE
assert Fq.ZERO - Fq.ONE == Fq.MINUS_ONE
assert Fq.ZERO * Fq.ONE == Fq.ZERO
assert Fq.ONE * Fq.ZERO == Fq.ZERO


#
# Point arithmetic
#

BABYJUBJUB_A = Fq(168700)
BABYJUBJUB_D = Fq(168696)

BABYJUBJUB_GENERATOR_X = 16540640123574156134436876038791482806971768689494387082833631921987005038935
BABYJUBJUB_GENERATOR_Y = 20819045374670962167435360035096875258406992893633759881276124905556507972311


class Point(object):
    def __init__(self, u, v):
        self.u = u
        self.v = v

    def __add__(self, a):
        (u1, v1) = (self.u, self.v)
        (u2, v2) = (a.u, a.v)
        u3 = (u1*v2 + v1*u2) / (Fq.ONE + BABYJUBJUB_D * u1 * u2 * v1 * v2)
        v3 = (v1 * v2 - BABYJUBJUB_A * u1 * u2) / (Fq.ONE - BABYJUBJUB_D * u1 * u2 * v1 * v2)
        return Point(u3, v3)

    def double(self):
        return self + self

    def negate(self):
        return Point(-self.u, self.v)

    def __mul__(self, s):
        s = format(s.s, '0256b')
        ret = self.ZERO
        for c in s:
            ret = ret.double()
            if int(c):
                ret = ret + self
        return ret

    def __eq__(self, a):
        return self.u == a.u and self.v == a.v

    def __str__(self):
        return 'Point(%s, %s)' % (self.u, self.v)


Point.ZERO = Point(Fq.ZERO, Fq.ONE)
Point.GENERATOR = Point(Fq(BABYJUBJUB_GENERATOR_X), Fq(BABYJUBJUB_GENERATOR_Y))

assert Point.ZERO + Point.ZERO == Point.ZERO
