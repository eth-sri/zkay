import os
import shutil
from contextlib import contextmanager

from parameterized import parameterized_class

from zkay.zkay_frontend import compile_zkay
from zkay.config import cfg
from zkay.examples.examples import all_examples, get_code_example
from zkay.tests.utils.test_examples import TestExamples

# get relevant paths
output_dir = os.path.join(cfg.log_dir, 'compile_tests', 'output')
os.makedirs(output_dir, exist_ok=True)


@contextmanager
def _mock_config(crypto: str, crypto_addhom: str, hash_opt):
    old_c_nh, old_c_add, old_h = cfg.main_crypto_backend, cfg.addhom_crypto_backend, cfg.should_use_hash
    cfg.main_crypto_backend = crypto
    cfg.addhom_crypto_backend = crypto_addhom
    cfg.should_use_hash = (lambda _: hash_opt) if isinstance(hash_opt, bool) else hash_opt
    yield
    cfg.main_crypto_backend, cfg.addhom_crypto_backend, cfg.should_use_hash = old_c_nh, old_c_add, old_h


#@parameterized_class(('name', 'example'), get_code_example('.zkay'))
@parameterized_class(('name', 'example'), all_examples)
class TestCompiler(TestExamples):

    def get_directory(self):
        d = os.path.join(output_dir, self.name)

        if os.path.isdir(d):
            shutil.rmtree(d)
        os.mkdir(d)

        return d

    def test_compilation_pipeline(self):
        c = self.example.code()
        d = self.get_directory()

        with _mock_config('dummy', 'dummy-hom', False):
            cg, code = compile_zkay(c, d)

        self.assertIsNotNone(cg)
        self.assertIsNotNone(code)
        self.assertIn(self.example.name(), code)

        shutil.rmtree(d)
