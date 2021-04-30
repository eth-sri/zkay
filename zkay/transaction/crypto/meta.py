cryptoparams = {
    'dummy': {
        'key_bits': 248,
        'cipher_payload_bytes': 31,
        'cipher_chunk_size': 31,
        'symmetric': False,
        'rnd_bytes': 31,
        'rnd_chunk_size': 31,
        'enc_signed_as_unsigned': True,
    },

    'dummy-hom': {
        'key_bits': 248,
        'cipher_payload_bytes': 32,
        'cipher_chunk_size': 32,
        'symmetric': False,
        'rnd_bytes': 32,
        'rnd_chunk_size': 32,
        'enc_signed_as_unsigned': False,
    },

    'rsa-oaep': {
        'key_bits': 2048,
        'cipher_payload_bytes': 256,
        'cipher_chunk_size': 29,
        'symmetric': False,
        'rnd_bytes': 32,
        'rnd_chunk_size': 16,
        'enc_signed_as_unsigned': True,
    },

    'rsa-pkcs1.5': {
        'key_bits': 2048,
        'cipher_payload_bytes': 256,
        'cipher_chunk_size': 29,
        'symmetric': False,
        'rnd_bytes': 221,  # for 256 - 3 - plainbytes (32 byte plaintext, for now fixed)
        'rnd_chunk_size': 28,
        'enc_signed_as_unsigned': True,
    },

    'ecdh-aes': {
        'key_bits': 253,
        'cipher_payload_bytes': 48, # 128bit iv + 256 bit ciphertext
        'cipher_chunk_size': 24,
        'symmetric': True,
        'rnd_bytes': 0, # included in cipher text
        'rnd_chunk_size': 0,
        'enc_signed_as_unsigned': True,
    },

    'ecdh-chaskey': {
        'key_bits': 253,
        'cipher_payload_bytes': 48, # 128bit iv + 256 bit ciphertext
        'cipher_chunk_size': 24,
        'symmetric': True,
        'rnd_bytes': 0, # included in cipher text
        'rnd_chunk_size': 0,
        'enc_signed_as_unsigned': True,
    },

    # WARNING: Not cryptographically secure. Values retained for developer sanity.
    # Recommended values:
    # - key_bits: 2048
    # - cipher_payload_bytes: 4096 // 8
    # - rnd_bytes: 2048 // 8
    'paillier': {
        'key_bits': 320,  # 320-bit n
        'cipher_payload_bytes': 640 // 8,  # cipher is mod n^2, thus at most twice the bit length
        'cipher_chunk_size': 120 // 8,  # LongElement.CHUNK_SIZE / sizeof(byte)
        'symmetric': False,
        'rnd_bytes': 320 // 8,  # random value mod n, thus same size as n
        'rnd_chunk_size': 120 // 8,  # LongElement.CHUNK_SIZE / sizeof(byte)
        'enc_signed_as_unsigned': False,
    },

    'elgamal': {
        'key_bits': 2*253,                  # two BabyJubJub coordinates
        'cipher_payload_bytes': 128,        # four BabyJubJub coordinates
        'cipher_chunk_size': 32,            # one BabyJubJub coordinate
        'symmetric': False,
        'rnd_bytes': 32,                    # one element from the BabyJubJub scalar field
        'rnd_chunk_size': 32,
        'enc_signed_as_unsigned': False,
    }
}
