"""
Creates a Zenoh-compatible payload and attachment from a Python object.
"""
from typing import Any, Dict, List
import json

from telekinesis import datatypes
from telekinesis.datatypes import serializer


class ZenohCodec:
    """Encodes and decodes Python objects for Zenoh transport."""

    def __init__(self, compression: str | None = "lz4"):
        """Create a codec.

        Args:
            compression: Arrow IPC-level codec passed to
                `telekinesis.datatypes.serializer.serialize` for every
                datatype payload. ``"lz4"`` (default) or ``"zstd"`` shrink
                the payload at CPU cost — pick these for bandwidth-limited
                links. ``None`` disables IPC compression, which is faster
                end-to-end on localhost / fast LANs. Decoding needs no
                matching setting; the reader detects the codec from the
                stream.
        """
        self._compression = compression
        self._registry: List[Dict[str, Any]] = [
            {
                "pred": lambda d: (
                    isinstance(d, dict) and bool(d)
                    and all(isinstance(k, str) for k in d)
                    and all(isinstance(v, datatypes.BaseDataType) for v in d.values())
                ),
                "tag": b"DTD", # Datatype Dict
                "ser": lambda d: serializer.serialize(
                    *d.values(), names=list(d.keys()), compression=self._compression
                ),
                "des": lambda p, _: serializer.deserialize(p),
            },
            {
                "pred": lambda d: isinstance(d, datatypes.BaseDataType),
                "tag": b"DTO", # Datatype Object
                "ser": lambda d: serializer.serialize(d, compression=self._compression),
                "des": lambda p, _: next(iter(serializer.deserialize(p).values())),
            },
            {
                "pred": lambda d: (
                    isinstance(d, (list, tuple)) and bool(d)
                    and all(isinstance(x, datatypes.BaseDataType) for x in d)
                ),
                "tag": b"DTS", # Datatype Sequence
                "ser": lambda d: serializer.serialize(*d, compression=self._compression),
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
