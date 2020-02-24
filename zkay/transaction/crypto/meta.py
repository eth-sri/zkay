cryptoparams = {'dummy': {
    'key_bits': 248,
    'cipher_payload_bytes': 31,
    'symmetric': False,
    'rnd_bytes': 31
}, 'rsa-oaep': {
    'key_bits': 2048,
    'cipher_payload_bytes': 256,
    'symmetric': False,
    'rnd_bytes': 32
}, 'rsa-pkcs1.5': {
    'key_bits': 2048,
    'cipher_payload_bytes': 256,
    'symmetric': False,
    'rnd_bytes': 221 # for 256 - 3 - plainbytes (32 byte plaintext, for now fixed)
}, 'ecdh-aes': {
    'key_bits': 253,
    'cipher_payload_bytes': 48, # 128bit iv + 256 bit ciphertext
    'symmetric': True,
    'rnd_bytes': 0
}, 'ecdh-chaskey': {
    'key_bits': 253,
    'cipher_payload_bytes': 48, # 128bit iv + 256 bit ciphertext
    'symmetric': True,
    'rnd_bytes': 0
}}
