"""
Creates a Zenoh-compatible payload and attachment from a Python object.
"""
from typing import Any, Dict, List
import json

from datatypes import datatypes, serializer


class ZenohCodec:
    """Encodes and decodes Python objects for Zenoh transport."""

    def __init__(self):
        self._registry: List[Dict[str, Any]] = [
            {
                "pred": lambda d: (
                    isinstance(d, dict) and bool(d)
                    and all(isinstance(k, str) for k in d)
                    and all(isinstance(v, datatypes.BaseDataType) for v in d.values())
                ),
                "tag": b"DTD", # Datatype Dict
                "ser": lambda d: serializer.serialize(*d.values(), names=list(d.keys())),
                "des": lambda p, _: serializer.deserialize(p),
            },
            {
                "pred": lambda d: isinstance(d, datatypes.BaseDataType),
                "tag": b"DTO", # Datatype Object
                "ser": serializer.serialize,
                "des": lambda p, _: next(iter(serializer.deserialize(p).values())),
            },
            {
                "pred": lambda d: (
                    isinstance(d, (list, tuple)) and bool(d)
                    and all(isinstance(x, datatypes.BaseDataType) for x in d)
                ),
                "tag": b"DTS", # Datatype Sequence
                "ser": lambda d: serializer.serialize(*d),
                "des": lambda p, _: list(serializer.deserialize(p).values()),
            },
            {
                "pred": lambda d: isinstance(d, dict),
                "tag": b"JSO",
                "ser": lambda d: json.dumps(d).encode("utf-8"),
                "des": lambda p, _: json.loads(p.decode("utf-8")),
            },
        ]
        self._tag_map = {e["tag"]: e for e in self._registry}

    def encode(self, data: Any) -> tuple[bytes, bytes]:
        """Returns (payload, attachment)."""
        for entry in self._registry:
            if entry["pred"](data):
                attachment = entry["tag"]
                if "att_extra" in entry:
                    attachment += entry["att_extra"](data)
                return entry["ser"](data), attachment
        raise TypeError(f"No serializer for {type(data)}")

    def decode(self, payload: bytes, attachment: bytes) -> Any:
        """Decode a Zenoh payload and attachment into a Python object."""
        tag = attachment[:3]
        entry = self._tag_map.get(tag)
        if entry is None:
            raise ValueError(f"Unknown attachment tag: {tag}")
        return entry["des"](payload, attachment)
