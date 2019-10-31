from typing import Union

from OpenSSL import crypto


def create_csr(common_name: str, country=None, state=None, city=None,
               organization=None, organizational_unit=None,
               email_address=None) -> (bytes, bytes):
    """ Returns: private key and certificate signing request (PEM). """
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    req = crypto.X509Req()
    subject = req.get_subject()
    subject.CN = common_name
    if country:
        subject.C = country
    if state:
        subject.ST = state
    if city:
        subject.L = city
    if organization:
        subject.O = organization  # noqa
    if organizational_unit:
        subject.OU = organizational_unit
    if email_address:
        subject.emailAddress = email_address

    req.set_pubkey(key)
    req.sign(key, 'sha256')

    return (
        crypto.dump_privatekey(crypto.FILETYPE_PEM, key),
        crypto.dump_certificate_request(crypto.FILETYPE_PEM, req),
    )


def export_pkcs12(cert: Union[bytes, crypto.X509],
                  key: Union[bytes, crypto.PKey],
                  passphrase: bytes = None) -> bytes:
    if not isinstance(cert, crypto.X509):
        # silly check
        if b'CERTIFICATE' not in cert:
            cert = (
                b'-----BEGIN CERTIFICATE-----\n'
                b'%s\n'
                b'-----END CERTIFICATE-----'
            ) % cert
        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
    if not isinstance(key, crypto.PKey):
        if b'PRIVATE KEY' not in key:
            key = (
                b'-----BEGIN PRIVATE KEY-----\n'
                b'%s\n'
                b'-----END PRIVATE KEY-----'
            ) % key
        key = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
    p12 = crypto.PKCS12()
    p12.set_certificate(cert)
    p12.set_privatekey(key)
    return p12.export(passphrase)


def load_pkcs12(data: bytes, passphrase: bytes = None) -> (bytes, bytes):
    assert isinstance(data, bytes)
    p12 = crypto.load_pkcs12(data, passphrase)
    cert = p12.get_certificate()
    key = p12.get_privatekey()
    return (
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert),
        crypto.dump_privatekey(crypto.FILETYPE_PEM, key),
    )


def sign_pkcs7_data(data, cert, key, stack=crypto._ffi.NULL):
    if isinstance(data, str):
        data = data.encode()
    bio_in = crypto._new_mem_buf(data)
    pkcs7 = crypto._lib.PKCS7_sign(
        cert._x509, key._pkey, stack, bio_in, crypto._lib.PKCS7_NOSIGS,
    )
    bio_out = crypto._new_mem_buf()
    crypto._lib.i2d_PKCS7_bio(bio_out, pkcs7)
    return crypto._bio_to_string(bio_out)


def verify_pkcs7_data(data):
    pdata = crypto.load_pkcs7_data(crypto.FILETYPE_ASN1, data)
    bio_out = crypto._new_mem_buf()
    crypto._lib.PKCS7_verify(
        pdata._pkcs7,
        crypto._ffi.NULL,
        crypto._ffi.NULL,
        crypto._ffi.NULL,
        bio_out,
        crypto._lib.PKCS7_NOVERIFY
    )
    return crypto._bio_to_string(bio_out)
