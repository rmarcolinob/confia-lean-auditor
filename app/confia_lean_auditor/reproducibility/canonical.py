"""GOV-01 canonical UTF-8 JSON, independent of presentation whitespace."""
import hashlib
import json
from datetime import datetime, timezone

from pydantic import BaseModel


def _json_value(value):
    if isinstance(value, BaseModel):
        return value.model_dump(mode="python")
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("canonical timestamps require a timezone")
        return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    raise TypeError("unsupported canonical value")


def canonical_bytes(value):
    return json.dumps(value, default=_json_value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()
