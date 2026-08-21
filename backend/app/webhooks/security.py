import hmac
import hashlib


def verify_github_signature(payload_bytes: bytes, signature_header: str | None, secret: str) -> bool:
    if not signature_header or not secret:
        return False

    prefix = "sha256="
    if not signature_header.startswith(prefix):
        return False

    received_sig = signature_header[len(prefix):]
    mac = hmac.new(secret.encode("utf-8"), msg=payload_bytes, digestmod=hashlib.sha256)
    expected_sig = mac.hexdigest()

    return hmac.compare_digest(received_sig, expected_sig)


def verify_gitlab_token(token_header: str | None, secret: str) -> bool:
    if not token_header or not secret:
        return False
    return hmac.compare_digest(token_header, secret)
