"""
This package contains the cryptography backends.

==========
Submodules
==========
* :py:mod:`.dummy`: Fast but insecure key generation (pk == sk == address) and encryption (enc = (+), dec = (-)) for debugging
* :py:mod:`.rsa_pkcs15`: Slow, secure rsa key generation and encryption using RSA PKCS1.5 padding
* :py:mod:`.rsa_oaep`: Very slow, secure rsa key generation and encryption using RSA OAEP padding
"""
