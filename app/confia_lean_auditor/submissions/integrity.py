"""Canonical hashes of persisted contracts, not signatures or filesystem security."""
import hashlib
import json


def canonical_sha256(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def model_sha256(model):
    return canonical_sha256(model.model_dump(mode="json"))
