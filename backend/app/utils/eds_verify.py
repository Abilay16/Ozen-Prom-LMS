"""
Cryptographic verification of NCALayer CMS (PKCS#7 SignedData) signatures.

This is the part cms_parser.py never did: it only ever *read* the fields of
the certificate embedded in the CMS blob (name, dates) without checking that
the signature bytes are mathematically valid, or that the certificate was
actually issued by НУЦ РК rather than self-signed/forged.

What this module adds, for RSA-signed ЭЦП (the common case — most НУЦ РК
individual certificates are RSA):
  1. Verifies the CMS signature cryptographically against the exact signed
     payload (handles both the "signed attributes" CAdES-BES form NCALayer
     produces, and the simpler direct-signature form).
  2. Verifies the certificate chain up to the real НУЦ РК root CA, using the
     actual certificates downloaded from pki.gov.kz / root.gov.kz (bundled
     under backend/app/certs/, chain verified with `openssl verify` against
     the live root at the time they were fetched).

What it does NOT do, and why — be upfront about this rather than pretend:
  - GOST-signed ЭЦП (Kazakhstan's national variant, OID prefix
    "1.2.398.3.10.1.1.2", NOT the Russian GOST OID tree that libraries like
    pygost/gostcrypto understand) cannot be cryptographically verified here.
    No available library recognizes this OID or has its curve parameters,
    and the digital-signature math genuinely cannot be faked safely. For a
    GOST certificate this function falls back to a *structural* chain check
    only (does the issuer/subject DN chain line up with the real НУЦ РК
    GOST CAs) plus the existing name+expiry checks — it does NOT confirm the
    signature bytes are authentic. Callers must check `.algorithm` and
    `.crypto_verified` and surface this distinction (see protocols.py).
  - Revocation (CRL/OCSP) checking — pki.gov.kz does publish live endpoints
    (http://ocsp.pki.gov.kz/, https://crl.pki.gov.kz/nca_rsa_2022.crl) but
    that requires a live network call at sign time, which is a separate,
    riskier piece of infrastructure (what happens if the OCSP responder is
    down? do we block signing?) — intentionally left for a follow-up.
"""
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from asn1crypto import cms as asn1_cms, pem as asn1_pem, x509 as asn1_x509
from cryptography import x509 as crypto_x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

_CERTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "certs")

# Kazakhstan's national digital-signature OID arc — not the Russian GOST
# tree (1.2.643.*) that any available Python library implements.
_GOST_OID_PREFIX = "1.2.398.3.10.1.1.2"

_DIGEST_OID_TO_HASH = {
    "sha256": hashes.SHA256(),
    "sha384": hashes.SHA384(),
    "sha512": hashes.SHA512(),
    "sha1": hashes.SHA1(),
}


def _load_pem(filename: str) -> crypto_x509.Certificate:
    path = os.path.join(_CERTS_DIR, filename)
    with open(path, "rb") as f:
        return crypto_x509.load_pem_x509_certificate(f.read())


# Loaded once at import time; tests monkeypatch these two lists directly
# (see conftest.py) to register a throwaway self-signed root instead of
# reaching for real НУЦ РК certificates.
RSA_ROOT = _load_pem("nca_root_rsa_2020.pem")
RSA_ISSUING = _load_pem("nca_issuing_rsa_2022.pem")
GOST_ROOT = _load_pem("nca_root_gost_2022.pem")
GOST_ISSUING = _load_pem("nca_issuing_gost_2022.pem")

RSA_TRUST_CHAIN = [RSA_ISSUING, RSA_ROOT]
GOST_TRUST_CHAIN = [GOST_ISSUING, GOST_ROOT]


class EDSVerifyError(ValueError):
    """Raised when a CMS fails cryptographic or chain verification."""


@dataclass
class VerifyResult:
    algorithm: str  # "RSA" | "GOST" | "unknown"
    signature_valid: bool
    chain_valid: bool
    crypto_verified: bool  # True only when BOTH checks above were real crypto checks (RSA)
    warnings: list[str] = field(default_factory=list)


def _verify_rsa_signature(pubkey: rsa.RSAPublicKey, signed_bytes: bytes,
                           signature: bytes, digest_name: str, is_pss: bool) -> bool:
    hash_algo = _DIGEST_OID_TO_HASH.get(digest_name, hashes.SHA256())
    try:
        if is_pss:
            pubkey.verify(
                signature, signed_bytes,
                padding.PSS(mgf=padding.MGF1(hash_algo), salt_length=hash_algo.digest_size),
                hash_algo,
            )
        else:
            pubkey.verify(signature, signed_bytes, padding.PKCS1v15(), hash_algo)
        return True
    except InvalidSignature:
        return False


def _verify_chain_rsa(leaf: crypto_x509.Certificate) -> bool:
    """Verify leaf -> issuing -> root, each link's signature checked with
    the parent's real public key (not just DN string matching)."""
    chain = [leaf] + RSA_TRUST_CHAIN
    for child, parent in zip(chain, chain[1:]):
        if child.issuer != parent.subject:
            return False
        parent_pub = parent.public_key()
        if not isinstance(parent_pub, rsa.RSAPublicKey):
            return False
        try:
            parent_pub.verify(
                child.signature, child.tbs_certificate_bytes,
                padding.PKCS1v15(), child.signature_hash_algorithm,
            )
        except InvalidSignature:
            return False
    return True


def verify_cms(cms_b64_or_der, payload: bytes) -> VerifyResult:
    """
    Cryptographically verify a CMS SignedData blob against the exact bytes
    that were supposedly signed (the protocol's signature-payload string,
    UTF-8 encoded — same bytes NCALayer received as base64 input).
    """
    import base64
    raw = cms_b64_or_der if isinstance(cms_b64_or_der, (bytes, bytearray)) else base64.b64decode(cms_b64_or_der)
    if asn1_pem.detect(raw):
        _, _, raw = asn1_pem.unarmor(raw)

    content_info = asn1_cms.ContentInfo.load(raw)
    signed_data = content_info["content"]
    certs = signed_data["certificates"]
    if not certs or len(certs) == 0:
        raise EDSVerifyError("В CMS нет сертификата подписанта")

    leaf_asn1 = certs[0].chosen
    leaf_der = leaf_asn1.dump()
    leaf = crypto_x509.load_der_x509_certificate(leaf_der)

    signer_infos = signed_data["signer_infos"]
    if not signer_infos or len(signer_infos) == 0:
        raise EDSVerifyError("В CMS нет SignerInfo")
    signer_info = signer_infos[0]

    digest_algo = signer_info["digest_algorithm"]["algorithm"].native
    sig_algo_oid = signer_info["signature_algorithm"]["algorithm"].dotted
    is_pss = "rsassa-pss" in (signer_info["signature_algorithm"]["algorithm"].native or "")
    signature = signer_info["signature"].native

    # Read the OID via `cryptography` (backed by OpenSSL's generic ASN.1
    # parser), NOT via asn1crypto's typed x509 structures: asn1crypto's
    # PublicKeyInfo/PublicKeyAlgorithm classes try to resolve a spec for
    # the *parameters* field as soon as ANY of their fields is touched —
    # including just reading the algorithm OID — and that spec lookup is a
    # dict keyed by known algorithm names. An OID it doesn't recognize
    # (like Kazakhstan's GOST arc below) raises KeyError and crashes the
    # whole signing request with a 500 instead of being handled as the
    # "can't verify this" case it actually is. cryptography's OpenSSL-backed
    # loader has no such problem — it only tries to build a Python key
    # object when you call .public_key(), which we never do for GOST.
    pubkey_oid = leaf.public_key_algorithm_oid.dotted_string
    is_gost = pubkey_oid.startswith(_GOST_OID_PREFIX)

    warnings: list[str] = []

    if is_gost:
        # Structural-only chain check: DN linkage, no signature math possible
        # (see module docstring for why).
        chain_valid = (
            leaf.issuer == GOST_TRUST_CHAIN[0].subject
            and GOST_TRUST_CHAIN[0].issuer == GOST_TRUST_CHAIN[1].subject
        )
        warnings.append(
            "ГОСТ-сертификат: криптографическая проверка подписи не выполнена "
            "(нет доступной реализации казахстанского варианта ГОСТ, OID "
            f"{pubkey_oid}) — проверены только срок действия, ФИО и структура цепочки."
        )
        return VerifyResult(
            algorithm="GOST", signature_valid=False, chain_valid=chain_valid,
            crypto_verified=False, warnings=warnings,
        )

    if pubkey_oid not in ("1.2.840.113549.1.1.1",):  # rsaEncryption
        warnings.append(f"Неизвестный алгоритм ключа подписанта (OID {pubkey_oid})")
        return VerifyResult(
            algorithm="unknown", signature_valid=False, chain_valid=False,
            crypto_verified=False, warnings=warnings,
        )

    leaf_pub = leaf.public_key()
    if not isinstance(leaf_pub, rsa.RSAPublicKey):
        return VerifyResult(
            algorithm="unknown", signature_valid=False, chain_valid=False,
            crypto_verified=False, warnings=["Открытый ключ подписанта не RSA"],
        )

    # Build the bytes that were actually signed. NCALayer (like most CAdES
    # tools) signs the DER encoding of the SignedAttributes SET, not the
    # raw content directly, when signed_attrs are present — and separately
    # binds that SET to the content via the messageDigest attribute.
    signed_attrs = signer_info["signed_attrs"]
    digest_name = {
        "sha256": "sha256", "sha384": "sha384", "sha512": "sha512", "sha1": "sha1",
    }.get(digest_algo, "sha256")

    if signed_attrs and signed_attrs.native:
        import hashlib
        h = hashlib.new(digest_name.replace("sha", "sha"))
        h.update(payload)
        content_digest = h.digest()

        msg_digest_attr = None
        for attr in signed_attrs:
            if attr["type"].native == "message_digest":
                msg_digest_attr = attr["values"][0].native
                break
        if msg_digest_attr is None:
            raise EDSVerifyError("В подписанных атрибутах нет messageDigest")
        if msg_digest_attr != content_digest:
            return VerifyResult(
                algorithm="RSA", signature_valid=False, chain_valid=False,
                crypto_verified=True,
                warnings=["messageDigest в подписи не совпадает с переданными данными протокола"],
            )
        signed_bytes = signed_attrs.dump(force=True)
        # CMS requires the signature cover an explicit SET OF tag (0x31),
        # not the implicit [0] tag used for storage in the CMS structure.
        signed_bytes = b"\x31" + signed_bytes[1:]
    else:
        signed_bytes = payload

    sig_ok = _verify_rsa_signature(leaf_pub, signed_bytes, signature, digest_name, is_pss)
    chain_ok = _verify_chain_rsa(leaf)

    if not chain_ok:
        warnings.append("Сертификат не удалось привязать к корневому УЦ НУЦ РК (RSA)")
    if not sig_ok:
        warnings.append("Криптографическая подпись недействительна")

    return VerifyResult(
        algorithm="RSA", signature_valid=sig_ok, chain_valid=chain_ok,
        crypto_verified=True, warnings=warnings,
    )
