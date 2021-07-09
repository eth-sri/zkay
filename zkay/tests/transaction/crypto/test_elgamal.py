from zkay.transaction.crypto import babyjubjub

from zkay.transaction.crypto.elgamal import ElgamalCrypto

from zkay.tests.zkay_unit_test import ZkayTestCase
from zkay.transaction.types import CipherValue


class TestElgamal(ZkayTestCase):

    def test_enc_with_rand(self):
        eg = ElgamalCrypto(None)
        plain = 42
        random = 4992017890738015216991440853823451346783754228142718316135811893930821210517
        pk = [2543111965495064707612623550577403881714453669184859408922451773306175031318,
              20927827475527585117296730644692999944545060105133073020125343132211068382185]
        cipher = eg._enc_with_rand(plain, random, pk)
        expected = [17990166387038654353532224054392704246273066434684370089496246721960255371329,
                    15866190370882469414665095798958204707796441173247149326160843221134574846694,
                    13578016172019942326633412365679613147103709674318008979748420035774874659858,
                    15995926508900361671313404296634773295236345482179714831868518062689263430374]
        self.assertEqual(cipher, expected)

    def test_enc_with_zero(self):
        eg = ElgamalCrypto(None)
        plain = 0
        random = 0
        pk = [2543111965495064707612623550577403881714453669184859408922451773306175031318,
              20927827475527585117296730644692999944545060105133073020125343132211068382185]
        cipher = eg._enc_with_rand(plain, random, pk)
        expected = [0, 1, 0, 1]
        self.assertEqual(cipher, expected)

    def test_de_embed_0(self):
        eg = ElgamalCrypto(None)
        plain = eg._de_embed(babyjubjub.Point.ZERO)
        expected = 0
        self.assertEqual(plain, expected)

    def test_de_embed_1(self):
        eg = ElgamalCrypto(None)
        plain = eg._de_embed(babyjubjub.Point.GENERATOR)
        expected = 1
        self.assertEqual(plain, expected)

    def test_de_embed_other(self):
        eg = ElgamalCrypto(None)
        embedded = [141579968252753561777903806704988380915591798817413028638954837858390837201,
                    8211442360329077616485844356105856211290554633036363698328149195845491718472]
        plain = eg._de_embed(babyjubjub.Point(babyjubjub.Fq(embedded[0]), babyjubjub.Fq(embedded[1])))
        expected = 42
        self.assertEqual(plain, expected)

    def test_decrypt(self):
        eg = ElgamalCrypto(None)
        cipher = [17990166387038654353532224054392704246273066434684370089496246721960255371329,
                  15866190370882469414665095798958204707796441173247149326160843221134574846694,
                  13578016172019942326633412365679613147103709674318008979748420035774874659858,
                  15995926508900361671313404296634773295236345482179714831868518062689263430374]
        sk = 448344687855328518203304384067387474955750326758815542295083498526674852893
        plain, _ = eg._dec(cipher, sk)
        expected = 42
        self.assertEqual(plain, expected)

    def test_homomorphic_add(self):
        eg = ElgamalCrypto(None)
        cipher1 = CipherValue([17990166387038654353532224054392704246273066434684370089496246721960255371329,
                               15866190370882469414665095798958204707796441173247149326160843221134574846694,
                               13578016172019942326633412365679613147103709674318008979748420035774874659858,
                               15995926508900361671313404296634773295236345482179714831868518062689263430374])
        cipher2 = CipherValue([20000451794290380375914691798920385097103434955980148521154607378788339649411,
                               3379688933589504078077257631396507733503572474143535438012650064116108361323,
                               19394553866420759826901398082663942344084257999221733532877406304105119931558,
                               20583024216337563044477284173241746163084488704258522180236559083511927239523])
        res = eg.do_op('+', None, cipher1, cipher2)
        expected = [18885199402227818148211810144232318738102042906622969713112212912459159846007,
                    11125071952177567933017599368067887482603292954302203070407920687516147981132,
                    20036470080915178878390944667725801469044803295396841663384258912114611255016,
                    18986185709423663075397883577572338596028661172318034324882291197251276265727]
        self.assertEqual(res, expected)

    def test_homomorphic_add_zero(self):
        eg = ElgamalCrypto(None)
        cipher1 = CipherValue([17990166387038654353532224054392704246273066434684370089496246721960255371329,
                               15866190370882469414665095798958204707796441173247149326160843221134574846694,
                               13578016172019942326633412365679613147103709674318008979748420035774874659858,
                               15995926508900361671313404296634773295236345482179714831868518062689263430374])
        cipher2 = CipherValue([0, 0, 0, 0])
        res = eg.do_op('+', None, cipher1, cipher2)
        self.assertEqual(CipherValue(res), cipher1)

    def test_homomorphic_sub(self):
        eg = ElgamalCrypto(None)
        cipher1 = CipherValue([18885199402227818148211810144232318738102042906622969713112212912459159846007,
                               11125071952177567933017599368067887482603292954302203070407920687516147981132,
                               20036470080915178878390944667725801469044803295396841663384258912114611255016,
                               18986185709423663075397883577572338596028661172318034324882291197251276265727])
        cipher2 = CipherValue([20000451794290380375914691798920385097103434955980148521154607378788339649411,
                               3379688933589504078077257631396507733503572474143535438012650064116108361323,
                               19394553866420759826901398082663942344084257999221733532877406304105119931558,
                               20583024216337563044477284173241746163084488704258522180236559083511927239523])
        res = eg.do_op('-', None, cipher1, cipher2)
        expected = [17990166387038654353532224054392704246273066434684370089496246721960255371329,
                    15866190370882469414665095798958204707796441173247149326160843221134574846694,
                    13578016172019942326633412365679613147103709674318008979748420035774874659858,
                    15995926508900361671313404296634773295236345482179714831868518062689263430374]
        self.assertEqual(res, expected)

    def test_homomorphic_mul(self):
        eg = ElgamalCrypto(None)
        cipher = CipherValue([17990166387038654353532224054392704246273066434684370089496246721960255371329,
                              15866190370882469414665095798958204707796441173247149326160843221134574846694,
                              13578016172019942326633412365679613147103709674318008979748420035774874659858,
                              15995926508900361671313404296634773295236345482179714831868518062689263430374])
        expected = eg.do_op('+', None, cipher, cipher)
        res = eg.do_op('*', None, cipher, 2)
        self.assertEqual(res, expected)
