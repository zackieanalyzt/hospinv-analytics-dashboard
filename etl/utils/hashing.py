import hashlib

def sha256_hash(*parts):
    raw = "||".join("" if p is None else str(p).strip() for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
