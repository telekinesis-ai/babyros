"""
Creates a Zenoh-compatible payload and attachment from a Python object.
"""
import json
import struct
import numpy as np
from typing import Any, Dict, Callable


class ZenohCodec:
    def __init__(self):
        # Maps Python types to (Tag, Serializer, Deserializer)
        self._registry: Dict[Any, Dict[str, Callable]] = {
            dict: {
                "tag": b"JSON",
                "ser": lambda d: json.dumps(d).encode("utf-8"),
                "des": lambda p, a: json.loads(p.decode("utf-8"))
            },
            np.ndarray: {
                "tag": b"IMG",
                "ser": self._serialize_np,
                "des": self._deserialize_np
            }
        }

    def _serialize_np(self, arr: np.ndarray) -> bytes:
        # We pack the metadata into the attachment later, 
        # so this just returns the raw buffer
        return arr.tobytes()

    def _deserialize_np(self, payload: bytes, attachment: bytes) -> np.ndarray:
        # Start after the 3-byte "IMG" tag
        h, w, c = struct.unpack("iii", attachment[3:15])
        dtype = attachment[15:25].rstrip(b"\0").decode("utf-8")
        return np.frombuffer(payload, dtype=dtype).reshape((h, w, c))

    def encode(self, data: Any) -> tuple[bytes, bytes]:
        """
        Returns (payload, attachment)"""
        t = type(data)
        if t not in self._registry:
            raise TypeError(f"No serializer for {t}")
        
        entry = self._registry[t]
        payload = entry["ser"](data)
        
        # Build attachment: Tag + Optional Metadata
        attachment = entry["tag"]
        if t == np.ndarray:
            h, w, c = data.shape
            dtype_bytes = str(data.dtype).encode("utf-8").ljust(10, b"\0")
            attachment += struct.pack("iii", h, w, c) + dtype_bytes
            
        return payload, attachment

    def decode(self, payload: bytes, attachment: bytes) -> Any:
        """
        Decode a Zenoh payload and attachment into a Python object.
        """
        tag = attachment[:3] # Assuming 3-char tags for simplicity
        if tag == b"JSO": # Handle JSON (tag was b"JSON", first 3 are JSO)
             return self._registry[dict]["des"](payload, attachment)
        if tag == b"IMG":
             return self._registry[np.ndarray]["des"](payload, attachment)
        
        raise ValueError(f"Unknown attachment tag: {tag}")