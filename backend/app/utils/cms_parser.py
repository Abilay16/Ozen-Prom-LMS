"""
Parse NCALayer CMS (PKCS#7 SignedData) and extract signer certificate info.

Usage:
    from app.utils.cms_parser import parse_cms

    info = parse_cms(cms_base64_string)
    # info.serial, info.owner, info.valid_from, info.valid_to
"""
import base64
from dataclasses import dataclass
from datetime import datetime, timezone

from asn1crypto import cms as asn1_cms, pem as asn1_pem, core as asn1_core


class CMSParseError(ValueError):
    """Raised when the CMS cannot be parsed or has no signer certificate."""


@dataclass
class CertInfo:
    serial: str          # hex serial number, upper-case
    owner: str           # CN from subject (or full subject string)
    valid_from: datetime
    valid_to: datetime


def parse_cms(cms_b64: str) -> CertInfo:
    """
    Parse a Base64-encoded CMS SignedData blob and return the first signer's
    certificate information.

    Accepts both raw DER (base64) and PEM formats.
    Raises CMSParseError on any parse failure.
    """
    try:
        raw = base64.b64decode(cms_b64)
    except Exception as exc:
        raise CMSParseError(f"Invalid Base64: {exc}") from exc

    try:
        # Unwrap PEM if wrapped
        if asn1_pem.detect(raw):
            _, _, raw = asn1_pem.unarmor(raw)

        content_info = asn1_cms.ContentInfo.load(raw)
        # ContentInfo["content"] is already the parsed SignedData in asn1crypto
        payload = content_info["content"]

        # Prefer certificates embedded in the SignedData (NCALayer always includes them)
        certs = payload["certificates"]
        if not certs or len(certs) == 0:
            raise CMSParseError("No certificates found in CMS")

        # Take the first certificate (the signer's cert)
        cert = certs[0].chosen

        serial_int = cert["tbs_certificate"]["serial_number"].native
        serial_hex = format(serial_int, "X")

        subject = cert["tbs_certificate"]["subject"].human_friendly
        # Try to extract just the CN
        cn = None
        for rdn in cert["tbs_certificate"]["subject"].chosen:
            for attr in rdn:
                if attr["type"].dotted == "2.5.4.3":  # commonName OID
                    cn = attr["value"].native
                    break
            if cn:
                break
        owner = cn or subject

        validity = cert["tbs_certificate"]["validity"]
        valid_from = validity["not_before"].native.astimezone(timezone.utc)
        valid_to   = validity["not_after"].native.astimezone(timezone.utc)

    except CMSParseError:
        raise
    except Exception as exc:
        raise CMSParseError(f"CMS parse error: {exc}") from exc

    return CertInfo(
        serial=serial_hex,
        owner=owner,
        valid_from=valid_from,
        valid_to=valid_to,
    )
