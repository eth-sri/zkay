from zkay.transaction.crypto import babyjubjub

from zkay.transaction.crypto.elgamal import ElgamalCrypto

from zkay.tests.zkay_unit_test import ZkayTestCase


class TestElgamal(ZkayTestCase):

    def test_enc_with_rand(self):
        eg = ElgamalCrypto(None)
        plain = 42
        random = 4992017890738015216991440853823451346783754228142718316135811893930821210517
        pk = [10420944247972906704901930255398155539251465080449381763175509401634402210816,
              676510933272081718087751130659922602804650769442378705766141464386492472495]
        cipher = eg._enc_with_rand(plain, random, pk)
        expected = [19192972422083923186464070519964101192898498903392337276087603285275966620124,
                    6618023754137786203285728996559262879033810391268429127227951976541677679344,
                    6783999682040621346526809601076528941995554662915581379351509236123929622234,
                    20987236539628450607197235495899116821794698514394599573760118705643049424532]
        self.assertEqual(cipher, expected)

    def test_de_embed(self):
        eg = ElgamalCrypto(None)
        embedded = [10535323380993087886472965362609445287191380307215483857591983963545230395281,
                    7231436746873551518227382498558787106156958562991793706165873939508722228633]
        plain = eg._de_embed(babyjubjub.Point(babyjubjub.Fq(embedded[0]), babyjubjub.Fq(embedded[1])))
        expected = 42
        self.assertEqual(plain, expected)

    def test_decrypt(self):
        eg = ElgamalCrypto(None)
        cipher = [19192972422083923186464070519964101192898498903392337276087603285275966620124,
                  6618023754137786203285728996559262879033810391268429127227951976541677679344,
                  6783999682040621346526809601076528941995554662915581379351509236123929622234,
                  20987236539628450607197235495899116821794698514394599573760118705643049424532]
        sk = 448344687855328518203304384067387474955750326758815542295083498526674852893
        plain, _ = eg._dec(cipher, sk)
        expected = 42
        self.assertEqual(plain, expected)
